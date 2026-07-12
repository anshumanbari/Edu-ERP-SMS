import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.models.user import User
from app.schemas.result import (
    ResultGenerateRequest,
    ResultResponse,
    ResultDeleteResponse,
    PaginatedResultResponse,
)
from app.crud import result as crud

router = APIRouter(
    prefix="/results",
    tags=["Results"],
)


# ---------------------------------------------------------------------------
# POST /results/generate  — Generate a student's result from exam marks
# ---------------------------------------------------------------------------
@router.post(
    "/generate",
    response_model=ResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a student's result from their exam marks",
)
def generate_result(
    payload: ResultGenerateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(Role.ADMIN)),
) -> ResultResponse:
    """
    Generate a result for a student in an academic session by aggregating all
    of their recorded exam marks. Requires the **admin** role.

    - **student_id**, **academic_session_id**: Must reference existing records.

    Totals, percentage, and pass/fail status are computed from the student's
    ExamMark records for examinations within the academic session (a student
    fails overall if any individual exam mark is below that exam's passing_marks).

    The generated result is **unpublished** by default and not visible to students
    until an administrator publishes it.

    Raises **404 Not Found** if student_id/academic_session_id does not exist, or if
    the student has no exam marks recorded for the academic session.
    Raises **409 Conflict** if a result has already been generated for this student+session.
    """
    return crud.generate_result(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /results/  — Retrieve results (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve results (paginated)",
)
def get_all_results(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    student_id: int | None = Query(None, gt=0, description="Filter by exact student_id"),
    academic_session_id: int | None = Query(None, gt=0, description="Filter by exact academic_session_id"),
    status_filter: Literal["pass", "fail"] | None = Query(
        None, alias="status", description="Filter by exact status"
    ),
    is_published: bool | None = Query(
        None, description="Filter by is_published flag (ignored for the student role, who only ever see published results)"
    ),
    sort_by: Literal["id", "percentage"] | None = Query(None, description="Field to sort by"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.STUDENT)),
) -> PaginatedResultResponse:
    """
    Return a paginated list of results. Accessible to **admin** and **student** roles.

    Students may only view **published** results — the is_published filter is
    forced to true for the student role regardless of the query parameter.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **student_id** / **academic_session_id**: Optional exact filters.
    - **status**: Optional exact status filter ("pass"/"fail").
    - **is_published**: Optional exact is_published filter (admin only).
    - **sort_by**: Optional field to sort by (id, percentage).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    effective_is_published = True if current_user.role == Role.STUDENT else is_published

    results, total_records = crud.get_paginated_results(
        db=db,
        page=page,
        limit=limit,
        student_id=student_id,
        academic_session_id=academic_session_id,
        status_filter=status_filter,
        is_published=effective_is_published,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedResultResponse(
        results=results,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /results/{result_id}  — Retrieve a single result
# ---------------------------------------------------------------------------
@router.get(
    "/{result_id}",
    response_model=ResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a result by ID",
)
def get_result(
    result_id: int = Path(..., gt=0, description="Primary key of the result"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.STUDENT)),
) -> ResultResponse:
    """
    Fetch a single result by its primary key. Accessible to **admin** and
    **student** roles.

    Students may only view **published** results; an unpublished result is
    reported as not found to the student role.

    Raises **404 Not Found** if no result with that ID exists (or, for the
    student role, if the result is not yet published).
    """
    result = crud.get_result_by_id(db=db, result_id=result_id)
    if result is None or (current_user.role == Role.STUDENT and not result.is_published):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result with ID {result_id} not found.",
        )
    return result


# ---------------------------------------------------------------------------
# POST /results/{result_id}/publish  — Publish a result
# ---------------------------------------------------------------------------
@router.post(
    "/{result_id}/publish",
    response_model=ResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish a result",
)
def publish_result(
    result_id: int = Path(..., gt=0, description="Primary key of the result"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(Role.ADMIN)),
) -> ResultResponse:
    """
    Publish a result, making it visible to the student. Requires the **admin** role.

    Raises **404 Not Found** if no result with that ID exists.
    Raises **409 Conflict** if the result is already published.
    """
    result = crud.publish_result(db=db, result_id=result_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result with ID {result_id} not found.",
        )
    return result


# ---------------------------------------------------------------------------
# DELETE /results/{result_id}  — Delete a result
# ---------------------------------------------------------------------------
@router.delete(
    "/{result_id}",
    response_model=ResultDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a result by ID",
)
def delete_result(
    result_id: int = Path(..., gt=0, description="Primary key of the result"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(Role.ADMIN)),
) -> ResultDeleteResponse:
    """
    Permanently remove a result record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no result with that ID exists.
    Returns a success message on deletion.
    """
    result = crud.delete_result(db=db, result_id=result_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result with ID {result_id} not found.",
        )
    return ResultDeleteResponse(message=f"Result with ID {result_id} deleted successfully.")
