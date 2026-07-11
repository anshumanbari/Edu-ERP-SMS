from typing import List

from pydantic import BaseModel, Field, ConfigDict


class ProgramBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=2, max_length=100, description="Administrator-defined program name, e.g. 'B.Tech Computer Science'"
    )
    code: str = Field(
        ..., min_length=2, max_length=20, description="Administrator-defined short code, e.g. 'BTCS'"
    )
    department_id: int = Field(..., gt=0, description="Primary key of the department this program belongs to")
    is_active: bool = Field(True, description="Whether the program is currently active and selectable")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(ProgramBase):
    pass


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    department_id: int
    is_active: bool
    description: str | None = None


class ProgramDeleteResponse(BaseModel):
    message: str


class PaginatedProgramResponse(BaseModel):
    programs: List[ProgramResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
