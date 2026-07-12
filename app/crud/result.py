from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.exam_mark import ExamMark
from app.models.examination import Examination
from app.models.result import Result
from app.models.student import Student
from app.schemas.result import ResultGenerateRequest


def _check_references_exist(db: Session, student_id: int, academic_session_id: int) -> None:
    if db.query(Student).filter(Student.id == student_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    if db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )


def _check_duplicate(db: Session, student_id: int, academic_session_id: int) -> None:
    existing = (
        db.query(Result)
        .filter(Result.student_id == student_id, Result.academic_session_id == academic_session_id)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A result has already been generated for student {student_id} in academic "
                f"session {academic_session_id}."
            ),
        )


# ---------------------------------------------------------------------------
# GENERATE
# ---------------------------------------------------------------------------
def generate_result(db: Session, payload: ResultGenerateRequest) -> Result:
    """
    Aggregate a student's exam marks for an academic session into a Result record.

    Raises:
        HTTPException 404: If student_id or academic_session_id does not reference an
                            existing record, or if the student has no exam marks
                            recorded for the academic session.
        HTTPException 409: If a result has already been generated for this
                            student+academic session.

    Returns:
        The newly created Result ORM instance (unpublished by default).
    """
    _check_references_exist(db, student_id=payload.student_id, academic_session_id=payload.academic_session_id)
    _check_duplicate(db, student_id=payload.student_id, academic_session_id=payload.academic_session_id)

    rows = (
        db.query(ExamMark, Examination)
        .join(Examination, ExamMark.examination_id == Examination.id)
        .filter(
            ExamMark.student_id == payload.student_id,
            Examination.academic_session_id == payload.academic_session_id,
        )
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No exam marks found for student {payload.student_id} in academic "
                f"session {payload.academic_session_id}."
            ),
        )

    total_marks_obtained = sum(mark.marks_obtained for mark, _ in rows)
    total_max_marks = sum(examination.max_marks for _, examination in rows)
    percentage = (total_marks_obtained / total_max_marks * 100) if total_max_marks > 0 else 0.0
    has_failed_subject = any(
        mark.marks_obtained < examination.passing_marks for mark, examination in rows
    )
    result_status = "fail" if has_failed_subject else "pass"

    result = Result(
        student_id=payload.student_id,
        academic_session_id=payload.academic_session_id,
        total_marks_obtained=total_marks_obtained,
        total_max_marks=total_max_marks,
        percentage=percentage,
        status=result_status,
        is_published=False,
        published_at=None,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_results(db: Session) -> list[Result]:
    return db.query(Result).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_results(
    db: Session,
    page: int,
    limit: int,
    student_id: int | None = None,
    academic_session_id: int | None = None,
    status_filter: str | None = None,
    is_published: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Result], int]:
    """
    Retrieve a page of results along with the total record count.

    Args:
        db:                  Active SQLAlchemy session (injected via Depends).
        page:                1-indexed page number.
        limit:               Maximum number of records to return for the page.
        student_id:          Optional exact student_id to filter by.
        academic_session_id: Optional exact academic_session_id to filter by.
        status_filter:       Optional exact status to filter by.
        is_published:        Optional exact is_published flag to filter by.
        sort_by:             Optional field to sort by (id, percentage).
        sort_order:          "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (results on the requested page, total number of records).
    """
    query = db.query(Result)

    if student_id is not None:
        query = query.filter(Result.student_id == student_id)

    if academic_session_id is not None:
        query = query.filter(Result.academic_session_id == academic_session_id)

    if status_filter:
        query = query.filter(Result.status == status_filter)

    if is_published is not None:
        query = query.filter(Result.is_published == is_published)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Result, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()
    return results, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_result_by_id(db: Session, result_id: int) -> Result | None:
    return db.query(Result).filter(Result.id == result_id).first()


# ---------------------------------------------------------------------------
# PUBLISH
# ---------------------------------------------------------------------------
def publish_result(db: Session, result_id: int) -> Result | None:
    """
    Mark a result as published, making it visible to the student.

    Raises:
        HTTPException 409: If the result is already published.

    Returns:
        The updated Result ORM instance, or None if no result with that ID exists.
    """
    result = get_result_by_id(db, result_id)
    if result is None:
        return None

    if result.is_published:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Result with ID {result_id} is already published.",
        )

    result.is_published = True
    result.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(result)
    return result


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_result(db: Session, result_id: int) -> Result | None:
    result = get_result_by_id(db, result_id)
    if result is None:
        return None

    db.delete(result)
    db.commit()
    return result
