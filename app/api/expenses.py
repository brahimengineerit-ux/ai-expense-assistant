"""
Expenses API Router
===================
All expense extraction endpoints including receipt parsing.
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
    OCRExpenseResponse,
    FullReceiptResponse
)
from app.services.extractor import (
    extract_single_expense,
    extract_multiple_expenses,
    extract_batch
)
from app.services.ocr import process_receipt, process_receipt_from_url
from app.services.receipt_parser import (
    parse_receipt_full,
    parse_receipt_from_image,
    parse_receipt_from_url as parse_receipt_url
)
from app.services.pdf_processor import (
    extract_text_from_pdf,
    pdf_page_to_image,
    get_pdf_info
)
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
    
    Supports multiple languages: English, French, German, Arabic, Darija.
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
# RECEIPT PARSER ENDPOINTS (NEW)
# ============================================================

@router.post("/receipt/parse/text", response_model=FullReceiptResponse)
def parse_receipt_text(
    text: str,
    extract_line_items: bool = Query(True, description="Extract individual line items"),
    extract_vendor: bool = Query(True, description="Extract vendor details"),
    extract_tax: bool = Query(True, description="Extract tax breakdown")
):
    """
    🧾 Parse receipt/invoice from text.
    
    Extracts:
    - Vendor info (name, address, phone, tax ID)
    - Invoice details (number, date, type)
    - Line items (products with qty, price, total)
    - Tax breakdown (subtotal, tax rate, tax amount, total)
    - Payment info (method, status)
    """
    try:
        result = parse_receipt_full(
            text=text,
            extract_line_items=extract_line_items,
            extract_vendor=extract_vendor,
            extract_tax=extract_tax
        )
        
        return FullReceiptResponse(
            success=True,
            source="text",
            invoice=result.get("invoice"),
            vendor=result.get("vendor"),
            line_items=result.get("line_items", []),
            line_items_count=len(result.get("line_items", [])),
            totals=result.get("totals"),
            payment_method=result.get("payment", {}).get("method"),
            payment_status=result.get("payment", {}).get("status"),
            language_detected=result.get("language_detected")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receipt/parse/upload", response_model=FullReceiptResponse)
async def parse_receipt_upload(
    file: UploadFile = File(..., description="Receipt/invoice image or PDF"),
    extract_line_items: bool = Query(True, description="Extract line items"),
    extract_vendor: bool = Query(True, description="Extract vendor details"),
    extract_tax: bool = Query(True, description="Extract tax breakdown")
):
    """
    🧾 Parse receipt/invoice from uploaded image or PDF.
    
    Supports: JPEG, PNG, WebP, GIF, PDF
    
    Returns full structured data including:
    - Vendor info
    - Line items (each product)
    - Tax breakdown
    - Invoice number
    - Payment status
    """
    allowed_image_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    allowed_pdf_types = ["application/pdf"]
    
    file_bytes = await file.read()
    
    try:
        # Handle PDF
        if file.content_type in allowed_pdf_types:
            # Get PDF info
            pdf_info = get_pdf_info(file_bytes)
            
            # Try text extraction first
            extracted_text = extract_text_from_pdf(file_bytes)
            
            if extracted_text.strip() and len(extracted_text) > 50:
                # PDF has text, use text parsing
                result = parse_receipt_full(
                    text=extracted_text,
                    extract_line_items=extract_line_items,
                    extract_vendor=extract_vendor,
                    extract_tax=extract_tax
                )
                source = "pdf_text"
            else:
                # PDF is scanned, convert to image and use OCR
                image_bytes = pdf_page_to_image(file_bytes, page_num=0, dpi=200)
                result = parse_receipt_from_image(
                    image_bytes=image_bytes,
                    mime_type="image/png",
                    extract_line_items=extract_line_items,
                    extract_vendor=extract_vendor,
                    extract_tax=extract_tax
                )
                source = "pdf_ocr"
                extracted_text = result.get("extracted_text", "")
        
        # Handle images
        elif file.content_type in allowed_image_types:
            result = parse_receipt_from_image(
                image_bytes=file_bytes,
                mime_type=file.content_type,
                extract_line_items=extract_line_items,
                extract_vendor=extract_vendor,
                extract_tax=extract_tax
            )
            source = "image_upload"
            extracted_text = result.get("extracted_text", "")
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed: images (JPEG, PNG, WebP, GIF) and PDF"
            )
        
        return FullReceiptResponse(
            success=True,
            source=source,
            invoice=result.get("invoice"),
            vendor=result.get("vendor"),
            line_items=result.get("line_items", []),
            line_items_count=len(result.get("line_items", [])),
            totals=result.get("totals"),
            payment_method=result.get("payment", {}).get("method"),
            payment_status=result.get("payment", {}).get("status"),
            extracted_text=extracted_text[:2000] if extracted_text else None,
            language_detected=result.get("language_detected"),
            confidence=result.get("confidence")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receipt/parse/url", response_model=FullReceiptResponse)
def parse_receipt_from_image_url(
    image_url: str,
    extract_line_items: bool = Query(True, description="Extract line items"),
    extract_vendor: bool = Query(True, description="Extract vendor details"),
    extract_tax: bool = Query(True, description="Extract tax breakdown")
):
    """
    🧾 Parse receipt/invoice from image URL.
    """
    try:
        result = parse_receipt_url(
            image_url=image_url,
            extract_line_items=extract_line_items,
            extract_vendor=extract_vendor,
            extract_tax=extract_tax
        )
        
        return FullReceiptResponse(
            success=True,
            source="image_url",
            invoice=result.get("invoice"),
            vendor=result.get("vendor"),
            line_items=result.get("line_items", []),
            line_items_count=len(result.get("line_items", [])),
            totals=result.get("totals"),
            payment_method=result.get("payment", {}).get("method"),
            payment_status=result.get("payment", {}).get("status"),
            extracted_text=result.get("extracted_text"),
            language_detected=result.get("language_detected"),
            confidence=result.get("confidence")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# PDF ENDPOINTS (NEW)
# ============================================================

@router.post("/pdf/info")
async def get_pdf_information(
    file: UploadFile = File(..., description="PDF file")
):
    """
    📄 Get PDF information (page count, metadata, has text/images).
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        pdf_bytes = await file.read()
        info = get_pdf_info(pdf_bytes)
        return {"success": True, **info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf/extract-text")
async def extract_pdf_text(
    file: UploadFile = File(..., description="PDF file")
):
    """
    📄 Extract text from PDF.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        pdf_bytes = await file.read()
        text = extract_text_from_pdf(pdf_bytes)
        return {
            "success": True,
            "text": text,
            "char_count": len(text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ANALYTICS ENDPOINTS
# ============================================================

@router.post("/analytics", response_model=AnalyticsResponse)
def get_analytics(request: AnalyticsRequest):
    """
    Analyze expenses and get insights.
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
