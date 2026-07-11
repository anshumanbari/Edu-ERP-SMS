from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(50))

    code: Mapped[str] = mapped_column(String(20))

    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
