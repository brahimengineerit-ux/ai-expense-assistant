import json
from datetime import date
from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are an expense extraction assistant.
Extract structured JSON from the user text.
Return ONLY valid JSON.
Schema:
{
  "amount": number,
  "currency": string,
  "category": string,
  "merchant": string | null,
  "payment_method": string,
  "date": "YYYY-MM-DD"
}
If date is relative (today, yesterday), resolve it.
"""

def parse_expense(text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("LLM returned invalid JSON")
