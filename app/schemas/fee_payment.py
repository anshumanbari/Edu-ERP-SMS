from datetime import date
from typing import List, Literal

from pydantic import BaseModel, Field, ConfigDict


class FeePaymentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    student_id: int = Field(..., gt=0, description="Primary key of the student this payment belongs to")
    fee_structure_id: int = Field(..., gt=0, description="Primary key of the fee structure being paid against")
    amount_paid: float = Field(0, ge=0, description="Cumulative amount the student has paid so far")
    payment_date: date | None = Field(
        None, description="Calendar date the (latest) payment was made; ignored if amount_paid is 0"
    )
    remarks: str | None = Field(None, max_length=255, description="Optional free-text notes")


class FeePaymentCreate(FeePaymentBase):
    pass


class FeePaymentUpdate(FeePaymentBase):
    pass


class FeePaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    fee_structure_id: int
    amount_paid: float
    payment_date: date | None = None
    status: Literal["paid", "pending", "overdue"]
    remarks: str | None = None


class FeePaymentDeleteResponse(BaseModel):
    message: str


class PaginatedFeePaymentResponse(BaseModel):
    fee_payments: List[FeePaymentResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
