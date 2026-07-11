import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.academic_session import (
    AcademicSessionCreate,
    AcademicSessionUpdate,
    AcademicSessionResponse,
    AcademicSessionDeleteResponse,
    PaginatedAcademicSessionResponse,
)
from app.crud import academic_session as crud

router = APIRouter(
    prefix="/academic-sessions",
    tags=["Academic Sessions"],
)


# ---------------------------------------------------------------------------
# POST /academic-sessions/  — Create a new academic session
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=AcademicSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new academic session",
)
def create_academic_session(
    payload: AcademicSessionCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> AcademicSessionResponse:
    """
    Create an academic session record. Requires the **admin** role.

    - **session_name**: Administrator-defined label (e.g. "2026-2027") — must not already exist.
    - **start_date** / **end_date**: end_date must be after start_date.
    - **status**: "upcoming", "active", or "completed".
    - **is_current**: If true, clears the flag on any other session so only one is ever current.
    - **description**: Optional free-text notes.

    Raises **409 Conflict** if session_name is already registered.
    """
    return crud.create_academic_session(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /academic-sessions/  — Retrieve all academic sessions (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedAcademicSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all academic sessions (paginated)",
)
def get_all_academic_sessions(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against session_name or description"
    ),
    status_filter: Literal["upcoming", "active", "completed"] | None = Query(
        None, alias="status", description="Filter by exact status"
    ),
    is_current: bool | None = Query(None, description="Filter by is_current flag"),
    sort_by: Literal["id", "session_name", "start_date"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedAcademicSessionResponse:
    """
    Return a paginated list of configured academic sessions.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against session_name or description.
    - **status**: Optional exact status filter.
    - **is_current**: Optional exact is_current filter.
    - **sort_by**: Optional field to sort by (id, session_name, start_date).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    academic_sessions, total_records = crud.get_paginated_academic_sessions(
        db=db,
        page=page,
        limit=limit,
        search=search,
        status_filter=status_filter,
        is_current=is_current,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedAcademicSessionResponse(
        academic_sessions=academic_sessions,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /academic-sessions/{academic_session_id}  — Retrieve a single session
# ---------------------------------------------------------------------------
@router.get(
    "/{academic_session_id}",
    response_model=AcademicSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an academic session by ID",
)
def get_academic_session(
    academic_session_id: int = Path(..., gt=0, description="Primary key of the academic session"),
    db: Session = Depends(get_db),
) -> AcademicSessionResponse:
    """
    Fetch a single academic session by its primary key.

    Raises **404 Not Found** if no session with that ID exists.
    """
    academic_session = crud.get_academic_session_by_id(db=db, academic_session_id=academic_session_id)
    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )
    return academic_session


# ---------------------------------------------------------------------------
# PUT /academic-sessions/{academic_session_id}  — Update a session
# ---------------------------------------------------------------------------
@router.put(
    "/{academic_session_id}",
    response_model=AcademicSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an academic session by ID",
)
def update_academic_session(
    payload: AcademicSessionUpdate,
    academic_session_id: int = Path(..., gt=0, description="Primary key of the academic session"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> AcademicSessionResponse:
    """
    Update an academic session's details by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no session with that ID exists.
    Raises **409 Conflict** if renaming to a session_name already in use.
    """
    academic_session = crud.update_academic_session(
        db=db, academic_session_id=academic_session_id, payload=payload
    )
    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )
    return academic_session


# ---------------------------------------------------------------------------
# DELETE /academic-sessions/{academic_session_id}  — Delete a session
# ---------------------------------------------------------------------------
@router.delete(
    "/{academic_session_id}",
    response_model=AcademicSessionDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an academic session by ID",
)
def delete_academic_session(
    academic_session_id: int = Path(..., gt=0, description="Primary key of the academic session"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> AcademicSessionDeleteResponse:
    """
    Permanently remove an academic session record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no session with that ID exists.
    Returns a success message on deletion.
    """
    academic_session = crud.delete_academic_session(db=db, academic_session_id=academic_session_id)
    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )
    return AcademicSessionDeleteResponse(
        message=f"Academic session with ID {academic_session_id} deleted successfully."
    )
