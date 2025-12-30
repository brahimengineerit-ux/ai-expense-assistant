"""
Receipt/Invoice Parser Service
==============================
Full receipt parsing with:
- Line items extraction
- Vendor details
- Tax breakdown
- Invoice number
- Payment status
"""

import json
import base64
from datetime import date
from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


RECEIPT_PARSE_PROMPT = """You are an expert receipt/invoice parser. Extract ALL information from this receipt.

EXTRACT THE FOLLOWING:

1. **VENDOR INFO**:
   - name: Store/company name
   - address: Full address if visible
   - phone: Phone number
   - tax_id: Tax ID/VAT number if visible

2. **INVOICE INFO**:
   - number: Invoice/receipt number
   - date: Date (YYYY-MM-DD format)
   - due_date: Due date if invoice
   - type: "receipt", "invoice", or "bill"

3. **LINE ITEMS** (each product/service):
   - description: Item name
   - quantity: Number of items (default 1)
   - unit_price: Price per unit
   - total: Line total
   - category: transport/food/utilities/shopping/health/entertainment/education/travel/other

4. **TOTALS**:
   - subtotal: Before tax
   - tax_rate: Tax percentage (e.g., 20 for 20%)
   - tax_amount: Tax amount
   - discount: Discount amount (0 if none)
   - total: Final total
   - currency: MAD, EUR, USD, etc.

5. **PAYMENT**:
   - method: cash, card, transfer, mobile, other
   - status: paid, unpaid, partial

CURRENCY DETECTION:
- dh, درهم, DH, MAD → "MAD"
- €, euro, EUR → "EUR"
- $, dollar, USD → "USD"

LANGUAGE SUPPORT:
- English, French, German, Arabic, Moroccan Darija

Return ONLY valid JSON, no explanation."""


def parse_receipt_full(
    text: str,
    extract_line_items: bool = True,
    extract_vendor: bool = True,
    extract_tax: bool = True,
    language: str = None
) -> dict:
    """
    Parse receipt/invoice text and extract all structured data.
    """
    
    json_structure = {
        "vendor": {
            "name": "<string or null>",
            "address": "<string or null>",
            "phone": "<string or null>",
            "tax_id": "<string or null>"
        } if extract_vendor else None,
        "invoice": {
            "number": "<string or null>",
            "date": "<YYYY-MM-DD or null>",
            "due_date": "<YYYY-MM-DD or null>",
            "type": "<receipt/invoice/bill>"
        },
        "line_items": [
            {
                "description": "<item name>",
                "quantity": "<number>",
                "unit_price": "<number or null>",
                "total": "<number>",
                "category": "<category>"
            }
        ] if extract_line_items else [],
        "totals": {
            "subtotal": "<number or null>",
            "tax_rate": "<number or null>",
            "tax_amount": "<number or null>",
            "discount": "<number or 0>",
            "total": "<number>",
            "currency": "<MAD/EUR/USD>"
        } if extract_tax else {"total": "<number>", "currency": "<code>"},
        "payment": {
            "method": "<cash/card/transfer/mobile/other or null>",
            "status": "<paid/unpaid/partial>"
        },
        "language_detected": "<detected language>"
    }
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""{RECEIPT_PARSE_PROMPT}

Return this exact JSON structure:
{json.dumps(json_structure, indent=2)}

TODAY'S DATE: {date.today().isoformat()}"""
            },
            {
                "role": "user",
                "content": f"Parse this receipt/invoice:\n\n{text}"
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Ensure line_items is a list
    if "line_items" not in result or result["line_items"] is None:
        result["line_items"] = []
    
    return result


def parse_receipt_from_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    extract_line_items: bool = True,
    extract_vendor: bool = True,
    extract_tax: bool = True
) -> dict:
    """
    Parse receipt from image using GPT-4o Vision.
    """
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    json_structure = {
        "vendor": {
            "name": "<string or null>",
            "address": "<string or null>",
            "phone": "<string or null>",
            "tax_id": "<string or null>"
        },
        "invoice": {
            "number": "<string or null>",
            "date": "<YYYY-MM-DD or null>",
            "due_date": "<YYYY-MM-DD or null>",
            "type": "<receipt/invoice/bill>"
        },
        "line_items": [
            {
                "description": "<item name>",
                "quantity": "<number>",
                "unit_price": "<number or null>",
                "total": "<number>",
                "category": "<category>"
            }
        ],
        "totals": {
            "subtotal": "<number or null>",
            "tax_rate": "<number or null>",
            "tax_amount": "<number or null>",
            "discount": "<number or 0>",
            "total": "<number>",
            "currency": "<MAD/EUR/USD>"
        },
        "payment": {
            "method": "<cash/card/transfer/mobile/other or null>",
            "status": "<paid/unpaid/partial>"
        },
        "extracted_text": "<all visible text from receipt>",
        "language_detected": "<detected language>",
        "confidence": "<0.0-1.0>"
    }
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""{RECEIPT_PARSE_PROMPT}

Return this exact JSON structure:
{json.dumps(json_structure, indent=2)}

TODAY'S DATE: {date.today().isoformat()}"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Parse this receipt/invoice image. Extract ALL visible information."
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
        temperature=0,
        max_tokens=2000
    )
    
    result = json.loads(response.choices[0].message.content)
    
    if "line_items" not in result or result["line_items"] is None:
        result["line_items"] = []
    
    return result


def parse_receipt_from_url(
    image_url: str,
    extract_line_items: bool = True,
    extract_vendor: bool = True,
    extract_tax: bool = True
) -> dict:
    """
    Parse receipt from image URL using GPT-4o Vision.
    """
    json_structure = {
        "vendor": {
            "name": "<string or null>",
            "address": "<string or null>",
            "phone": "<string or null>",
            "tax_id": "<string or null>"
        },
        "invoice": {
            "number": "<string or null>",
            "date": "<YYYY-MM-DD or null>",
            "due_date": "<YYYY-MM-DD or null>",
            "type": "<receipt/invoice/bill>"
        },
        "line_items": [
            {
                "description": "<item name>",
                "quantity": "<number>",
                "unit_price": "<number or null>",
                "total": "<number>",
                "category": "<category>"
            }
        ],
        "totals": {
            "subtotal": "<number or null>",
            "tax_rate": "<number or null>",
            "tax_amount": "<number or null>",
            "discount": "<number or 0>",
            "total": "<number>",
            "currency": "<MAD/EUR/USD>"
        },
        "payment": {
            "method": "<cash/card/transfer/mobile/other or null>",
            "status": "<paid/unpaid/partial>"
        },
        "extracted_text": "<all visible text>",
        "language_detected": "<detected language>",
        "confidence": "<0.0-1.0>"
    }
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""{RECEIPT_PARSE_PROMPT}

Return this exact JSON structure:
{json.dumps(json_structure, indent=2)}

TODAY'S DATE: {date.today().isoformat()}"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Parse this receipt/invoice image. Extract ALL visible information."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }
        ],
        temperature=0,
        max_tokens=2000
    )
    
    result = json.loads(response.choices[0].message.content)
    
    if "line_items" not in result or result["line_items"] is None:
        result["line_items"] = []
    
    return result
