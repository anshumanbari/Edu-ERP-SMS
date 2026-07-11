from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)

    academic_session_id: Mapped[int] = mapped_column(ForeignKey("academic_sessions.id"), index=True)

    attendance_date: Mapped[Date] = mapped_column(Date, index=True)

    status: Mapped[str] = mapped_column(String(20))

    marked_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
