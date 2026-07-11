from typing import List

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class StudentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=100, description="The full name of the student")
    email: EmailStr = Field(..., max_length=100, description="The unique email address of the student")
    phone: int = Field(
        ...,
        ge=1000000,
        le=999999999999999,
        description="The contact phone number of the student (digits only, 7-15 digits)",
    )
    course: str = Field(..., min_length=1, max_length=100, description="The enrolled course or program")
    semester: int = Field(..., ge=1, le=8, description="The current semester (between 1 and 8)")


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: int
    course: str
    semester: int


class StudentDeleteResponse(BaseModel):
    message: str


class PaginatedStudentResponse(BaseModel):
    students: List[StudentResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
