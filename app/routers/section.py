import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.section import (
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionDeleteResponse,
    PaginatedSectionResponse,
)
from app.crud import section as crud

router = APIRouter(
    prefix="/sections",
    tags=["Sections"],
)


# ---------------------------------------------------------------------------
# POST /sections/  — Create a new section
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new section",
)
def create_section(
    payload: SectionCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SectionResponse:
    """
    Create a section record. Requires the **admin** role.

    - **name**: Administrator-defined section name (e.g. "A"), unique within its program+semester.
    - **code**: Administrator-defined short code (e.g. "SEC-A"), unique within its program+semester.
    - **program_id**: Primary key of the program this section belongs to.
    - **semester_id**: Primary key of the semester this section belongs to (must belong to program_id).
    - **is_active**: Whether the section is active/selectable (default true).
    - **description**: Optional free-text notes.

    Raises **404 Not Found** if program_id or semester_id does not reference an existing record.
    Raises **400 Bad Request** if semester_id does not belong to program_id.
    Raises **409 Conflict** if name or code is already used within the program+semester.
    """
    return crud.create_section(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /sections/  — Retrieve all sections (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedSectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all sections (paginated)",
)
def get_all_sections(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, code, or description"
    ),
    program_id: int | None = Query(None, gt=0, description="Filter by exact program_id"),
    semester_id: int | None = Query(None, gt=0, description="Filter by exact semester_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "code"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedSectionResponse:
    """
    Return a paginated list of configured sections.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, code, or description.
    - **program_id** / **semester_id**: Optional exact filters.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, code).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    sections, total_records = crud.get_paginated_sections(
        db=db,
        page=page,
        limit=limit,
        search=search,
        program_id=program_id,
        semester_id=semester_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedSectionResponse(
        sections=sections,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /sections/{section_id}  — Retrieve a single section
# ---------------------------------------------------------------------------
@router.get(
    "/{section_id}",
    response_model=SectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a section by ID",
)
def get_section(
    section_id: int = Path(..., gt=0, description="Primary key of the section"),
    db: Session = Depends(get_db),
) -> SectionResponse:
    """
    Fetch a single section by its primary key.

    Raises **404 Not Found** if no section with that ID exists.
    """
    section = crud.get_section_by_id(db=db, section_id=section_id)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with ID {section_id} not found.",
        )
    return section


# ---------------------------------------------------------------------------
# PUT /sections/{section_id}  — Update a section
# ---------------------------------------------------------------------------
@router.put(
    "/{section_id}",
    response_model=SectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a section by ID",
)
def update_section(
    payload: SectionUpdate,
    section_id: int = Path(..., gt=0, description="Primary key of the section"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SectionResponse:
    """
    Update a section's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a section by toggling **is_active**.

    Raises **404 Not Found** if no section with that ID exists, or if program_id/semester_id
    does not reference an existing record.
    Raises **400 Bad Request** if semester_id does not belong to program_id.
    Raises **409 Conflict** if the new name/code is already used within the target program+semester.
    """
    section = crud.update_section(db=db, section_id=section_id, payload=payload)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with ID {section_id} not found.",
        )
    return section


# ---------------------------------------------------------------------------
# DELETE /sections/{section_id}  — Delete a section
# ---------------------------------------------------------------------------
@router.delete(
    "/{section_id}",
    response_model=SectionDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a section by ID",
)
def delete_section(
    section_id: int = Path(..., gt=0, description="Primary key of the section"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SectionDeleteResponse:
    """
    Permanently remove a section record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no section with that ID exists.
    Returns a success message on deletion.
    """
    section = crud.delete_section(db=db, section_id=section_id)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with ID {section_id} not found.",
        )
    return SectionDeleteResponse(
        message=f"Section with ID {section_id} deleted successfully."
    )
