# AI Expense & Receipt Parser

AI-powered expense extraction and receipt parsing with multi-language support.

## Features

- ✅ **Text Extraction** - Natural language expense parsing
- ✅ **Multi-Language** - EN, FR, DE, AR, Darija
- ✅ **Image OCR** - Receipt/invoice image processing (GPT-4o Vision)
- ✅ **PDF Support** - Parse PDF invoices and receipts
- ✅ **Line Items** - Extract individual products from receipts
- ✅ **Tax Breakdown** - Subtotal, tax rate, tax amount, total
- ✅ **Vendor Info** - Name, address, phone, tax ID
- ✅ **Invoice Number** - Extract receipt/invoice numbers
- ✅ **Payment Status** - Paid/unpaid, payment method
- ✅ **Analytics** - Spending insights and breakdown
- ✅ **Export** - Excel and CSV export

## Installation

```bash
# Clone
git clone https://github.com/brahimengineerit-ux/ai-expense-assistant.git
cd ai-expense-assistant

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your OpenAI API key to .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000

## API Endpoints

### Expense Extraction
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/expenses/extract` | Single expense from text |
| POST | `/expenses/extract/multi` | Multiple expenses from text |
| POST | `/expenses/extract/batch` | Batch processing |

### OCR
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/expenses/ocr/upload` | OCR from uploaded image |
| POST | `/expenses/ocr/url` | OCR from image URL |

### Receipt Parser (NEW)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/expenses/receipt/parse/text` | Parse receipt from text |
| POST | `/expenses/receipt/parse/upload` | Parse receipt from image/PDF |
| POST | `/expenses/receipt/parse/url` | Parse receipt from URL |

### PDF Processing (NEW)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/expenses/pdf/info` | Get PDF info |
| POST | `/expenses/pdf/extract-text` | Extract text from PDF |

### Analytics & Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/expenses/analytics` | Get insights |
| POST | `/expenses/export/csv` | Export to CSV |
| POST | `/expenses/export/excel` | Export to Excel |

## Receipt Parser Response

```json
{
  "success": true,
  "source": "pdf_text",
  "vendor": {
    "name": "Marjane",
    "address": "Rabat, Morocco",
    "phone": "+212 5XX-XXXXXX",
    "tax_id": "XXXXXXXX"
  },
  "invoice": {
    "number": "INV-2025-001234",
    "date": "2025-01-15",
    "type": "receipt"
  },
  "line_items": [
    {"description": "Milk 1L", "quantity": 2, "unit_price": 8.50, "total": 17.00, "category": "food"},
    {"description": "Bread", "quantity": 1, "unit_price": 5.00, "total": 5.00, "category": "food"}
  ],
  "totals": {
    "subtotal": 22.00,
    "tax_rate": 20,
    "tax_amount": 4.40,
    "total": 26.40,
    "currency": "MAD"
  },
  "payment_method": "card",
  "payment_status": "paid",
  "language_detected": "French"
}
```

## Supported Languages

- 🇺🇸 English
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇸🇦 العربية
- 🇲🇦 الدارجة (Darija)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `DEFAULT_MODEL` | ❌ | Default: `gpt-4o-mini` |

## Author

**Baha Mlouk** - AI Engineer
