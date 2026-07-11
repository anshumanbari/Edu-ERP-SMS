import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.semester import (
    SemesterCreate,
    SemesterUpdate,
    SemesterResponse,
    SemesterDeleteResponse,
    PaginatedSemesterResponse,
)
from app.crud import semester as crud

router = APIRouter(
    prefix="/semesters",
    tags=["Semesters"],
)


# ---------------------------------------------------------------------------
# POST /semesters/  — Create a new semester
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=SemesterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new semester",
)
def create_semester(
    payload: SemesterCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SemesterResponse:
    """
    Create a semester record. Requires the **admin** role.

    - **name**: Administrator-defined semester name (e.g. "Semester 1"), unique within its program.
    - **code**: Administrator-defined short code (e.g. "SEM1"), unique within its program.
    - **program_id**: Primary key of the program this semester belongs to.
    - **sequence_number**: Administrator-defined order within the program, unique within its program.
    - **is_active**: Whether the semester is active/selectable (default true).
    - **description**: Optional free-text notes.

    Raises **404 Not Found** if program_id does not reference an existing program.
    Raises **409 Conflict** if name, code, or sequence_number is already used within the program.
    """
    return crud.create_semester(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /semesters/  — Retrieve all semesters (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedSemesterResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all semesters (paginated)",
)
def get_all_semesters(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, code, or description"
    ),
    program_id: int | None = Query(None, gt=0, description="Filter by exact program_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "sequence_number"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedSemesterResponse:
    """
    Return a paginated list of configured semesters.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, code, or description.
    - **program_id**: Optional exact program filter.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, sequence_number).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    semesters, total_records = crud.get_paginated_semesters(
        db=db,
        page=page,
        limit=limit,
        search=search,
        program_id=program_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedSemesterResponse(
        semesters=semesters,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /semesters/{semester_id}  — Retrieve a single semester
# ---------------------------------------------------------------------------
@router.get(
    "/{semester_id}",
    response_model=SemesterResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a semester by ID",
)
def get_semester(
    semester_id: int = Path(..., gt=0, description="Primary key of the semester"),
    db: Session = Depends(get_db),
) -> SemesterResponse:
    """
    Fetch a single semester by its primary key.

    Raises **404 Not Found** if no semester with that ID exists.
    """
    semester = crud.get_semester_by_id(db=db, semester_id=semester_id)
    if semester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found.",
        )
    return semester


# ---------------------------------------------------------------------------
# PUT /semesters/{semester_id}  — Update a semester
# ---------------------------------------------------------------------------
@router.put(
    "/{semester_id}",
    response_model=SemesterResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a semester by ID",
)
def update_semester(
    payload: SemesterUpdate,
    semester_id: int = Path(..., gt=0, description="Primary key of the semester"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SemesterResponse:
    """
    Update a semester's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a semester by toggling **is_active**.

    Raises **404 Not Found** if no semester with that ID exists, or if program_id
    does not reference an existing program.
    Raises **409 Conflict** if the new name/code/sequence_number is already used
    within the target program.
    """
    semester = crud.update_semester(db=db, semester_id=semester_id, payload=payload)
    if semester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found.",
        )
    return semester


# ---------------------------------------------------------------------------
# DELETE /semesters/{semester_id}  — Delete a semester
# ---------------------------------------------------------------------------
@router.delete(
    "/{semester_id}",
    response_model=SemesterDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a semester by ID",
)
def delete_semester(
    semester_id: int = Path(..., gt=0, description="Primary key of the semester"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SemesterDeleteResponse:
    """
    Permanently remove a semester record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no semester with that ID exists.
    Returns a success message on deletion.
    """
    semester = crud.delete_semester(db=db, semester_id=semester_id)
    if semester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found.",
        )
    return SemesterDeleteResponse(
        message=f"Semester with ID {semester_id} deleted successfully."
    )
