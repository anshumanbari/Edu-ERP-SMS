from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AcademicSession(Base):
    __tablename__ = "academic_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    session_name: Mapped[str] = mapped_column(String(50), unique=True)

    start_date: Mapped[Date] = mapped_column(Date)

    end_date: Mapped[Date] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(20), default="upcoming")

    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
