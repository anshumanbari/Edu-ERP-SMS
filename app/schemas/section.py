from typing import List

from pydantic import BaseModel, Field, ConfigDict


class SectionBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=1, max_length=50, description="Administrator-defined section name, e.g. 'A'"
    )
    code: str = Field(
        ..., min_length=1, max_length=20, description="Administrator-defined short code, e.g. 'SEC-A'"
    )
    program_id: int = Field(..., gt=0, description="Primary key of the program this section belongs to")
    semester_id: int = Field(..., gt=0, description="Primary key of the semester this section belongs to")
    is_active: bool = Field(True, description="Whether the section is currently active and selectable")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class SectionCreate(SectionBase):
    pass


class SectionUpdate(SectionBase):
    pass


class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    program_id: int
    semester_id: int
    is_active: bool
    description: str | None = None


class SectionDeleteResponse(BaseModel):
    message: str


class PaginatedSectionResponse(BaseModel):
    sections: List[SectionResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
