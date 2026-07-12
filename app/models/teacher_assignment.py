from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), index=True)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)

    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), index=True)

    academic_session_id: Mapped[int] = mapped_column(ForeignKey("academic_sessions.id"), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
