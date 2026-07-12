from typing import List

from pydantic import BaseModel, Field, ConfigDict


class ExamMarkBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    examination_id: int = Field(..., gt=0, description="Primary key of the examination this mark belongs to")
    student_id: int = Field(..., gt=0, description="Primary key of the student being graded")
    teacher_id: int = Field(
        ..., gt=0, description="Primary key of the teacher entering the mark (must be assigned to the examination's subject)"
    )
    marks_obtained: float = Field(..., ge=0, description="Marks scored by the student")
    remarks: str | None = Field(None, max_length=255, description="Optional free-text notes")


class ExamMarkCreate(ExamMarkBase):
    pass


class ExamMarkUpdate(ExamMarkBase):
    pass


class ExamMarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    examination_id: int
    student_id: int
    teacher_id: int
    marks_obtained: float
    remarks: str | None = None


class ExamMarkDeleteResponse(BaseModel):
    message: str


class PaginatedExamMarkResponse(BaseModel):
    exam_marks: List[ExamMarkResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
