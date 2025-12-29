"""
Core AI Expense Extraction Engine
=================================
Advanced extraction with:
- Structured JSON output (guaranteed valid JSON)
- Multi-expense detection
- Multi-language support (EN, FR, AR, Darija)
- Smart categorization
- Force category when user specifies
"""

import json
import re
from openai import OpenAI
from app.core.config import OPENAI_API_KEY, DEFAULT_MODEL, EXPENSE_CATEGORIES

client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def has_multiple_expenses(text: str) -> bool:
    """
    Detect if text likely contains multiple expenses.
    """
    price_pattern = r'\d+\s*(dh|درهم|mad|€|euro|euros|\$|dollar|dollars)'
    prices = re.findall(price_pattern, text.lower())
    if len(prices) > 1:
        return True
    if re.search(r'\d+\s*(dh|درهم|mad).*?(w|و|and|et|,).*?\d+\s*(dh|درهم|mad)', text.lower()):
        return True
    return False


# ============================================================
# EXTRACTION FUNCTIONS
# ============================================================

def extract_single_expense(
    text: str,
    expense_type: str | None = None,
    fields: list[str] | None = None,
    language: str | None = None
) -> dict:
    """
    Extract a single expense from text.
    If expense_type is provided, it will be used as the category.
    """
    from datetime import date
    
    if fields is None:
        fields = ["amount", "currency", "category", "description", "date", "payment_method"]
    
    # Build category instruction
    if expense_type and expense_type in EXPENSE_CATEGORIES:
        category_instruction = f'IMPORTANT: The user has specified the category as "{expense_type}". You MUST use "{expense_type}" as the category.'
    else:
        category_instruction = f"Determine the best category from: {', '.join(EXPENSE_CATEGORIES)}"
    
    prompt = f"""Extract expense information from this text:

TEXT: {text}

TODAY'S DATE: {date.today().isoformat()}

{category_instruction}

VOCABULARY:

DAIRJA (Moroccan):
- khlsst/خلصت = paid
- chrit/شريت = bought
- dh/درهم = MAD (Moroccan Dirham)
- f/في = for
- lyouma = today
- ghda = lunch
- ftour = breakfast

DEUTSCH (German):
- bezahlt/gezahlt = paid
- gekauft = bought
- €/Euro = EUR
- für = for
- heute = today
- Mittagessen = lunch
- Frühstück = breakfast
- Taxi/Fahrt = transport
- Essen = food
- Miete = rent
- Einkaufen = shopping

Return the extracted expense data."""

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""You are an expense extraction engine. Extract expense data and return ONLY valid JSON.

{f'CRITICAL: The category MUST be "{expense_type}". Do not change it.' if expense_type else ''}

Return this exact structure:
{{
  "expense": {{
    "amount": <number or null>,
    "currency": "<MAD/EUR/USD - detect from text>",
    "category": "{expense_type if expense_type else '<detect from text>'}",
    "description": "<short description>",
    "date": "{date.today().isoformat()}",
    "payment_method": "cash"
  }},
  "language_detected": "<English/French/German/Arabic/Moroccan Darija>"
}}"""
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Get expense data
    expense_data = result.get("expense", result)
    if "expenses" in result and len(result["expenses"]) > 0:
        expense_data = result["expenses"][0]
    
    # FORCE the category if user specified it
    if expense_type and expense_type in EXPENSE_CATEGORIES:
        expense_data["category"] = expense_type
    
    return {
        "success": True,
        "journal": "expenses",
        "expense_type": expense_data.get("category"),
        "data": expense_data,
        "language_detected": result.get("language_detected")
    }


def extract_multiple_expenses(
    text: str,
    fields: list[str] | None = None,
    language: str | None = None
) -> dict:
    """
    Extract multiple expenses from a single text.
    """
    from datetime import date
    
    if fields is None:
        fields = ["amount", "currency", "category", "description", "date", "payment_method"]
    
    prompt = f"""Extract ALL expenses from this text. Each item separated by "w", "و", "and", "et", or "," is a SEPARATE expense.

TEXT: {text}

TODAY'S DATE: {date.today().isoformat()}

VOCABULARY:

DAIRJA/ARABIC:
- khlsst/خلصت = paid
- chrit/شريت = bought
- dh/درهم = MAD (Moroccan Dirham)
- f/في = for/in
- w/و = and (separates expenses)
- lyouma/ليوما = today
- ghda/غدا = lunch → category: food
- ftour/فطور = breakfast → category: food
- taxi/طاكسي = taxi → category: transport
- tramway/tram = tram → category: transport
- facture/فاتورة = bill → category: utilities
- telefon/تيليفون = phone → category: utilities
- carburant/essence = fuel → category: transport

DEUTSCH (German):
- bezahlt/gezahlt = paid
- gekauft = bought
- €/Euro = EUR
- für = for
- und = and (separates expenses)
- heute = today
- Mittagessen = lunch → food
- Frühstück = breakfast → food
- Taxi/Fahrt/U-Bahn = transport
- Miete = rent
- Rechnung = bill → utilities
- Einkaufen = shopping

CATEGORY RULES:
- taxi, tramway, bus, carburant, essence, parking → "transport"
- ghda, ftour, sandwich, pizza, café, atay, restaurant → "food"
- facture, telephone, telefon, internet, eau, electricité → "utilities"
- loyer → "rent"
- cinema, film, match → "entertainment"
- habits, vetements → "shopping"
- pharmacie, medicament → "health"
- école, formation → "education"
- voyage, hotel → "travel"
- anything else → "other"
"""

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are an expense extraction engine. Extract ALL expenses and return ONLY valid JSON.

CRITICAL: Each expense must have its OWN correct category based on what it is.

Return this exact structure:
{
  "expenses": [
    {
      "amount": <number>,
      "currency": "MAD",
      "category": "<correct category for THIS item>",
      "description": "<what was bought>",
      "date": "<YYYY-MM-DD>",
      "payment_method": "cash"
    }
  ],
  "language_detected": "<detected language>"
}

Example: "30dh f taxi w 45dh f ghda w 150dh f facture telefon" becomes:
- taxi → transport
- ghda → food  
- facture telefon → utilities"""
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    expenses = result.get("expenses", [])
    
    return {
        "success": True,
        "count": len(expenses),
        "expenses": expenses,
        "language_detected": result.get("language_detected")
    }


def smart_extract(
    text: str,
    expense_type: str | None = None,
    fields: list[str] | None = None,
    language: str | None = None
) -> dict:
    """
    Smart extraction - automatically detects if single or multiple expenses.
    """
    if has_multiple_expenses(text):
        return extract_multiple_expenses(text, fields, language)
    else:
        result = extract_single_expense(text, expense_type, fields, language)
        return {
            "success": True,
            "count": 1,
            "expenses": [result["data"]],
            "language_detected": result.get("language_detected")
        }


def extract_batch(
    texts: list[str],
    fields: list[str] | None = None
) -> dict:
    """
    Process multiple texts in batch.
    """
    results = []
    failed = 0
    
    for text in texts:
        try:
            result = extract_single_expense(text=text, fields=fields)
            results.append({
                "input": text,
                "success": True,
                "data": result["data"]
            })
        except Exception as e:
            failed += 1
            results.append({
                "input": text,
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": True,
        "total": len(texts),
        "processed": len(texts) - failed,
        "failed": failed,
        "results": results
    }
