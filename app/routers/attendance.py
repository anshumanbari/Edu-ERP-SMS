import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    AttendanceDeleteResponse,
    PaginatedAttendanceResponse,
)
from app.crud import attendance as crud

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


# ---------------------------------------------------------------------------
# POST /attendance/  — Record a new attendance entry
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new attendance entry",
)
def create_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> AttendanceResponse:
    """
    Record an attendance entry. Requires the **admin** or **teacher** role.

    - **student_id**, **subject_id**, **academic_session_id**: Must reference existing records.
    - **attendance_date**: Calendar date the attendance was taken.
    - **status**: "present", "absent", "late", or "excused".
    - **remarks**: Optional free-text notes.

    The recording user (from the JWT session) is stored as **marked_by_id**.

    Raises **404 Not Found** if any referenced record does not exist.
    Raises **409 Conflict** if attendance for this student/subject/date already exists.
    """
    return crud.create_attendance(db=db, payload=payload, marked_by_id=current_user.id)


# ---------------------------------------------------------------------------
# GET /attendance/  — Retrieve attendance records (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedAttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve attendance records (paginated)",
)
def get_all_attendance_records(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(None, max_length=100, description="Search term matched against remarks"),
    student_id: int | None = Query(None, gt=0, description="Filter by exact student_id"),
    subject_id: int | None = Query(None, gt=0, description="Filter by exact subject_id"),
    academic_session_id: int | None = Query(None, gt=0, description="Filter by exact academic_session_id"),
    status_filter: Literal["present", "absent", "late", "excused"] | None = Query(
        None, alias="status", description="Filter by exact status"
    ),
    sort_by: Literal["id", "attendance_date", "status"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> PaginatedAttendanceResponse:
    """
    Return a paginated list of attendance records. Requires the **admin** or **teacher** role.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against remarks.
    - **student_id** / **subject_id** / **academic_session_id**: Optional exact filters.
    - **status**: Optional exact status filter.
    - **sort_by**: Optional field to sort by (id, attendance_date, status).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    attendance_records, total_records = crud.get_paginated_attendance_records(
        db=db,
        page=page,
        limit=limit,
        search=search,
        student_id=student_id,
        subject_id=subject_id,
        academic_session_id=academic_session_id,
        status_filter=status_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedAttendanceResponse(
        attendance_records=attendance_records,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /attendance/{attendance_id}  — Retrieve a single attendance record
# ---------------------------------------------------------------------------
@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an attendance record by ID",
)
def get_attendance(
    attendance_id: int = Path(..., gt=0, description="Primary key of the attendance record"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> AttendanceResponse:
    """
    Fetch a single attendance record by its primary key. Requires the **admin** or **teacher** role.

    Raises **404 Not Found** if no record with that ID exists.
    """
    attendance = crud.get_attendance_by_id(db=db, attendance_id=attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found.",
        )
    return attendance


# ---------------------------------------------------------------------------
# PUT /attendance/{attendance_id}  — Update an attendance record
# ---------------------------------------------------------------------------
@router.put(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an attendance record by ID",
)
def update_attendance(
    payload: AttendanceUpdate,
    attendance_id: int = Path(..., gt=0, description="Primary key of the attendance record"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> AttendanceResponse:
    """
    Update an attendance record by its primary key. Requires the **admin** or **teacher** role.

    Raises **404 Not Found** if no record with that ID exists, or if student_id,
    subject_id, or academic_session_id does not reference an existing record.
    Raises **409 Conflict** if the change collides with an existing student/subject/date entry.
    """
    attendance = crud.update_attendance(db=db, attendance_id=attendance_id, payload=payload)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found.",
        )
    return attendance


# ---------------------------------------------------------------------------
# DELETE /attendance/{attendance_id}  — Delete an attendance record
# ---------------------------------------------------------------------------
@router.delete(
    "/{attendance_id}",
    response_model=AttendanceDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an attendance record by ID",
)
def delete_attendance(
    attendance_id: int = Path(..., gt=0, description="Primary key of the attendance record"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> AttendanceDeleteResponse:
    """
    Permanently remove an attendance record by its primary key. Requires the **admin** or **teacher** role.

    Raises **404 Not Found** if no record with that ID exists.
    Returns a success message on deletion.
    """
    attendance = crud.delete_attendance(db=db, attendance_id=attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found.",
        )
    return AttendanceDeleteResponse(
        message=f"Attendance record with ID {attendance_id} deleted successfully."
    )
