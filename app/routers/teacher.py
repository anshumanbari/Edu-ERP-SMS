import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    TeacherDeleteResponse,
    PaginatedTeacherResponse,
)
from app.crud import teacher as crud

router = APIRouter(
    prefix="/teachers",
    tags=["Teachers"],
)


# ---------------------------------------------------------------------------
# POST /teachers/  — Create a new teacher
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=TeacherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new teacher",
)
def create_teacher(
    payload: TeacherCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TeacherResponse:
    """
    Create a teacher record. Requires the **admin** role.

    - **name**: Full name of the teacher.
    - **email**: Unique email address — must not already exist.
    - **phone**: Contact phone number.
    - **subject**: Subject taught by the teacher.
    - **experience_years**: Years of teaching experience.

    Raises **409 Conflict** if the email is already registered.
    """
    return crud.create_teacher(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /teachers/  — Retrieve all teachers (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedTeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all teachers (paginated)",
)
def get_all_teachers(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, email, or phone"
    ),
    subject: str | None = Query(None, max_length=100, description="Filter by exact subject"),
    experience_years: int | None = Query(
        None, ge=0, le=60, description="Filter by exact years of experience"
    ),
    sort_by: Literal["id", "name", "experience_years"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedTeacherResponse:
    """
    Return a paginated list of registered teachers.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, email, or phone.
    - **subject**: Optional exact subject filter.
    - **experience_years**: Optional exact experience filter.
    - **sort_by**: Optional field to sort by (id, name, experience_years).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    teachers, total_records = crud.get_paginated_teachers(
        db=db,
        page=page,
        limit=limit,
        search=search,
        subject=subject,
        experience_years=experience_years,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedTeacherResponse(
        teachers=teachers,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /teachers/{teacher_id}  — Retrieve a single teacher
# ---------------------------------------------------------------------------
@router.get(
    "/{teacher_id}",
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a teacher by ID",
)
def get_teacher(
    teacher_id: int = Path(..., gt=0, description="Primary key of the teacher"),
    db: Session = Depends(get_db),
) -> TeacherResponse:
    """
    Fetch a single teacher by their primary key.

    Raises **404 Not Found** if no teacher with that ID exists.
    """
    teacher = crud.get_teacher_by_id(db=db, teacher_id=teacher_id)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found.",
        )
    return teacher


# ---------------------------------------------------------------------------
# PUT /teachers/{teacher_id}  — Update a teacher
# ---------------------------------------------------------------------------
@router.put(
    "/{teacher_id}",
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a teacher by ID",
)
def update_teacher(
    payload: TeacherUpdate,
    teacher_id: int = Path(..., gt=0, description="Primary key of the teacher"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TeacherResponse:
    """
    Update a teacher's details by their primary key. Requires the **admin** role.

    Raises **404 Not Found** if no teacher with that ID exists.
    """
    teacher = crud.update_teacher(db=db, teacher_id=teacher_id, payload=payload)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found.",
        )
    return teacher


# ---------------------------------------------------------------------------
# DELETE /teachers/{teacher_id}  — Delete a teacher
# ---------------------------------------------------------------------------
@router.delete(
    "/{teacher_id}",
    response_model=TeacherDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a teacher by ID",
)
def delete_teacher(
    teacher_id: int = Path(..., gt=0, description="Primary key of the teacher"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TeacherDeleteResponse:
    """
    Permanently remove a teacher record by their primary key. Requires the **admin** role.

    Raises **404 Not Found** if no teacher with that ID exists.
    Returns a success message on deletion.
    """
    teacher = crud.delete_teacher(db=db, teacher_id=teacher_id)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found.",
        )
    return TeacherDeleteResponse(
        message=f"Teacher with ID {teacher_id} deleted successfully."
    )
