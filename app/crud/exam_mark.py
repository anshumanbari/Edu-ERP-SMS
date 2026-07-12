from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.exam_mark import ExamMark
from app.models.examination import Examination
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.schemas.exam_mark import ExamMarkCreate, ExamMarkUpdate


def _get_examination_or_404(db: Session, examination_id: int) -> Examination:
    examination = db.query(Examination).filter(Examination.id == examination_id).first()
    if examination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Examination with ID {examination_id} not found.",
        )
    return examination


def _check_references_exist(
    db: Session, student_id: int, teacher_id: int
) -> None:
    if db.query(Student).filter(Student.id == student_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    if db.query(Teacher).filter(Teacher.id == teacher_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found.",
        )


def _check_teacher_assigned(db: Session, teacher_id: int, examination: Examination) -> None:
    """
    Teachers may only enter marks for subjects they are actively assigned to
    (per the Teacher Assignment module), scoped to the examination's academic session.
    """
    assignment = (
        db.query(TeacherAssignment)
        .filter(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.subject_id == examination.subject_id,
            TeacherAssignment.academic_session_id == examination.academic_session_id,
            TeacherAssignment.is_active.is_(True),
        )
        .first()
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Teacher {teacher_id} is not assigned to subject {examination.subject_id} "
                f"for academic session {examination.academic_session_id}."
            ),
        )


def _check_marks_within_range(marks_obtained: float, examination: Examination) -> None:
    if marks_obtained > examination.max_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"marks_obtained ({marks_obtained}) cannot exceed max_marks ({examination.max_marks}).",
        )


def _check_duplicate(
    db: Session,
    examination_id: int,
    student_id: int,
    exclude_id: int | None = None,
) -> None:
    """
    A student can only have one mark entry per examination.
    """
    query = db.query(ExamMark).filter(
        ExamMark.examination_id == examination_id,
        ExamMark.student_id == student_id,
    )
    if exclude_id is not None:
        query = query.filter(ExamMark.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student {student_id} already has a mark recorded for examination {examination_id}.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_exam_mark(db: Session, payload: ExamMarkCreate) -> ExamMark:
    """
    Insert a new exam mark record into the database.

    Raises:
        HTTPException 404: If examination_id, student_id, or teacher_id does not
                            reference an existing record.
        HTTPException 403: If teacher_id is not actively assigned to the
                            examination's subject for its academic session.
        HTTPException 400: If marks_obtained exceeds the examination's max_marks.
        HTTPException 409: If the student already has a mark recorded for this examination.

    Returns:
        The newly created ExamMark ORM instance.
    """
    examination = _get_examination_or_404(db, payload.examination_id)
    _check_references_exist(db, student_id=payload.student_id, teacher_id=payload.teacher_id)
    _check_teacher_assigned(db, teacher_id=payload.teacher_id, examination=examination)
    _check_marks_within_range(payload.marks_obtained, examination)
    _check_duplicate(db, examination_id=payload.examination_id, student_id=payload.student_id)

    exam_mark = ExamMark(
        examination_id=payload.examination_id,
        student_id=payload.student_id,
        teacher_id=payload.teacher_id,
        marks_obtained=payload.marks_obtained,
        remarks=payload.remarks,
    )
    db.add(exam_mark)
    db.commit()
    db.refresh(exam_mark)
    return exam_mark


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_exam_marks(db: Session) -> list[ExamMark]:
    return db.query(ExamMark).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_exam_marks(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    examination_id: int | None = None,
    student_id: int | None = None,
    teacher_id: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[ExamMark], int]:
    """
    Retrieve a page of exam marks along with the total record count.

    Args:
        db:             Active SQLAlchemy session (injected via Depends).
        page:           1-indexed page number.
        limit:          Maximum number of records to return for the page.
        search:         Optional case-insensitive substring to match against remarks.
        examination_id: Optional exact examination_id to filter by.
        student_id:     Optional exact student_id to filter by.
        teacher_id:     Optional exact teacher_id to filter by.
        sort_by:        Optional field to sort by (id, marks_obtained).
        sort_order:     "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (exam marks on the requested page, total number of records).
    """
    query = db.query(ExamMark)

    if search:
        pattern = f"%{search}%"
        query = query.filter(ExamMark.remarks.ilike(pattern))

    if examination_id is not None:
        query = query.filter(ExamMark.examination_id == examination_id)

    if student_id is not None:
        query = query.filter(ExamMark.student_id == student_id)

    if teacher_id is not None:
        query = query.filter(ExamMark.teacher_id == teacher_id)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(ExamMark, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    exam_marks = query.offset(offset).limit(limit).all()
    return exam_marks, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_exam_mark_by_id(db: Session, exam_mark_id: int) -> ExamMark | None:
    return db.query(ExamMark).filter(ExamMark.id == exam_mark_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_exam_mark(db: Session, exam_mark_id: int, payload: ExamMarkUpdate) -> ExamMark | None:
    exam_mark = get_exam_mark_by_id(db, exam_mark_id)
    if exam_mark is None:
        return None

    examination = _get_examination_or_404(db, payload.examination_id)

    references_changed = (
        payload.examination_id != exam_mark.examination_id
        or payload.student_id != exam_mark.student_id
        or payload.teacher_id != exam_mark.teacher_id
    )
    if references_changed:
        _check_references_exist(db, student_id=payload.student_id, teacher_id=payload.teacher_id)

    if payload.teacher_id != exam_mark.teacher_id or payload.examination_id != exam_mark.examination_id:
        _check_teacher_assigned(db, teacher_id=payload.teacher_id, examination=examination)

    _check_marks_within_range(payload.marks_obtained, examination)

    if payload.examination_id != exam_mark.examination_id or payload.student_id != exam_mark.student_id:
        _check_duplicate(
            db,
            examination_id=payload.examination_id,
            student_id=payload.student_id,
            exclude_id=exam_mark_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exam_mark, field, value)

    db.commit()
    db.refresh(exam_mark)
    return exam_mark


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_exam_mark(db: Session, exam_mark_id: int) -> ExamMark | None:
    exam_mark = get_exam_mark_by_id(db, exam_mark_id)
    if exam_mark is None:
        return None

    db.delete(exam_mark)
    db.commit()
    return exam_mark
