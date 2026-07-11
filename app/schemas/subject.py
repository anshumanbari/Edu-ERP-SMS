from typing import List

from pydantic import BaseModel, Field, ConfigDict


class SubjectBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=2, max_length=100, description="Administrator-defined subject name, e.g. 'Data Structures Lab'"
    )
    code: str = Field(
        ..., min_length=2, max_length=20, description="Administrator-defined short code, e.g. 'CS201L'"
    )
    course_id: int = Field(..., gt=0, description="Primary key of the course this subject belongs to")
    is_active: bool = Field(True, description="Whether the subject is currently active and selectable")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(SubjectBase):
    pass


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    course_id: int
    is_active: bool
    description: str | None = None


class SubjectDeleteResponse(BaseModel):
    message: str


class PaginatedSubjectResponse(BaseModel):
    subjects: List[SubjectResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
