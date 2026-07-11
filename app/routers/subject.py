import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.subject import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectDeleteResponse,
    PaginatedSubjectResponse,
)
from app.crud import subject as crud

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
)


# ---------------------------------------------------------------------------
# POST /subjects/  — Create a new subject
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subject",
)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SubjectResponse:
    """
    Create a subject record. Requires the **admin** role.

    - **name**: Administrator-defined subject name (e.g. "Data Structures Lab"), unique within its course.
    - **code**: Administrator-defined short code (e.g. "CS201L"), unique within its course.
    - **course_id**: Primary key of the course this subject belongs to.
    - **is_active**: Whether the subject is active/selectable (default true).
    - **description**: Optional free-text notes.

    Raises **404 Not Found** if course_id does not reference an existing course.
    Raises **409 Conflict** if name or code is already used within the course.
    """
    return crud.create_subject(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /subjects/  — Retrieve all subjects (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedSubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all subjects (paginated)",
)
def get_all_subjects(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, code, or description"
    ),
    course_id: int | None = Query(None, gt=0, description="Filter by exact course_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "code"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedSubjectResponse:
    """
    Return a paginated list of configured subjects.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, code, or description.
    - **course_id**: Optional exact course filter.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, code).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    subjects, total_records = crud.get_paginated_subjects(
        db=db,
        page=page,
        limit=limit,
        search=search,
        course_id=course_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedSubjectResponse(
        subjects=subjects,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /subjects/{subject_id}  — Retrieve a single subject
# ---------------------------------------------------------------------------
@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a subject by ID",
)
def get_subject(
    subject_id: int = Path(..., gt=0, description="Primary key of the subject"),
    db: Session = Depends(get_db),
) -> SubjectResponse:
    """
    Fetch a single subject by its primary key.

    Raises **404 Not Found** if no subject with that ID exists.
    """
    subject = crud.get_subject_by_id(db=db, subject_id=subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    return subject


# ---------------------------------------------------------------------------
# PUT /subjects/{subject_id}  — Update a subject
# ---------------------------------------------------------------------------
@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a subject by ID",
)
def update_subject(
    payload: SubjectUpdate,
    subject_id: int = Path(..., gt=0, description="Primary key of the subject"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SubjectResponse:
    """
    Update a subject's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a subject by toggling **is_active**.

    Raises **404 Not Found** if no subject with that ID exists, or if course_id
    does not reference an existing course.
    Raises **409 Conflict** if the new name/code is already used within the target course.
    """
    subject = crud.update_subject(db=db, subject_id=subject_id, payload=payload)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    return subject


# ---------------------------------------------------------------------------
# DELETE /subjects/{subject_id}  — Delete a subject
# ---------------------------------------------------------------------------
@router.delete(
    "/{subject_id}",
    response_model=SubjectDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a subject by ID",
)
def delete_subject(
    subject_id: int = Path(..., gt=0, description="Primary key of the subject"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> SubjectDeleteResponse:
    """
    Permanently remove a subject record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no subject with that ID exists.
    Returns a success message on deletion.
    """
    subject = crud.delete_subject(db=db, subject_id=subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    return SubjectDeleteResponse(
        message=f"Subject with ID {subject_id} deleted successfully."
    )
