from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100))

    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)

    academic_session_id: Mapped[int] = mapped_column(ForeignKey("academic_sessions.id"), index=True)

    amount: Mapped[float] = mapped_column(Float)

    due_date: Mapped[Date] = mapped_column(Date)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
