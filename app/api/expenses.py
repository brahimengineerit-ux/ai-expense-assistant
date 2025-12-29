"""
Expenses API Router
===================
All expense extraction endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import io

from app.models.schemas import (
    SingleExpenseRequest,
    MultiExpenseRequest,
    BatchExpenseRequest,
    AnalyticsRequest,
    SingleExpenseResponse,
    MultiExpenseResponse,
    BatchExpenseResponse,
    AnalyticsResponse,
    OCRExpenseResponse
)
from app.services.extractor import (
    extract_single_expense,
    extract_multiple_expenses,
    extract_batch
)
from app.services.ocr import process_receipt, process_receipt_from_url
from app.services.analytics import analyze_expenses, generate_summary, detect_anomalies
from app.services.export import export_to_csv, export_to_excel

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ============================================================
# EXTRACTION ENDPOINTS
# ============================================================

@router.post("/extract", response_model=SingleExpenseResponse)
def extract_single(request: SingleExpenseRequest):
    """
    Extract a single expense from text.
    
    Supports multiple languages: English, French, Arabic, Darija.
    
    Example:
    ```json
    {
      "text": "I paid 15 dh for a taxi this morning",
      "expense_type": "transport",
      "fields": ["amount", "currency", "payment_method", "date"]
    }
    ```
    """
    try:
        result = extract_single_expense(
            text=request.text,
            expense_type=request.expense_type,
            fields=request.fields,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/multi", response_model=MultiExpenseResponse)
def extract_multi(request: MultiExpenseRequest):
    """
    Extract multiple expenses from a single text.
    
    Example:
    ```json
    {
      "text": "Today I spent 20dh on taxi, 45dh on lunch, and 100dh on phone bill",
      "fields": ["amount", "currency", "category", "description"]
    }
    ```
    
    Or in Darija:
    ```json
    {
      "text": "khlsst 50dh f taxi w 30dh f sandwich",
      "fields": ["amount", "currency", "category"]
    }
    ```
    """
    try:
        result = extract_multiple_expenses(
            text=request.text,
            fields=request.fields,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/batch", response_model=BatchExpenseResponse)
def extract_batch_endpoint(request: BatchExpenseRequest):
    """
    Process multiple expense texts in batch.
    
    Example:
    ```json
    {
      "texts": [
        "Taxi to airport 150dh",
        "Coffee at Starbucks 45dh",
        "Monthly Netflix subscription 50dh"
      ],
      "fields": ["amount", "currency", "category", "description"]
    }
    ```
    """
    try:
        result = extract_batch(
            texts=request.texts,
            fields=request.fields
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# OCR ENDPOINTS
# ============================================================

@router.post("/ocr/upload", response_model=OCRExpenseResponse)
async def ocr_upload(
    file: UploadFile = File(..., description="Receipt or invoice image"),
    fields: str = Query(
        default="amount,currency,category,description,date,vendor",
        description="Comma-separated fields to extract"
    )
):
    """
    Extract expenses from uploaded receipt/invoice image.
    
    Supports: JPEG, PNG, WebP, GIF
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        image_bytes = await file.read()
        field_list = [f.strip() for f in fields.split(",")]
        
        result = process_receipt(
            image_bytes=image_bytes,
            mime_type=file.content_type,
            fields=field_list
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/url", response_model=OCRExpenseResponse)
def ocr_from_url(
    image_url: str,
    fields: str = Query(
        default="amount,currency,category,description,date,vendor",
        description="Comma-separated fields to extract"
    )
):
    """
    Extract expenses from receipt image URL.
    """
    try:
        field_list = [f.strip() for f in fields.split(",")]
        result = process_receipt_from_url(
            image_url=image_url,
            fields=field_list
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ANALYTICS ENDPOINTS
# ============================================================

@router.post("/analytics", response_model=AnalyticsResponse)
def get_analytics(request: AnalyticsRequest):
    """
    Analyze expenses and get insights.
    
    Example:
    ```json
    {
      "expenses": [
        {"amount": 20, "currency": "MAD", "category": "transport"},
        {"amount": 45, "currency": "MAD", "category": "food"},
        {"amount": 100, "currency": "MAD", "category": "utilities"}
      ],
      "group_by": "category"
    }
    ```
    """
    try:
        result = analyze_expenses(
            expenses=request.expenses,
            group_by=request.group_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/summary")
def get_summary(expenses: list[dict], period: str = "this period"):
    """
    Get human-readable expense summary.
    """
    try:
        summary = generate_summary(expenses, period)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/anomalies")
def get_anomalies(
    expenses: list[dict],
    threshold: float = Query(default=2.0, description="Standard deviation threshold")
):
    """
    Detect unusual expenses.
    """
    try:
        anomalies = detect_anomalies(expenses, threshold)
        return {
            "count": len(anomalies),
            "anomalies": anomalies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# EXPORT ENDPOINTS
# ============================================================

@router.post("/export/csv")
def export_csv(expenses: list[dict]):
    """
    Export expenses to CSV.
    """
    try:
        csv_content = export_to_csv(expenses)
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=expenses.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/excel")
def export_excel_endpoint(
    expenses: list[dict],
    title: str = Query(default="Expense Report", description="Report title"),
    include_summary: bool = Query(default=True, description="Include summary sheet")
):
    """
    Export expenses to Excel with formatting.
    """
    try:
        excel_bytes = export_to_excel(
            expenses=expenses,
            include_summary=include_summary,
            title=title
        )
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
