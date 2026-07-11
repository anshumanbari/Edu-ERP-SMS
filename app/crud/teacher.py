from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_teacher(db: Session, payload: TeacherCreate) -> Teacher:
    """
    Insert a new teacher record into the database.

    Args:
        db:      Active SQLAlchemy session (injected via Depends).
        payload: Validated TeacherCreate schema.

    Raises:
        HTTPException 409: If the email address is already registered.

    Returns:
        The newly created Teacher ORM instance.
    """
    if db.query(Teacher).filter(Teacher.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A teacher with email '{payload.email}' is already registered.",
        )

    teacher = Teacher(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        subject=payload.subject,
        experience_years=payload.experience_years,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_teachers(db: Session) -> list[Teacher]:
    """
    Retrieve all teachers from the database.

    Args:
        db: Active SQLAlchemy session (injected via Depends).

    Returns:
        A list of all Teacher ORM instances.
    """
    return db.query(Teacher).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_teachers(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    subject: str | None = None,
    experience_years: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Teacher], int]:
    """
    Retrieve a page of teachers along with the total record count.

    Args:
        db:                Active SQLAlchemy session (injected via Depends).
        page:              1-indexed page number.
        limit:             Maximum number of records to return for the page.
        search:            Optional case-insensitive substring to match against
                           name, email, or phone.
        subject:           Optional exact subject to filter by.
        experience_years:  Optional exact experience_years to filter by.
        sort_by:           Optional field to sort by (id, name, experience_years).
        sort_order:        "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (teachers on the requested page, total number of records).
    """
    query = db.query(Teacher)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Teacher.name.ilike(pattern),
                Teacher.email.ilike(pattern),
                cast(Teacher.phone, String).ilike(pattern),
            )
        )

    if subject:
        query = query.filter(Teacher.subject == subject)

    if experience_years is not None:
        query = query.filter(Teacher.experience_years == experience_years)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Teacher, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    teachers = query.offset(offset).limit(limit).all()
    return teachers, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_teacher_by_id(db: Session, teacher_id: int) -> Teacher | None:
    """
    Fetch a single teacher by primary key.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        teacher_id: Primary key of the teacher to retrieve.

    Returns:
        The matching Teacher ORM instance, or None if not found.
    """
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_teacher(
    db: Session,
    teacher_id: int,
    payload: TeacherUpdate,
) -> Teacher | None:
    """
    Update an existing teacher's fields.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        teacher_id: Primary key of the teacher to update.
        payload:    Validated TeacherUpdate schema with new values.

    Returns:
        The updated Teacher ORM instance, or None if not found.
    """
    teacher = get_teacher_by_id(db, teacher_id)
    if teacher is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(teacher, field, value)

    db.commit()
    db.refresh(teacher)
    return teacher


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_teacher(db: Session, teacher_id: int) -> Teacher | None:
    """
    Delete a teacher record by primary key.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        teacher_id: Primary key of the teacher to delete.

    Returns:
        The deleted Teacher ORM instance, or None if not found.
    """
    teacher = get_teacher_by_id(db, teacher_id)
    if teacher is None:
        return None

    db.delete(teacher)
    db.commit()
    return teacher
