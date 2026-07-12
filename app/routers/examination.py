import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.examination import (
    ExaminationCreate,
    ExaminationUpdate,
    ExaminationResponse,
    ExaminationDeleteResponse,
    PaginatedExaminationResponse,
)
from app.crud import examination as crud

router = APIRouter(
    prefix="/examinations",
    tags=["Examinations"],
)


# ---------------------------------------------------------------------------
# POST /examinations/  — Create a new examination
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ExaminationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new examination",
)
def create_examination(
    payload: ExaminationCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ExaminationResponse:
    """
    Create an examination record. Requires the **admin** role.

    - **name**: Administrator-defined examination name (e.g. "Midterm Examination"),
      unique within its subject+academic session.
    - **subject_id**: Primary key of the subject this examination covers.
    - **academic_session_id**: Primary key of the academic session this examination belongs to.
    - **exam_date**: Calendar date the examination is/was held.
    - **max_marks** / **passing_marks**: Marks configuration (passing_marks cannot exceed max_marks).
    - **is_active**: Whether the examination is active/visible (default true).
    - **description**: Optional free-text notes.

    Raises **404 Not Found** if subject_id or academic_session_id does not reference an existing record.
    Raises **409 Conflict** if the name is already used within the same subject and academic session.
    """
    return crud.create_examination(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /examinations/  — Retrieve all examinations (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedExaminationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all examinations (paginated)",
)
def get_all_examinations(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name or description"
    ),
    subject_id: int | None = Query(None, gt=0, description="Filter by exact subject_id"),
    academic_session_id: int | None = Query(None, gt=0, description="Filter by exact academic_session_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "exam_date"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER, Role.STUDENT)),
) -> PaginatedExaminationResponse:
    """
    Return a paginated list of examinations. Accessible to **admin**, **teacher**,
    and **student** roles.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name or description.
    - **subject_id** / **academic_session_id**: Optional exact filters.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, exam_date).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    examinations, total_records = crud.get_paginated_examinations(
        db=db,
        page=page,
        limit=limit,
        search=search,
        subject_id=subject_id,
        academic_session_id=academic_session_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedExaminationResponse(
        examinations=examinations,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /examinations/{examination_id}  — Retrieve a single examination
# ---------------------------------------------------------------------------
@router.get(
    "/{examination_id}",
    response_model=ExaminationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an examination by ID",
)
def get_examination(
    examination_id: int = Path(..., gt=0, description="Primary key of the examination"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER, Role.STUDENT)),
) -> ExaminationResponse:
    """
    Fetch a single examination by its primary key. Accessible to **admin**,
    **teacher**, and **student** roles.

    Raises **404 Not Found** if no examination with that ID exists.
    """
    examination = crud.get_examination_by_id(db=db, examination_id=examination_id)
    if examination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Examination with ID {examination_id} not found.",
        )
    return examination


# ---------------------------------------------------------------------------
# PUT /examinations/{examination_id}  — Update an examination
# ---------------------------------------------------------------------------
@router.put(
    "/{examination_id}",
    response_model=ExaminationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an examination by ID",
)
def update_examination(
    payload: ExaminationUpdate,
    examination_id: int = Path(..., gt=0, description="Primary key of the examination"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ExaminationResponse:
    """
    Update an examination's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate an examination by toggling **is_active**.

    Raises **404 Not Found** if no examination with that ID exists, or if
    subject_id/academic_session_id does not reference an existing record.
    Raises **409 Conflict** if the new name is already used within the target subject+session.
    """
    examination = crud.update_examination(db=db, examination_id=examination_id, payload=payload)
    if examination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Examination with ID {examination_id} not found.",
        )
    return examination


# ---------------------------------------------------------------------------
# DELETE /examinations/{examination_id}  — Delete an examination
# ---------------------------------------------------------------------------
@router.delete(
    "/{examination_id}",
    response_model=ExaminationDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an examination by ID",
)
def delete_examination(
    examination_id: int = Path(..., gt=0, description="Primary key of the examination"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ExaminationDeleteResponse:
    """
    Permanently remove an examination record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no examination with that ID exists.
    Returns a success message on deletion.
    """
    examination = crud.delete_examination(db=db, examination_id=examination_id)
    if examination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Examination with ID {examination_id} not found.",
        )
    return ExaminationDeleteResponse(
        message=f"Examination with ID {examination_id} deleted successfully."
    )
