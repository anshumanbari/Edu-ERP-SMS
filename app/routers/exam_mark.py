import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.exam_mark import (
    ExamMarkCreate,
    ExamMarkUpdate,
    ExamMarkResponse,
    ExamMarkDeleteResponse,
    PaginatedExamMarkResponse,
)
from app.crud import exam_mark as crud

router = APIRouter(
    prefix="/exam-marks",
    tags=["Exam Marks"],
)


# ---------------------------------------------------------------------------
# POST /exam-marks/  — Record a student's mark for an examination
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ExamMarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a student's mark for an examination",
)
def create_exam_mark(
    payload: ExamMarkCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> ExamMarkResponse:
    """
    Record a student's mark for an examination. Requires the **admin** or
    **teacher** role.

    - **examination_id**, **student_id**, **teacher_id**: Must reference existing records.
    - **teacher_id** must be actively assigned (via the Teacher Assignment module) to the
      examination's subject for its academic session — teachers may only enter marks
      for subjects they are assigned to.
    - **marks_obtained**: Must not exceed the examination's max_marks.
    - **remarks**: Optional free-text notes.

    Raises **404 Not Found** if any referenced record does not exist.
    Raises **403 Forbidden** if teacher_id is not assigned to the examination's subject.
    Raises **400 Bad Request** if marks_obtained exceeds max_marks.
    Raises **409 Conflict** if the student already has a mark recorded for this examination.
    """
    return crud.create_exam_mark(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /exam-marks/  — Retrieve exam marks (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedExamMarkResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve exam marks (paginated)",
)
def get_all_exam_marks(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(None, max_length=100, description="Search term matched against remarks"),
    examination_id: int | None = Query(None, gt=0, description="Filter by exact examination_id"),
    student_id: int | None = Query(None, gt=0, description="Filter by exact student_id"),
    teacher_id: int | None = Query(None, gt=0, description="Filter by exact teacher_id"),
    sort_by: Literal["id", "marks_obtained"] | None = Query(None, description="Field to sort by"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> PaginatedExamMarkResponse:
    """
    Return a paginated list of exam marks. Requires the **admin** or **teacher** role.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against remarks.
    - **examination_id** / **student_id** / **teacher_id**: Optional exact filters.
    - **sort_by**: Optional field to sort by (id, marks_obtained).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    exam_marks, total_records = crud.get_paginated_exam_marks(
        db=db,
        page=page,
        limit=limit,
        search=search,
        examination_id=examination_id,
        student_id=student_id,
        teacher_id=teacher_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedExamMarkResponse(
        exam_marks=exam_marks,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /exam-marks/{exam_mark_id}  — Retrieve a single exam mark
# ---------------------------------------------------------------------------
@router.get(
    "/{exam_mark_id}",
    response_model=ExamMarkResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an exam mark by ID",
)
def get_exam_mark(
    exam_mark_id: int = Path(..., gt=0, description="Primary key of the exam mark"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> ExamMarkResponse:
    """
    Fetch a single exam mark by its primary key. Requires the **admin** or **teacher** role.

    Raises **404 Not Found** if no exam mark with that ID exists.
    """
    exam_mark = crud.get_exam_mark_by_id(db=db, exam_mark_id=exam_mark_id)
    if exam_mark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam mark with ID {exam_mark_id} not found.",
        )
    return exam_mark


# ---------------------------------------------------------------------------
# PUT /exam-marks/{exam_mark_id}  — Update an exam mark
# ---------------------------------------------------------------------------
@router.put(
    "/{exam_mark_id}",
    response_model=ExamMarkResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an exam mark by ID",
)
def update_exam_mark(
    payload: ExamMarkUpdate,
    exam_mark_id: int = Path(..., gt=0, description="Primary key of the exam mark"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN, Role.TEACHER)),
) -> ExamMarkResponse:
    """
    Update an exam mark by its primary key. Requires the **admin** or **teacher** role.

    Raises **404 Not Found** if no exam mark with that ID exists, or if any
    referenced record does not exist.
    Raises **403 Forbidden** if teacher_id is not assigned to the examination's subject.
    Raises **400 Bad Request** if marks_obtained exceeds max_marks.
    Raises **409 Conflict** if the change collides with an existing mark for the same student+examination.
    """
    exam_mark = crud.update_exam_mark(db=db, exam_mark_id=exam_mark_id, payload=payload)
    if exam_mark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam mark with ID {exam_mark_id} not found.",
        )
    return exam_mark


# ---------------------------------------------------------------------------
# DELETE /exam-marks/{exam_mark_id}  — Delete an exam mark
# ---------------------------------------------------------------------------
@router.delete(
    "/{exam_mark_id}",
    response_model=ExamMarkDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an exam mark by ID",
)
def delete_exam_mark(
    exam_mark_id: int = Path(..., gt=0, description="Primary key of the exam mark"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ExamMarkDeleteResponse:
    """
    Permanently remove an exam mark record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no exam mark with that ID exists.
    Returns a success message on deletion.
    """
    exam_mark = crud.delete_exam_mark(db=db, exam_mark_id=exam_mark_id)
    if exam_mark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam mark with ID {exam_mark_id} not found.",
        )
    return ExamMarkDeleteResponse(
        message=f"Exam mark with ID {exam_mark_id} deleted successfully."
    )
