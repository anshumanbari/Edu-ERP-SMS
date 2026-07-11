import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDeleteResponse,
    PaginatedStudentResponse,
)
from app.crud import student as crud

router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


# ---------------------------------------------------------------------------
# POST /students/  — Create a new student
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student",
)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> StudentResponse:
    """
    Create a student record. Requires the **admin** or **teacher** role.

    - **name**: Full name of the student.
    - **email**: Unique email address — must not already exist.
    - **phone**: Contact phone number.
    - **course**: Enrolled course or program name.
    - **semester**: Current semester number (1–8).

    Raises **409 Conflict** if the email is already registered.
    """
    return crud.create_student(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /students/  — Retrieve all students (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedStudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all students (paginated)",
)
def get_all_students(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, email, or phone"
    ),
    course: str | None = Query(None, max_length=100, description="Filter by exact course"),
    semester: int | None = Query(None, ge=1, le=8, description="Filter by exact semester"),
    sort_by: Literal["id", "name", "semester"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedStudentResponse:
    """
    Return a paginated list of registered students.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, email, or phone.
    - **course**: Optional exact course filter.
    - **semester**: Optional exact semester filter.
    - **sort_by**: Optional field to sort by (id, name, semester).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    students, total_records = crud.get_paginated_students(
        db=db,
        page=page,
        limit=limit,
        search=search,
        course=course,
        semester=semester,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedStudentResponse(
        students=students,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /students/{student_id}  — Retrieve a single student
# ---------------------------------------------------------------------------
@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a student by ID",
)
def get_student(
    student_id: int = Path(..., gt=0, description="Primary key of the student"),
    db: Session = Depends(get_db),
) -> StudentResponse:
    """
    Fetch a single student by their primary key.

    Raises **404 Not Found** if no student with that ID exists.
    """
    student = crud.get_student_by_id(db=db, student_id=student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    return student


# ---------------------------------------------------------------------------
# PUT /students/{student_id}  — Update a student
# ---------------------------------------------------------------------------
@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a student by ID",
)
def update_student(
    payload: StudentUpdate,
    student_id: int = Path(..., gt=0, description="Primary key of the student"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> StudentResponse:
    """
    Update a student's details by their primary key. Requires the **admin** or **teacher** role.

    Raises **404 Not Found** if no student with that ID exists.
    """
    student = crud.update_student(db=db, student_id=student_id, payload=payload)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    return student


# ---------------------------------------------------------------------------
# DELETE /students/{student_id}  — Delete a student
# ---------------------------------------------------------------------------
@router.delete(
    "/{student_id}",
    response_model=StudentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a student by ID",
)
def delete_student(
    student_id: int = Path(..., gt=0, description="Primary key of the student"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> StudentDeleteResponse:
    """
    Permanently remove a student record by their primary key. Requires the **admin** role.

    Raises **404 Not Found** if no student with that ID exists.
    Returns a success message on deletion.
    """
    student = crud.delete_student(db=db, student_id=student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    return StudentDeleteResponse(
        message=f"Student with ID {student_id} deleted successfully."
    )
