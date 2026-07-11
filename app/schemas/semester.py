from typing import List

from pydantic import BaseModel, Field, ConfigDict


class SemesterBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=2, max_length=100, description="Administrator-defined semester name, e.g. 'Semester 1'"
    )
    code: str = Field(
        ..., min_length=1, max_length=20, description="Administrator-defined short code, e.g. 'SEM1'"
    )
    program_id: int = Field(..., gt=0, description="Primary key of the program this semester belongs to")
    sequence_number: int = Field(
        ..., ge=1, le=20, description="Administrator-defined order of this semester within its program"
    )
    is_active: bool = Field(True, description="Whether the semester is currently active and selectable")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(SemesterBase):
    pass


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    program_id: int
    sequence_number: int
    is_active: bool
    description: str | None = None


class SemesterDeleteResponse(BaseModel):
    message: str


class PaginatedSemesterResponse(BaseModel):
    semesters: List[SemesterResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
