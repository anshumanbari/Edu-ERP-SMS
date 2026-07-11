from sqlalchemy import String, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(String(100), unique=True)

    phone: Mapped[int] = mapped_column(BigInteger)

    course: Mapped[str] = mapped_column(String(100))

    semester: Mapped[int] = mapped_column(Integer)