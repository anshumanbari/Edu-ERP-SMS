from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), unique=True)

    code: Mapped[str] = mapped_column(String(20), unique=True)

    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
