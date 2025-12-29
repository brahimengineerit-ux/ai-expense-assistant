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
    extracted_text: str
    expenses: list[dict]
    confidence: Optional[float] = None
