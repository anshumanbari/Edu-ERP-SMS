import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.timetable import (
    TimetableCreate,
    TimetableUpdate,
    TimetableResponse,
    TimetableDeleteResponse,
    PaginatedTimetableResponse,
)
from app.crud import timetable as crud

router = APIRouter(
    prefix="/timetables",
    tags=["Timetable"],
)


# ---------------------------------------------------------------------------
# POST /timetables/  — Create a new timetable entry
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=TimetableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new timetable entry",
)
def create_timetable_entry(
    payload: TimetableCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TimetableResponse:
    """
    Schedule a recurring weekly class period. Requires the **admin** role.

    - **section_id**, **subject_id**, **teacher_id**, **classroom_id**, **academic_session_id**:
      Must reference existing records.
    - **day_of_week**: Day the class recurs on.
    - **start_time** / **end_time**: Class period's time range (end must be after start).
    - **is_active**: Whether the entry is currently active (default true).
    - **remarks**: Optional free-text notes.

    Raises **404 Not Found** if any referenced record does not exist.
    Raises **409 Conflict** if the section, teacher, or classroom already has an
    overlapping class scheduled on the same day within the same academic session.
    """
    return crud.create_timetable_entry(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /timetables/  — Retrieve timetable entries (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedTimetableResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve timetable entries (paginated)",
)
def get_all_timetable_entries(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(None, max_length=100, description="Search term matched against remarks"),
    section_id: int | None = Query(None, gt=0, description="Filter by exact section_id"),
    subject_id: int | None = Query(None, gt=0, description="Filter by exact subject_id"),
    teacher_id: int | None = Query(None, gt=0, description="Filter by exact teacher_id"),
    classroom_id: int | None = Query(None, gt=0, description="Filter by exact classroom_id"),
    academic_session_id: int | None = Query(None, gt=0, description="Filter by exact academic_session_id"),
    day_of_week: Literal[
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ] | None = Query(None, description="Filter by exact day_of_week"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "day_of_week", "start_time"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> PaginatedTimetableResponse:
    """
    Return a paginated list of timetable entries. Requires the **admin** or
    **teacher** role.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against remarks.
    - **section_id** / **subject_id** / **teacher_id** / **classroom_id** / **academic_session_id**:
      Optional exact filters.
    - **day_of_week**: Optional exact day filter.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, day_of_week, start_time).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    entries, total_records = crud.get_paginated_timetable_entries(
        db=db,
        page=page,
        limit=limit,
        search=search,
        section_id=section_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        classroom_id=classroom_id,
        academic_session_id=academic_session_id,
        day_of_week=day_of_week,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedTimetableResponse(
        timetables=entries,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /timetables/{timetable_id}  — Retrieve a single timetable entry
# ---------------------------------------------------------------------------
@router.get(
    "/{timetable_id}",
    response_model=TimetableResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a timetable entry by ID",
)
def get_timetable_entry(
    timetable_id: int = Path(..., gt=0, description="Primary key of the timetable entry"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> TimetableResponse:
    """
    Fetch a single timetable entry by its primary key. Requires the **admin**
    or **teacher** role.

    Raises **404 Not Found** if no entry with that ID exists.
    """
    entry = crud.get_timetable_entry_by_id(db=db, timetable_id=timetable_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable entry with ID {timetable_id} not found.",
        )
    return entry


# ---------------------------------------------------------------------------
# PUT /timetables/{timetable_id}  — Update a timetable entry
# ---------------------------------------------------------------------------
@router.put(
    "/{timetable_id}",
    response_model=TimetableResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a timetable entry by ID",
)
def update_timetable_entry(
    payload: TimetableUpdate,
    timetable_id: int = Path(..., gt=0, description="Primary key of the timetable entry"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TimetableResponse:
    """
    Update a timetable entry by its primary key. Requires the **admin** role.

    Also used to activate/deactivate an entry by toggling **is_active**.

    Raises **404 Not Found** if no entry with that ID exists, or if any
    referenced record does not exist.
    Raises **409 Conflict** if the change collides with an existing schedule for
    the section, teacher, or classroom.
    """
    entry = crud.update_timetable_entry(db=db, timetable_id=timetable_id, payload=payload)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable entry with ID {timetable_id} not found.",
        )
    return entry


# ---------------------------------------------------------------------------
# DELETE /timetables/{timetable_id}  — Delete a timetable entry
# ---------------------------------------------------------------------------
@router.delete(
    "/{timetable_id}",
    response_model=TimetableDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a timetable entry by ID",
)
def delete_timetable_entry(
    timetable_id: int = Path(..., gt=0, description="Primary key of the timetable entry"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> TimetableDeleteResponse:
    """
    Permanently remove a timetable entry by its primary key. Requires the
    **admin** role.

    Raises **404 Not Found** if no entry with that ID exists.
    Returns a success message on deletion.
    """
    entry = crud.delete_timetable_entry(db=db, timetable_id=timetable_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable entry with ID {timetable_id} not found.",
        )
    return TimetableDeleteResponse(
        message=f"Timetable entry with ID {timetable_id} deleted successfully."
    )
