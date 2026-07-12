from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FeePayment(Base):
    __tablename__ = "fee_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    fee_structure_id: Mapped[int] = mapped_column(ForeignKey("fee_structures.id"), index=True)

    amount_paid: Mapped[float] = mapped_column(Float, default=0)

    payment_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
