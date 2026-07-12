from datetime import date
from typing import List

from pydantic import BaseModel, Field, ConfigDict, model_validator


class ExaminationBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=2, max_length=150, description="Administrator-defined examination name, e.g. 'Midterm Examination'"
    )
    subject_id: int = Field(..., gt=0, description="Primary key of the subject this examination covers")
    academic_session_id: int = Field(
        ..., gt=0, description="Primary key of the academic session this examination belongs to"
    )
    exam_date: date = Field(..., description="Calendar date the examination is/was held")
    max_marks: int = Field(..., gt=0, description="Maximum marks obtainable in this examination")
    passing_marks: int = Field(..., gt=0, description="Minimum marks required to pass this examination")
    is_active: bool = Field(True, description="Whether the examination is currently active/visible")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")

    @model_validator(mode="after")
    def _validate_passing_marks(self) -> "ExaminationBase":
        if self.passing_marks > self.max_marks:
            raise ValueError("passing_marks cannot exceed max_marks.")
        return self


class ExaminationCreate(ExaminationBase):
    pass


class ExaminationUpdate(ExaminationBase):
    pass


class ExaminationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    subject_id: int
    academic_session_id: int
    exam_date: date
    max_marks: int
    passing_marks: int
    is_active: bool
    description: str | None = None


class ExaminationDeleteResponse(BaseModel):
    message: str


class PaginatedExaminationResponse(BaseModel):
    examinations: List[ExaminationResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
