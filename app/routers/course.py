import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDeleteResponse,
    PaginatedCourseResponse,
)
from app.crud import course as crud

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


# ---------------------------------------------------------------------------
# POST /courses/  — Create a new course
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> CourseResponse:
    """
    Create a course record. Requires the **admin** role.

    - **name**: Administrator-defined course name (e.g. "Data Structures"), unique within its semester.
    - **code**: Administrator-defined short code (e.g. "CS201"), unique within its semester.
    - **semester_id**: Primary key of the semester this course belongs to.
    - **credit_hours**: Administrator-defined credit hours for the course.
    - **is_active**: Whether the course is active/selectable (default true).
    - **description**: Optional free-text notes.

    Raises **404 Not Found** if semester_id does not reference an existing semester.
    Raises **409 Conflict** if name or code is already used within the semester.
    """
    return crud.create_course(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /courses/  — Retrieve all courses (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedCourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all courses (paginated)",
)
def get_all_courses(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, code, or description"
    ),
    semester_id: int | None = Query(None, gt=0, description="Filter by exact semester_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "credit_hours"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedCourseResponse:
    """
    Return a paginated list of configured courses.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, code, or description.
    - **semester_id**: Optional exact semester filter.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, credit_hours).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    courses, total_records = crud.get_paginated_courses(
        db=db,
        page=page,
        limit=limit,
        search=search,
        semester_id=semester_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedCourseResponse(
        courses=courses,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /courses/{course_id}  — Retrieve a single course
# ---------------------------------------------------------------------------
@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a course by ID",
)
def get_course(
    course_id: int = Path(..., gt=0, description="Primary key of the course"),
    db: Session = Depends(get_db),
) -> CourseResponse:
    """
    Fetch a single course by its primary key.

    Raises **404 Not Found** if no course with that ID exists.
    """
    course = crud.get_course_by_id(db=db, course_id=course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    return course


# ---------------------------------------------------------------------------
# PUT /courses/{course_id}  — Update a course
# ---------------------------------------------------------------------------
@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a course by ID",
)
def update_course(
    payload: CourseUpdate,
    course_id: int = Path(..., gt=0, description="Primary key of the course"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> CourseResponse:
    """
    Update a course's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a course by toggling **is_active**.

    Raises **404 Not Found** if no course with that ID exists, or if semester_id
    does not reference an existing semester.
    Raises **409 Conflict** if the new name/code is already used within the target semester.
    """
    course = crud.update_course(db=db, course_id=course_id, payload=payload)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    return course


# ---------------------------------------------------------------------------
# DELETE /courses/{course_id}  — Delete a course
# ---------------------------------------------------------------------------
@router.delete(
    "/{course_id}",
    response_model=CourseDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a course by ID",
)
def delete_course(
    course_id: int = Path(..., gt=0, description="Primary key of the course"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> CourseDeleteResponse:
    """
    Permanently remove a course record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no course with that ID exists.
    Returns a success message on deletion.
    """
    course = crud.delete_course(db=db, course_id=course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    return CourseDeleteResponse(
        message=f"Course with ID {course_id} deleted successfully."
    )
