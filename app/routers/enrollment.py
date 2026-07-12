import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    EnrollmentDeleteResponse,
    PaginatedEnrollmentResponse,
)
from app.crud import enrollment as crud

router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"],
)


# ---------------------------------------------------------------------------
# POST /enrollments/  — Create a new enrollment
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll a student",
)
def create_enrollment(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> EnrollmentResponse:
    """
    Enroll a student into an academic session, program, semester, and section.
    Requires the **admin** role.

    - **student_id**, **academic_session_id**, **program_id**, **semester_id**, **section_id**:
      Must reference existing records.
    - **semester_id** must belong to **program_id**.
    - **section_id** must belong to **program_id** and **semester_id**.
    - **enrollment_date**: Calendar date the enrollment took effect.
    - **status**: "active", "completed", "dropped", or "transferred" (default "active").
    - **remarks**: Optional free-text notes.

    Raises **404 Not Found** if any referenced record does not exist.
    Raises **400 Bad Request** if semester/section do not belong to the given program/semester.
    Raises **409 Conflict** if the student already has an enrollment for this academic session.
    """
    return crud.create_enrollment(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /enrollments/  — Retrieve enrollments (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedEnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve enrollments (paginated)",
)
def get_all_enrollments(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(None, max_length=100, description="Search term matched against remarks"),
    student_id: int | None = Query(None, gt=0, description="Filter by exact student_id"),
    academic_session_id: int | None = Query(None, gt=0, description="Filter by exact academic_session_id"),
    program_id: int | None = Query(None, gt=0, description="Filter by exact program_id"),
    semester_id: int | None = Query(None, gt=0, description="Filter by exact semester_id"),
    section_id: int | None = Query(None, gt=0, description="Filter by exact section_id"),
    status_filter: Literal["active", "completed", "dropped", "transferred"] | None = Query(
        None, alias="status", description="Filter by exact status"
    ),
    sort_by: Literal["id", "enrollment_date", "status"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> PaginatedEnrollmentResponse:
    """
    Return a paginated list of enrollments. Requires the **admin** or **teacher** role.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against remarks.
    - **student_id** / **academic_session_id** / **program_id** / **semester_id** / **section_id**:
      Optional exact filters.
    - **status**: Optional exact status filter.
    - **sort_by**: Optional field to sort by (id, enrollment_date, status).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    enrollments, total_records = crud.get_paginated_enrollments(
        db=db,
        page=page,
        limit=limit,
        search=search,
        student_id=student_id,
        academic_session_id=academic_session_id,
        program_id=program_id,
        semester_id=semester_id,
        section_id=section_id,
        status_filter=status_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedEnrollmentResponse(
        enrollments=enrollments,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /enrollments/{enrollment_id}  — Retrieve a single enrollment
# ---------------------------------------------------------------------------
@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an enrollment by ID",
)
def get_enrollment(
    enrollment_id: int = Path(..., gt=0, description="Primary key of the enrollment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> EnrollmentResponse:
    """
    Fetch a single enrollment by its primary key. Requires the **admin** or **teacher** role.

    Raises **404 Not Found** if no enrollment with that ID exists.
    """
    enrollment = crud.get_enrollment_by_id(db=db, enrollment_id=enrollment_id)
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment with ID {enrollment_id} not found.",
        )
    return enrollment


# ---------------------------------------------------------------------------
# PUT /enrollments/{enrollment_id}  — Update an enrollment
# ---------------------------------------------------------------------------
@router.put(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an enrollment by ID",
)
def update_enrollment(
    payload: EnrollmentUpdate,
    enrollment_id: int = Path(..., gt=0, description="Primary key of the enrollment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> EnrollmentResponse:
    """
    Update an enrollment's details by its primary key. Requires the **admin** role.

    Also used to change enrollment **status** (e.g. to "completed", "dropped", or "transferred").

    Raises **404 Not Found** if no enrollment with that ID exists, or if any referenced
    record does not exist.
    Raises **400 Bad Request** if semester/section do not belong to the given program/semester.
    Raises **409 Conflict** if the change collides with an existing student/session enrollment.
    """
    enrollment = crud.update_enrollment(db=db, enrollment_id=enrollment_id, payload=payload)
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment with ID {enrollment_id} not found.",
        )
    return enrollment


# ---------------------------------------------------------------------------
# DELETE /enrollments/{enrollment_id}  — Delete an enrollment
# ---------------------------------------------------------------------------
@router.delete(
    "/{enrollment_id}",
    response_model=EnrollmentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an enrollment by ID",
)
def delete_enrollment(
    enrollment_id: int = Path(..., gt=0, description="Primary key of the enrollment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> EnrollmentDeleteResponse:
    """
    Permanently remove an enrollment record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no enrollment with that ID exists.
    Returns a success message on deletion.
    """
    enrollment = crud.delete_enrollment(db=db, enrollment_id=enrollment_id)
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment with ID {enrollment_id} not found.",
        )
    return EnrollmentDeleteResponse(
        message=f"Enrollment with ID {enrollment_id} deleted successfully."
    )
