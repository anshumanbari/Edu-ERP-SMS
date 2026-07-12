from datetime import date
from typing import List, Literal

from pydantic import BaseModel, Field, ConfigDict


class EnrollmentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    student_id: int = Field(..., gt=0, description="Primary key of the student being enrolled")
    academic_session_id: int = Field(
        ..., gt=0, description="Primary key of the academic session for this enrollment"
    )
    program_id: int = Field(..., gt=0, description="Primary key of the program the student is enrolling into")
    semester_id: int = Field(
        ..., gt=0, description="Primary key of the semester the student is enrolling into (must belong to program_id)"
    )
    section_id: int = Field(
        ...,
        gt=0,
        description="Primary key of the section the student is enrolling into (must belong to program_id and semester_id)",
    )
    enrollment_date: date = Field(..., description="Calendar date the enrollment took effect")
    status: Literal["active", "completed", "dropped", "transferred"] = Field(
        "active", description="Current state of the enrollment"
    )
    remarks: str | None = Field(None, max_length=255, description="Optional free-text notes")


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(EnrollmentBase):
    pass


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    academic_session_id: int
    program_id: int
    semester_id: int
    section_id: int
    enrollment_date: date
    status: str
    remarks: str | None = None


class EnrollmentDeleteResponse(BaseModel):
    message: str


class PaginatedEnrollmentResponse(BaseModel):
    enrollments: List[EnrollmentResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
