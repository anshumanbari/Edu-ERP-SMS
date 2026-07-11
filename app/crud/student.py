from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_student(db: Session, payload: StudentCreate) -> Student:
    """
    Insert a new student record into the database.

    Args:
        db:      Active SQLAlchemy session (injected via Depends).
        payload: Validated StudentCreate schema.

    Raises:
        HTTPException 409: If the email address is already registered.

    Returns:
        The newly created Student ORM instance.
    """
    if db.query(Student).filter(Student.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A student with email '{payload.email}' is already registered.",
        )

    student = Student(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        course=payload.course,
        semester=payload.semester,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_students(db: Session) -> list[Student]:
    """
    Retrieve all students from the database.

    Args:
        db: Active SQLAlchemy session (injected via Depends).

    Returns:
        A list of all Student ORM instances.
    """
    return db.query(Student).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_students(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    course: str | None = None,
    semester: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Student], int]:
    """
    Retrieve a page of students along with the total record count.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        page:       1-indexed page number.
        limit:      Maximum number of records to return for the page.
        search:     Optional case-insensitive substring to match against
                    name, email, or phone.
        course:     Optional exact course to filter by.
        semester:   Optional exact semester to filter by.
        sort_by:    Optional field to sort by (id, name, semester).
        sort_order: "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (students on the requested page, total number of records).
    """
    query = db.query(Student)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Student.name.ilike(pattern),
                Student.email.ilike(pattern),
                cast(Student.phone, String).ilike(pattern),
            )
        )

    if course:
        query = query.filter(Student.course == course)

    if semester is not None:
        query = query.filter(Student.semester == semester)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Student, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    students = query.offset(offset).limit(limit).all()
    return students, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_student_by_id(db: Session, student_id: int) -> Student | None:
    """
    Fetch a single student by primary key.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        student_id: Primary key of the student to retrieve.

    Returns:
        The matching Student ORM instance, or None if not found.
    """
    return db.query(Student).filter(Student.id == student_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_student(
    db: Session,
    student_id: int,
    payload: StudentUpdate,
) -> Student | None:
    """
    Update an existing student's fields.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        student_id: Primary key of the student to update.
        payload:    Validated StudentUpdate schema with new values.

    Returns:
        The updated Student ORM instance, or None if not found.
    """
    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_student(db: Session, student_id: int) -> Student | None:
    """
    Delete a student record by primary key.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        student_id: Primary key of the student to delete.

    Returns:
        The deleted Student ORM instance, or None if not found.
    """
    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    db.delete(student)
    db.commit()
    return student
