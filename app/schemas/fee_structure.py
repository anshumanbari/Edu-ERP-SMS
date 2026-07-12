from datetime import date
from typing import List

from pydantic import BaseModel, Field, ConfigDict


class FeeStructureBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=2, max_length=100, description="Administrator-defined fee name, e.g. 'Tuition Fee'"
    )
    program_id: int = Field(..., gt=0, description="Primary key of the program this fee applies to")
    semester_id: int = Field(
        ..., gt=0, description="Primary key of the semester this fee applies to (must belong to program_id)"
    )
    academic_session_id: int = Field(
        ..., gt=0, description="Primary key of the academic session this fee applies to"
    )
    amount: float = Field(..., gt=0, description="Amount due for this fee")
    due_date: date = Field(..., description="Calendar date payment is due by")
    is_active: bool = Field(True, description="Whether this fee structure is currently active")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class FeeStructureCreate(FeeStructureBase):
    pass


class FeeStructureUpdate(FeeStructureBase):
    pass


class FeeStructureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    program_id: int
    semester_id: int
    academic_session_id: int
    amount: float
    due_date: date
    is_active: bool
    description: str | None = None


class FeeStructureDeleteResponse(BaseModel):
    message: str


class PaginatedFeeStructureResponse(BaseModel):
    fee_structures: List[FeeStructureResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
