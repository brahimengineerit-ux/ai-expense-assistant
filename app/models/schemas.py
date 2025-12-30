from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ============================================================
# REQUEST MODELS
# ============================================================

class SingleExpenseRequest(BaseModel):
    """Extract one expense from text"""
    text: str = Field(..., description="Free-text expense description")
    expense_type: Optional[str] = Field(None, description="Type hint (transport, food, etc.)")
    fields: Optional[list[str]] = Field(
        default=["amount", "currency", "category", "description", "date", "payment_method"],
        description="Fields to extract"
    )
    language: Optional[str] = Field(None, description="Language hint (en, fr, ar, darija)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "I paid 15 dh for a taxi this morning",
                    "expense_type": "transport",
                    "fields": ["amount", "currency", "payment_method", "date"]
                }
            ]
        }
    }


class MultiExpenseRequest(BaseModel):
    """Extract multiple expenses from one text"""
    text: str = Field(..., description="Text containing multiple expenses")
    fields: Optional[list[str]] = Field(
        default=["amount", "currency", "category", "description", "date", "payment_method"],
        description="Fields to extract for each expense"
    )
    language: Optional[str] = Field(None, description="Language hint")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Today I spent 20dh on taxi, 45dh on lunch, and 100dh on phone bill",
                    "fields": ["amount", "currency", "category", "description"]
                }
            ]
        }
    }


class BatchExpenseRequest(BaseModel):
    """Process multiple texts at once"""
    texts: list[str] = Field(..., description="List of expense descriptions")
    fields: Optional[list[str]] = Field(
        default=["amount", "currency", "category", "description", "date", "payment_method"],
        description="Fields to extract"
    )


class AnalyticsRequest(BaseModel):
    """Request expense analytics"""
    expenses: list[dict] = Field(..., description="List of extracted expenses")
    group_by: Optional[str] = Field("category", description="Group by: category, date, payment_method")


class ReceiptParseRequest(BaseModel):
    """Request for full receipt/invoice parsing"""
    extract_line_items: bool = Field(True, description="Extract individual line items")
    extract_vendor: bool = Field(True, description="Extract vendor details")
    extract_tax: bool = Field(True, description="Extract tax breakdown")
    language: Optional[str] = Field(None, description="Language hint")


# ============================================================
# RESPONSE MODELS
# ============================================================

class ExpenseData(BaseModel):
    """Single extracted expense"""
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    payment_method: Optional[str] = None


class LineItem(BaseModel):
    """Single line item from receipt"""
    description: str
    quantity: Optional[float] = 1
    unit_price: Optional[float] = None
    total: float
    category: Optional[str] = None


class VendorInfo(BaseModel):
    """Vendor/merchant information"""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    website: Optional[str] = None


class TaxBreakdown(BaseModel):
    """Tax breakdown information"""
    subtotal: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    discount: Optional[float] = None
    total: float
    currency: str = "MAD"


class InvoiceInfo(BaseModel):
    """Invoice/receipt metadata"""
    number: Optional[str] = None
    date: Optional[str] = None
    due_date: Optional[str] = None
    type: str = "receipt"  # receipt, invoice, bill


class FullReceiptResponse(BaseModel):
    """Complete receipt/invoice parsing response"""
    success: bool
    source: str  # image_upload, pdf_upload, url, text
    
    # Invoice metadata
    invoice: Optional[InvoiceInfo] = None
    
    # Vendor info
    vendor: Optional[VendorInfo] = None
    
    # Line items
    line_items: list[LineItem] = []
    line_items_count: int = 0
    
    # Totals & tax
    totals: Optional[TaxBreakdown] = None
    
    # Payment info
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    
    # Metadata
    extracted_text: Optional[str] = None
    language_detected: Optional[str] = None
    confidence: Optional[float] = None


class SingleExpenseResponse(BaseModel):
    """Response for single expense extraction"""
    success: bool
    journal: str = "expenses"
    expense_type: Optional[str] = None
    data: dict
    language_detected: Optional[str] = None


class MultiExpenseResponse(BaseModel):
    """Response for multi-expense extraction"""
    success: bool
    count: int
    expenses: list[dict]
    language_detected: Optional[str] = None


class BatchExpenseResponse(BaseModel):
    """Response for batch processing"""
    success: bool
    total: int
    processed: int
    failed: int
    results: list[dict]


class AnalyticsResponse(BaseModel):
    """Response for analytics"""
    success: bool
    total_amount: float
    currency: str
    count: int
    breakdown: dict
    insights: list[str]


class OCRExpenseResponse(BaseModel):
    """Response for OCR extraction"""
    success: bool
    source: Optional[str] = None
    extracted_text: Optional[str] = None
    expenses: list[dict] = []
    count: int = 0
    language_detected: Optional[str] = None
    confidence: Optional[float] = None
