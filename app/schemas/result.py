from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field, ConfigDict


class ResultGenerateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    student_id: int = Field(..., gt=0, description="Primary key of the student to generate a result for")
    academic_session_id: int = Field(
        ..., gt=0, description="Primary key of the academic session to generate the result for"
    )


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    academic_session_id: int
    total_marks_obtained: float
    total_max_marks: float
    percentage: float
    status: Literal["pass", "fail"]
    is_published: bool
    published_at: datetime | None = None
    remarks: str | None = None


class ResultDeleteResponse(BaseModel):
    message: str


class PaginatedResultResponse(BaseModel):
    results: List[ResultResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
