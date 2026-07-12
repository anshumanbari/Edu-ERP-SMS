from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate


def _check_duplicate(
    db: Session,
    room_number: str,
    building: str | None,
    exclude_id: int | None = None,
) -> None:
    """
    Room number only needs to be unique within the same building — the same
    room number is expected to repeat across different buildings.
    """
    query = db.query(Classroom).filter(
        Classroom.room_number == room_number,
        Classroom.building == building,
    )
    if exclude_id is not None:
        query = query.filter(Classroom.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A classroom with room number '{room_number}' already exists in this building.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_classroom(db: Session, payload: ClassroomCreate) -> Classroom:
    """
    Insert a new classroom record into the database.

    Raises:
        HTTPException 409: If the room_number is already used within the same building.

    Returns:
        The newly created Classroom ORM instance.
    """
    _check_duplicate(db, room_number=payload.room_number, building=payload.building)

    classroom = Classroom(
        room_number=payload.room_number,
        building=payload.building,
        capacity=payload.capacity,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_classrooms(db: Session) -> list[Classroom]:
    return db.query(Classroom).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_classrooms(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Classroom], int]:
    """
    Retrieve a page of classrooms along with the total record count.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        page:       1-indexed page number.
        limit:      Maximum number of records to return for the page.
        search:     Optional case-insensitive substring to match against
                    room_number, building, or description.
        is_active:  Optional exact is_active flag to filter by.
        sort_by:    Optional field to sort by (id, room_number, capacity).
        sort_order: "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (classrooms on the requested page, total number of records).
    """
    query = db.query(Classroom)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Classroom.room_number.ilike(pattern),
                cast(Classroom.building, String).ilike(pattern),
                cast(Classroom.description, String).ilike(pattern),
            )
        )

    if is_active is not None:
        query = query.filter(Classroom.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Classroom, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    classrooms = query.offset(offset).limit(limit).all()
    return classrooms, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_classroom_by_id(db: Session, classroom_id: int) -> Classroom | None:
    return db.query(Classroom).filter(Classroom.id == classroom_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_classroom(db: Session, classroom_id: int, payload: ClassroomUpdate) -> Classroom | None:
    classroom = get_classroom_by_id(db, classroom_id)
    if classroom is None:
        return None

    if payload.room_number != classroom.room_number or payload.building != classroom.building:
        _check_duplicate(
            db,
            room_number=payload.room_number,
            building=payload.building,
            exclude_id=classroom_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(classroom, field, value)

    db.commit()
    db.refresh(classroom)
    return classroom


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_classroom(db: Session, classroom_id: int) -> Classroom | None:
    classroom = get_classroom_by_id(db, classroom_id)
    if classroom is None:
        return None

    db.delete(classroom)
    db.commit()
    return classroom
