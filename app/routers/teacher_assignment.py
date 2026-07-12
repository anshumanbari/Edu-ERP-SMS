import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.teacher_assignment import (
    TeacherAssignmentCreate,
    TeacherAssignmentUpdate,
    TeacherAssignmentResponse,
    TeacherAssignmentDeleteResponse,
    PaginatedTeacherAssignmentResponse,
)
from app.crud import teacher_assignment as crud

router = APIRouter(
    prefix="/teacher-assignments",
    tags=["Teacher Assignments"],
)


# ---------------------------------------------------------------------------
# POST /teacher-assignments/  — Assign a teacher to a subject/section
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=TeacherAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a teacher to a subject and section",
)
def create_teacher_assignment(
    payload: TeacherAssignmentCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TeacherAssignmentResponse:
    """
    Assign a teacher to a subject within a section for an academic session.
    Requires the **admin** role.

    - **teacher_id**, **subject_id**, **section_id**, **academic_session_id**:
      Must reference existing records.
    - **is_active**: Whether the assignment is currently in effect (default true).
    - **remarks**: Optional free-text notes.

    Raises **404 Not Found** if any referenced record does not exist.
    Raises **409 Conflict** if the subject+section already has a teacher assigned
    for the academic session.
    """
    return crud.create_teacher_assignment(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /teacher-assignments/  — Retrieve assignments (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedTeacherAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve teacher assignments (paginated)",
)
def get_all_teacher_assignments(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(None, max_length=100, description="Search term matched against remarks"),
    teacher_id: int | None = Query(None, gt=0, description="Filter by exact teacher_id"),
    subject_id: int | None = Query(None, gt=0, description="Filter by exact subject_id"),
    section_id: int | None = Query(None, gt=0, description="Filter by exact section_id"),
    academic_session_id: int | None = Query(None, gt=0, description="Filter by exact academic_session_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id"] | None = Query(None, description="Field to sort by"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> PaginatedTeacherAssignmentResponse:
    """
    Return a paginated list of teacher assignments. Requires the **admin** or
    **teacher** role.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against remarks.
    - **teacher_id** / **subject_id** / **section_id** / **academic_session_id**:
      Optional exact filters.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    assignments, total_records = crud.get_paginated_teacher_assignments(
        db=db,
        page=page,
        limit=limit,
        search=search,
        teacher_id=teacher_id,
        subject_id=subject_id,
        section_id=section_id,
        academic_session_id=academic_session_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedTeacherAssignmentResponse(
        teacher_assignments=assignments,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /teacher-assignments/{assignment_id}  — Retrieve a single assignment
# ---------------------------------------------------------------------------
@router.get(
    "/{assignment_id}",
    response_model=TeacherAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a teacher assignment by ID",
)
def get_teacher_assignment(
    assignment_id: int = Path(..., gt=0, description="Primary key of the teacher assignment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> TeacherAssignmentResponse:
    """
    Fetch a single teacher assignment by its primary key. Requires the **admin**
    or **teacher** role.

    Raises **404 Not Found** if no assignment with that ID exists.
    """
    assignment = crud.get_teacher_assignment_by_id(db=db, assignment_id=assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher assignment with ID {assignment_id} not found.",
        )
    return assignment


# ---------------------------------------------------------------------------
# PUT /teacher-assignments/{assignment_id}  — Update an assignment
# ---------------------------------------------------------------------------
@router.put(
    "/{assignment_id}",
    response_model=TeacherAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a teacher assignment by ID",
)
def update_teacher_assignment(
    payload: TeacherAssignmentUpdate,
    assignment_id: int = Path(..., gt=0, description="Primary key of the teacher assignment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TeacherAssignmentResponse:
    """
    Update a teacher assignment by its primary key. Requires the **admin** role.

    Also used to activate/deactivate an assignment by toggling **is_active**.

    Raises **404 Not Found** if no assignment with that ID exists, or if any
    referenced record does not exist.
    Raises **409 Conflict** if the change collides with an existing assignment
    for the same subject+section+academic session.
    """
    assignment = crud.update_teacher_assignment(
        db=db, assignment_id=assignment_id, payload=payload
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher assignment with ID {assignment_id} not found.",
        )
    return assignment


# ---------------------------------------------------------------------------
# DELETE /teacher-assignments/{assignment_id}  — Delete an assignment
# ---------------------------------------------------------------------------
@router.delete(
    "/{assignment_id}",
    response_model=TeacherAssignmentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a teacher assignment by ID",
)
def delete_teacher_assignment(
    assignment_id: int = Path(..., gt=0, description="Primary key of the teacher assignment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TeacherAssignmentDeleteResponse:
    """
    Permanently remove a teacher assignment record by its primary key.
    Requires the **admin** role.

    Raises **404 Not Found** if no assignment with that ID exists.
    Returns a success message on deletion.
    """
    assignment = crud.delete_teacher_assignment(db=db, assignment_id=assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher assignment with ID {assignment_id} not found.",
        )
    return TeacherAssignmentDeleteResponse(
        message=f"Teacher assignment with ID {assignment_id} deleted successfully."
    )
