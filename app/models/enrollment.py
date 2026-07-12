from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    academic_session_id: Mapped[int] = mapped_column(ForeignKey("academic_sessions.id"), index=True)

    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)

    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), index=True)

    enrollment_date: Mapped[Date] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(20), default="active")

    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
