from sqlalchemy import Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.roles import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    hashed_password: Mapped[str] = mapped_column(String(255))

    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="user_role", native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=Role.STUDENT,
        server_default=Role.STUDENT.value,
        nullable=False,
    )
