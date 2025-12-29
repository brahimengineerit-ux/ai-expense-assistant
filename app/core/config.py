import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

# App settings
APP_NAME = "AI Expense Analysis Assistant"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = "Advanced AI-powered expense extraction with multi-language support, OCR, and analytics"

# Supported languages
SUPPORTED_LANGUAGES = ["en", "fr", "de", "ar", "darija"]

# Default expense categories
EXPENSE_CATEGORIES = [
    "transport",
    "food",
    "utilities",
    "rent",
    "entertainment",
    "shopping",
    "health",
    "education",
    "travel",
    "other"
]
