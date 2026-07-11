from sqlalchemy import String, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(String(100), unique=True)

    phone: Mapped[int] = mapped_column(BigInteger)

    subject: Mapped[str] = mapped_column(String(100))

    experience_years: Mapped[int] = mapped_column(Integer)
