from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dashboard.schemas.summary import DashboardSummaryResponse
from app.models.enrollment import Enrollment
from app.models.examination import Examination
from app.models.fee_structure import FeeStructure
from app.models.student import Student
from app.models.teacher import Teacher


def get_summary(db: Session) -> DashboardSummaryResponse:
    """
    Top-line counts drawn directly from existing modules — no derived or
    invented figures.
    """
    total_students = db.query(func.count(Student.id)).scalar() or 0
    total_teachers = db.query(func.count(Teacher.id)).scalar() or 0
    total_active_enrollments = (
        db.query(func.count(Enrollment.id)).filter(Enrollment.status == "active").scalar() or 0
    )
    total_examinations = db.query(func.count(Examination.id)).scalar() or 0
    total_fee_structures = db.query(func.count(FeeStructure.id)).scalar() or 0

    return DashboardSummaryResponse(
        total_students=total_students,
        total_teachers=total_teachers,
        total_active_enrollments=total_active_enrollments,
        total_examinations=total_examinations,
        total_fee_structures=total_fee_structures,
        generated_at=datetime.now(timezone.utc),
    )
