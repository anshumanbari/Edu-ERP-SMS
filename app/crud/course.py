from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.semester import Semester
from app.schemas.course import CourseCreate, CourseUpdate


def _check_duplicate(
    db: Session,
    semester_id: int,
    name: str,
    code: str,
    exclude_id: int | None = None,
) -> None:
    """
    Course name/code only need to be unique within the same semester — the
    same course name is expected to repeat across different semesters/programs.
    """
    query = db.query(Course).filter(
        Course.semester_id == semester_id,
        or_(Course.name == name, Course.code == code),
    )
    if exclude_id is not None:
        query = query.filter(Course.id != exclude_id)

    existing = query.first()
    if existing is not None:
        field = "name" if existing.name == name else "code"
        value = name if field == "name" else code
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A course with {field} '{value}' already exists for this semester.",
        )


def _check_semester_exists(db: Session, semester_id: int) -> None:
    if db.query(Semester).filter(Semester.id == semester_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_course(db: Session, payload: CourseCreate) -> Course:
    """
    Insert a new course record into the database.

    Raises:
        HTTPException 404: If semester_id does not reference an existing semester.
        HTTPException 409: If the name or code is already used within the same semester.

    Returns:
        The newly created Course ORM instance.
    """
    _check_semester_exists(db, payload.semester_id)
    _check_duplicate(db, semester_id=payload.semester_id, name=payload.name, code=payload.code)

    course = Course(
        name=payload.name,
        code=payload.code,
        semester_id=payload.semester_id,
        credit_hours=payload.credit_hours,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_courses(db: Session) -> list[Course]:
    return db.query(Course).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_courses(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    semester_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Course], int]:
    """
    Retrieve a page of courses along with the total record count.

    Args:
        db:          Active SQLAlchemy session (injected via Depends).
        page:        1-indexed page number.
        limit:       Maximum number of records to return for the page.
        search:      Optional case-insensitive substring to match against
                     name, code, or description.
        semester_id: Optional exact semester_id to filter by.
        is_active:   Optional exact is_active flag to filter by.
        sort_by:     Optional field to sort by (id, name, credit_hours).
        sort_order:  "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (courses on the requested page, total number of records).
    """
    query = db.query(Course)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Course.name.ilike(pattern),
                Course.code.ilike(pattern),
                cast(Course.description, String).ilike(pattern),
            )
        )

    if semester_id is not None:
        query = query.filter(Course.semester_id == semester_id)

    if is_active is not None:
        query = query.filter(Course.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Course, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    courses = query.offset(offset).limit(limit).all()
    return courses, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_course_by_id(db: Session, course_id: int) -> Course | None:
    return db.query(Course).filter(Course.id == course_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_course(db: Session, course_id: int, payload: CourseUpdate) -> Course | None:
    course = get_course_by_id(db, course_id)
    if course is None:
        return None

    if payload.semester_id != course.semester_id:
        _check_semester_exists(db, payload.semester_id)

    if (
        payload.semester_id != course.semester_id
        or payload.name != course.name
        or payload.code != course.code
    ):
        _check_duplicate(
            db,
            semester_id=payload.semester_id,
            name=payload.name,
            code=payload.code,
            exclude_id=course_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_course(db: Session, course_id: int) -> Course | None:
    course = get_course_by_id(db, course_id)
    if course is None:
        return None

    db.delete(course)
    db.commit()
    return course
