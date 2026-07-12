from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExamMark(Base):
    __tablename__ = "exam_marks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    examination_id: Mapped[int] = mapped_column(ForeignKey("examinations.id"), index=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), index=True)

    marks_obtained: Mapped[float] = mapped_column(Float)

    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
