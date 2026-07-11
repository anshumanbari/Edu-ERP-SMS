from datetime import date
from typing import List, Literal

from pydantic import BaseModel, Field, ConfigDict, model_validator


class AcademicSessionBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    session_name: str = Field(
        ..., min_length=4, max_length=50, description="Administrator-defined session label, e.g. '2026-2027'"
    )
    start_date: date = Field(..., description="Date the academic session begins")
    end_date: date = Field(..., description="Date the academic session ends")
    status: Literal["upcoming", "active", "completed"] = Field(
        "upcoming", description="Lifecycle status of the session"
    )
    is_current: bool = Field(
        False, description="Whether this is the currently active session referenced by other modules"
    )
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")

    @model_validator(mode="after")
    def validate_date_range(self) -> "AcademicSessionBase":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class AcademicSessionCreate(AcademicSessionBase):
    pass


class AcademicSessionUpdate(AcademicSessionBase):
    pass


class AcademicSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_name: str
    start_date: date
    end_date: date
    status: str
    is_current: bool
    description: str | None = None


class AcademicSessionDeleteResponse(BaseModel):
    message: str


class PaginatedAcademicSessionResponse(BaseModel):
    academic_sessions: List[AcademicSessionResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
