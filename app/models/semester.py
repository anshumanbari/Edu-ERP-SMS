from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100))

    code: Mapped[str] = mapped_column(String(20))

    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)

    sequence_number: Mapped[int] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
