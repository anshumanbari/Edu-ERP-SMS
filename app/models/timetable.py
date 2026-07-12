from sqlalchemy import Boolean, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Timetable(Base):
    __tablename__ = "timetables"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), index=True)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), index=True)

    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)

    academic_session_id: Mapped[int] = mapped_column(ForeignKey("academic_sessions.id"), index=True)

    day_of_week: Mapped[str] = mapped_column(String(10), index=True)

    start_time: Mapped[Time] = mapped_column(Time)

    end_time: Mapped[Time] = mapped_column(Time)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
