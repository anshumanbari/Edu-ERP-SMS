from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


def _check_duplicate(
    db: Session,
    course_id: int,
    name: str,
    code: str,
    exclude_id: int | None = None,
) -> None:
    """
    Subject name/code only need to be unique within the same course — the
    same subject label is expected to repeat across different courses.
    """
    query = db.query(Subject).filter(
        Subject.course_id == course_id,
        or_(Subject.name == name, Subject.code == code),
    )
    if exclude_id is not None:
        query = query.filter(Subject.id != exclude_id)

    existing = query.first()
    if existing is not None:
        field = "name" if existing.name == name else "code"
        value = name if field == "name" else code
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A subject with {field} '{value}' already exists for this course.",
        )


def _check_course_exists(db: Session, course_id: int) -> None:
    if db.query(Course).filter(Course.id == course_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_subject(db: Session, payload: SubjectCreate) -> Subject:
    """
    Insert a new subject record into the database.

    Raises:
        HTTPException 404: If course_id does not reference an existing course.
        HTTPException 409: If the name or code is already used within the same course.

    Returns:
        The newly created Subject ORM instance.
    """
    _check_course_exists(db, payload.course_id)
    _check_duplicate(db, course_id=payload.course_id, name=payload.name, code=payload.code)

    subject = Subject(
        name=payload.name,
        code=payload.code,
        course_id=payload.course_id,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_subjects(db: Session) -> list[Subject]:
    return db.query(Subject).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_subjects(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    course_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Subject], int]:
    """
    Retrieve a page of subjects along with the total record count.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        page:       1-indexed page number.
        limit:      Maximum number of records to return for the page.
        search:     Optional case-insensitive substring to match against
                    name, code, or description.
        course_id:  Optional exact course_id to filter by.
        is_active:  Optional exact is_active flag to filter by.
        sort_by:    Optional field to sort by (id, name, code).
        sort_order: "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (subjects on the requested page, total number of records).
    """
    query = db.query(Subject)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Subject.name.ilike(pattern),
                Subject.code.ilike(pattern),
                cast(Subject.description, String).ilike(pattern),
            )
        )

    if course_id is not None:
        query = query.filter(Subject.course_id == course_id)

    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Subject, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    subjects = query.offset(offset).limit(limit).all()
    return subjects, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_subject_by_id(db: Session, subject_id: int) -> Subject | None:
    return db.query(Subject).filter(Subject.id == subject_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_subject(db: Session, subject_id: int, payload: SubjectUpdate) -> Subject | None:
    subject = get_subject_by_id(db, subject_id)
    if subject is None:
        return None

    if payload.course_id != subject.course_id:
        _check_course_exists(db, payload.course_id)

    if (
        payload.course_id != subject.course_id
        or payload.name != subject.name
        or payload.code != subject.code
    ):
        _check_duplicate(
            db,
            course_id=payload.course_id,
            name=payload.name,
            code=payload.code,
            exclude_id=subject_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subject, field, value)

    db.commit()
    db.refresh(subject)
    return subject


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_subject(db: Session, subject_id: int) -> Subject | None:
    subject = get_subject_by_id(db, subject_id)
    if subject is None:
        return None

    db.delete(subject)
    db.commit()
    return subject
