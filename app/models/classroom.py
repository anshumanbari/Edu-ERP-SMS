from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    room_number: Mapped[str] = mapped_column(String(20))

    building: Mapped[str | None] = mapped_column(String(100), nullable=True)

    capacity: Mapped[int] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
