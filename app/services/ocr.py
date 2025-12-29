"""
OCR Service for Receipt/Invoice Processing
==========================================
Uses GPT-4o Vision to extract text from images,
and can also scrape webpages for expense information.
"""

import base64
import re
import ssl
from urllib.parse import urlparse
from openai import OpenAI
from app.core.config import OPENAI_API_KEY
from app.services.extractor import extract_multiple_expenses

client = OpenAI(api_key=OPENAI_API_KEY)


def encode_image(image_bytes: bytes) -> str:
    """Encode image bytes to base64"""
    return base64.b64encode(image_bytes).decode("utf-8")


def is_image_url(url: str) -> bool:
    """Check if URL looks like a direct image link"""
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')
    url_lower = url.lower().split('?')[0]
    return url_lower.endswith(image_extensions)


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False


def fetch_webpage_text(url: str) -> str:
    """
    Fetch and extract text content from a webpage using requests + BeautifulSoup.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        # Fallback to urllib if requests not installed
        return fetch_webpage_text_urllib(url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5,fr;q=0.3,ar;q=0.2',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=True)
        response.raise_for_status()
        html = response.text
    except requests.exceptions.SSLError:
        # Try without SSL verification as fallback
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            raise ValueError(f"Failed to fetch webpage (SSL error): {str(e)}")
    except requests.exceptions.Timeout:
        raise ValueError("Webpage took too long to respond (timeout)")
    except requests.exceptions.ConnectionError:
        raise ValueError("Could not connect to the webpage")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"Webpage returned error: {e.response.status_code}")
    except Exception as e:
        raise ValueError(f"Failed to fetch webpage: {str(e)}")
    
    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for element in soup(['script', 'style', 'head', 'meta', 'link', 'noscript', 'header', 'footer', 'nav']):
        element.decompose()
    
    # Get text
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text[:8000]  # Limit length


def fetch_webpage_text_urllib(url: str) -> str:
    """Fallback using urllib"""
    import urllib.request
    from html.parser import HTMLParser
    
    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts = []
            self.skip_tags = {'script', 'style', 'head', 'meta', 'link', 'noscript'}
            self.current_tag = None
            
        def handle_starttag(self, tag, attrs):
            self.current_tag = tag.lower()
            
        def handle_endtag(self, tag):
            self.current_tag = None
            
        def handle_data(self, data):
            if self.current_tag not in self.skip_tags:
                text = data.strip()
                if text:
                    self.text_parts.append(text)
                    
        def get_text(self):
            return '\n'.join(self.text_parts)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    
    # Create SSL context that doesn't verify
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        raise ValueError(f"Failed to fetch webpage: {str(e)}")
    
    parser = TextExtractor()
    parser.feed(html)
    text = parser.get_text()
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text[:8000]


def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Extract text from an image using GPT-4o Vision."""
    base64_image = encode_image(image_bytes)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract ALL text from this receipt/invoice image.
                        
Include:
- Vendor/store name
- Date
- All items with prices
- Subtotal, tax, total
- Payment method if visible

Return the text exactly as it appears, preserving structure."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    
    return response.choices[0].message.content


def process_receipt(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    fields: list[str] | None = None
) -> dict:
    """Full pipeline: Image → Text → Structured Expenses"""
    extracted_text = extract_text_from_image(image_bytes, mime_type)
    
    expenses = extract_multiple_expenses(
        text=extracted_text,
        fields=fields
    )
    
    return {
        "success": True,
        "source": "image_upload",
        "extracted_text": extracted_text,
        "expenses": expenses["expenses"],
        "count": expenses["count"]
    }


def process_receipt_from_url(
    image_url: str,
    fields: list[str] | None = None
) -> dict:
    """
    Process receipt from URL - handles both images and webpages.
    """
    if not is_valid_url(image_url):
        raise ValueError("Invalid URL format. Please provide a valid URL starting with http:// or https://")
    
    # Determine if it's an image or webpage
    if is_image_url(image_url):
        # Process as image using GPT-4o Vision
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Extract ALL text from this receipt/invoice image.
Include vendor name, date, items, prices, total, and payment method."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            extracted_text = response.choices[0].message.content
            source = "image_url"
        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}")
        
    else:
        # Process as webpage
        extracted_text = fetch_webpage_text(image_url)
        source = "webpage"
    
    # Process through expense extractor
    if source == "webpage":
        # Use AI to extract relevant pricing info from webpage text
        import json
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expense extraction engine. 
Extract ALL prices, fees, tickets, subscriptions, fares, or any monetary amounts from the text.
Look for prices in various formats: 10dh, 10 MAD, 10€, $10, 10 dirhams, etc.

Return ONLY valid JSON with this structure:
{
  "expenses": [
    {"amount": <number>, "currency": "<code like MAD, EUR, USD>", "category": "<category>", "description": "<what it is>"}
  ],
  "language_detected": "<language>"
}

Categories: transport, food, utilities, rent, entertainment, shopping, health, education, travel, other
If no prices found, return {"expenses": [], "language_detected": "<language>"}"""
                },
                {
                    "role": "user",
                    "content": f"Extract all prices and expenses from this webpage content:\n\n{extracted_text}"
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "success": True,
            "source": source,
            "url": image_url,
            "extracted_text": extracted_text[:1500] + "..." if len(extracted_text) > 1500 else extracted_text,
            "expenses": result.get("expenses", []),
            "count": len(result.get("expenses", [])),
            "language_detected": result.get("language_detected")
        }
    
    # For images, use the standard extractor
    expenses = extract_multiple_expenses(
        text=extracted_text,
        fields=fields
    )
    
    return {
        "success": True,
        "source": source,
        "extracted_text": extracted_text,
        "expenses": expenses["expenses"],
        "count": expenses["count"]
    }
