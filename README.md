# AI Expense Analysis Assistant

Advanced AI-powered backend that extracts structured expense data from free-text descriptions, receipts, and invoices.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple)

## Features

### 🎯 Core Extraction
- **Single expense** extraction from natural language
- **Multi-expense** detection from one text
- **Batch processing** for multiple texts
- **Dynamic schema** - specify exactly what fields you need

### 🌍 Multi-Language Support
- English
- French
- Arabic (العربية)
- Moroccan Darija (الدارجة المغربية)
- Auto-detection of input language

### 📷 Receipt/Invoice OCR
- Upload receipt images
- Process from URL
- GPT-4o Vision powered
- Supports JPEG, PNG, WebP, GIF

### 📊 Analytics & Insights
- Category breakdown
- Payment method analysis
- Spending trends
- Anomaly detection
- Human-readable summaries

### 📁 Export
- CSV export
- Formatted Excel reports with summary sheet

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run the server
```bash
uvicorn app.main:app --reload
```

### 4. Open docs
```
http://127.0.0.1:8000/docs
```

---

## API Examples

### Single Expense Extraction
```bash
curl -X POST http://localhost:8000/expenses/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I paid 15 dh for a taxi this morning",
    "expense_type": "transport",
    "fields": ["amount", "currency", "payment_method", "date"]
  }'
```

**Response:**
```json
{
  "success": true,
  "journal": "expenses",
  "expense_type": "transport",
  "data": {
    "amount": 15,
    "currency": "MAD",
    "payment_method": "cash",
    "date": "2025-12-29"
  },
  "language_detected": "English"
}
```

### Multi-Expense Extraction
```bash
curl -X POST http://localhost:8000/expenses/extract/multi \
  -H "Content-Type: application/json" \
  -d '{
    "text": "khlsst 50dh f taxi w 30dh f sandwich w 100dh f telephone",
    "fields": ["amount", "currency", "category", "description"]
  }'
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "expenses": [
    {"amount": 50, "currency": "MAD", "category": "transport", "description": "Taxi"},
    {"amount": 30, "currency": "MAD", "category": "food", "description": "Sandwich"},
    {"amount": 100, "currency": "MAD", "category": "utilities", "description": "Phone bill"}
  ],
  "language_detected": "Moroccan Darija"
}
```

### Receipt OCR
```bash
curl -X POST http://localhost:8000/expenses/ocr/upload \
  -F "file=@receipt.jpg"
```

### Analytics
```bash
curl -X POST http://localhost:8000/expenses/analytics \
  -H "Content-Type: application/json" \
  -d '{
    "expenses": [
      {"amount": 50, "currency": "MAD", "category": "transport"},
      {"amount": 30, "currency": "MAD", "category": "food"},
      {"amount": 100, "currency": "MAD", "category": "utilities"}
    ],
    "group_by": "category"
  }'
```

### Export to Excel
```bash
curl -X POST http://localhost:8000/expenses/export/excel \
  -H "Content-Type: application/json" \
  -d '[
    {"amount": 50, "currency": "MAD", "category": "transport"},
    {"amount": 30, "currency": "MAD", "category": "food"}
  ]' \
  --output expenses.xlsx
```

---

## Project Structure

```
ai-expense-assistant/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   └── expenses.py      # All API endpoints
│   ├── services/
│   │   ├── extractor.py     # Core AI extraction engine
│   │   ├── ocr.py           # Receipt/invoice OCR
│   │   ├── analytics.py     # Analytics & insights
│   │   └── export.py        # CSV/Excel export
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── core/
│       └── config.py        # Configuration
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Technical Highlights

### Structured Outputs
Uses OpenAI's JSON Schema mode for **guaranteed valid JSON** responses - no more parsing errors.

### Dynamic Field Selection
Request exactly the fields you need - the schema is built dynamically per request.

### Language Detection
Automatically detects input language and handles mixed-language inputs (e.g., "khlsst 50dh f taxi").

### Smart Currency Detection
- `dh`, `درهم` → MAD
- `$` → USD  
- `€` → EUR

### Date Parsing
Handles relative dates: "this morning", "yesterday", "lyouma" (today in Darija)

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `DEFAULT_MODEL` | No | `gpt-4o-mini` | Model for text extraction |

---

## Tech Stack

- **FastAPI** - Modern Python web framework
- **OpenAI GPT-4o** - AI extraction & OCR
- **Pydantic** - Data validation
- **openpyxl** - Excel generation

---

## Author

**Baha Mlouk**  
AI Engineer | Python Developer

---

## License

MIT
