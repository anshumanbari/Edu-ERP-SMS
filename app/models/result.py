from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    academic_session_id: Mapped[int] = mapped_column(ForeignKey("academic_sessions.id"), index=True)

    total_marks_obtained: Mapped[float] = mapped_column(Float)

    total_max_marks: Mapped[float] = mapped_column(Float)

    percentage: Mapped[float] = mapped_column(Float)

    status: Mapped[str] = mapped_column(String(10))

    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
