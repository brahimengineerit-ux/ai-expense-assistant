"""
AI Expense Analysis Assistant
=============================
Advanced AI-powered expense extraction with:
- Multi-language support (EN, FR, AR, Darija)
- Multi-expense detection from single text
- Receipt/Invoice OCR
- Analytics & insights
- Excel/CSV export

Version: 3.0.0
Author: Baha Mlouk
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.api.expenses import router as expenses_router
from app.core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, EXPENSE_CATEGORIES

# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Expenses",
            "description": "Extract, analyze, and export expense data"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Static files (if needed)
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(expenses_router)


# ============================================================
# WEB INTERFACE
# ============================================================

@app.get("/", response_class=HTMLResponse, tags=["Web"])
async def home(request: Request):
    """Serve the web interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/app", response_class=HTMLResponse, tags=["Web"])
async def app_page(request: Request):
    """Alternative route for web interface"""
    return templates.TemplateResponse("index.html", {"request": request})


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api", tags=["Health"])
def api_info():
    """API health check and info"""
    return {
        "status": "ok",
        "name": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs"
    }


@app.get("/info", tags=["Health"])
def info():
    """API information and capabilities"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "capabilities": {
            "single_extraction": "Extract one expense from text",
            "multi_extraction": "Extract multiple expenses from one text",
            "batch_processing": "Process multiple texts at once",
            "ocr": "Extract from receipt/invoice images",
            "analytics": "Generate insights and summaries",
            "export": "Export to CSV and Excel"
        },
        "supported_languages": ["English", "French", "Arabic", "Moroccan Darija"],
        "expense_categories": EXPENSE_CATEGORIES,
        "endpoints": {
            "extract_single": "POST /expenses/extract",
            "extract_multi": "POST /expenses/extract/multi",
            "extract_batch": "POST /expenses/extract/batch",
            "ocr_upload": "POST /expenses/ocr/upload",
            "ocr_url": "POST /expenses/ocr/url",
            "analytics": "POST /expenses/analytics",
            "summary": "POST /expenses/analytics/summary",
            "anomalies": "POST /expenses/analytics/anomalies",
            "export_csv": "POST /expenses/export/csv",
            "export_excel": "POST /expenses/export/excel"
        }
    }
