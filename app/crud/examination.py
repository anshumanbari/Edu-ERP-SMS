from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.examination import Examination
from app.models.subject import Subject
from app.schemas.examination import ExaminationCreate, ExaminationUpdate


def _check_references_exist(db: Session, subject_id: int, academic_session_id: int) -> None:
    if db.query(Subject).filter(Subject.id == subject_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    if db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )


def _check_duplicate(
    db: Session,
    subject_id: int,
    academic_session_id: int,
    name: str,
    exclude_id: int | None = None,
) -> None:
    """
    Examination name only needs to be unique within the same subject+academic
    session — the same exam name (e.g. "Midterm") is expected to repeat across
    different subjects/sessions.
    """
    query = db.query(Examination).filter(
        Examination.subject_id == subject_id,
        Examination.academic_session_id == academic_session_id,
        Examination.name == name,
    )
    if exclude_id is not None:
        query = query.filter(Examination.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An examination named '{name}' already exists for this subject and academic session."
            ),
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_examination(db: Session, payload: ExaminationCreate) -> Examination:
    """
    Insert a new examination record into the database.

    Raises:
        HTTPException 404: If subject_id or academic_session_id does not
                            reference an existing record.
        HTTPException 409: If the name is already used within the same
                            subject and academic session.

    Returns:
        The newly created Examination ORM instance.
    """
    _check_references_exist(db, subject_id=payload.subject_id, academic_session_id=payload.academic_session_id)
    _check_duplicate(
        db,
        subject_id=payload.subject_id,
        academic_session_id=payload.academic_session_id,
        name=payload.name,
    )

    examination = Examination(
        name=payload.name,
        subject_id=payload.subject_id,
        academic_session_id=payload.academic_session_id,
        exam_date=payload.exam_date,
        max_marks=payload.max_marks,
        passing_marks=payload.passing_marks,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(examination)
    db.commit()
    db.refresh(examination)
    return examination


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_examinations(db: Session) -> list[Examination]:
    return db.query(Examination).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_examinations(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    subject_id: int | None = None,
    academic_session_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Examination], int]:
    """
    Retrieve a page of examinations along with the total record count.

    Args:
        db:                  Active SQLAlchemy session (injected via Depends).
        page:                1-indexed page number.
        limit:               Maximum number of records to return for the page.
        search:              Optional case-insensitive substring to match against
                             name or description.
        subject_id:          Optional exact subject_id to filter by.
        academic_session_id: Optional exact academic_session_id to filter by.
        is_active:           Optional exact is_active flag to filter by.
        sort_by:             Optional field to sort by (id, name, exam_date).
        sort_order:          "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (examinations on the requested page, total number of records).
    """
    query = db.query(Examination)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Examination.name.ilike(pattern),
                cast(Examination.description, String).ilike(pattern),
            )
        )

    if subject_id is not None:
        query = query.filter(Examination.subject_id == subject_id)

    if academic_session_id is not None:
        query = query.filter(Examination.academic_session_id == academic_session_id)

    if is_active is not None:
        query = query.filter(Examination.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Examination, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    examinations = query.offset(offset).limit(limit).all()
    return examinations, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_examination_by_id(db: Session, examination_id: int) -> Examination | None:
    return db.query(Examination).filter(Examination.id == examination_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_examination(db: Session, examination_id: int, payload: ExaminationUpdate) -> Examination | None:
    examination = get_examination_by_id(db, examination_id)
    if examination is None:
        return None

    references_changed = (
        payload.subject_id != examination.subject_id
        or payload.academic_session_id != examination.academic_session_id
    )
    if references_changed:
        _check_references_exist(
            db, subject_id=payload.subject_id, academic_session_id=payload.academic_session_id
        )

    if references_changed or payload.name != examination.name:
        _check_duplicate(
            db,
            subject_id=payload.subject_id,
            academic_session_id=payload.academic_session_id,
            name=payload.name,
            exclude_id=examination_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(examination, field, value)

    db.commit()
    db.refresh(examination)
    return examination


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_examination(db: Session, examination_id: int) -> Examination | None:
    examination = get_examination_by_id(db, examination_id)
    if examination is None:
        return None

    db.delete(examination)
    db.commit()
    return examination
