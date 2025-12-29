# AI Expense Assistant

AI-powered expense extraction from natural language with multi-language support.

## Installation

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/ai-expense-assistant.git
cd ai-expense-assistant

# Create virtual environment
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

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `DEFAULT_MODEL` | ❌ | Default: `gpt-4o-mini` |

## Supported Languages

- 🇺🇸 English
- 🇫🇷 Français  
- 🇩🇪 Deutsch
- 🇸🇦 العربية
- 🇲🇦 الدارجة (Darija)

## Author

**Baha Mlouk** - AI Engineer
