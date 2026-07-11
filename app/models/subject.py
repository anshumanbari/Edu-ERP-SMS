from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100))

    code: Mapped[str] = mapped_column(String(20))

    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
