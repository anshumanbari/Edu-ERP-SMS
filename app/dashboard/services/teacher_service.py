from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dashboard.schemas.teachers import TeacherAnalyticsResponse
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment


def get_teacher_analytics(db: Session) -> TeacherAnalyticsResponse:
    """
    Teacher counts from the Teacher module, plus active-assignment coverage
    from the Teacher Assignment module.
    """
    total_teachers = db.query(func.count(Teacher.id)).scalar() or 0

    total_active_assignments = (
        db.query(func.count(TeacherAssignment.id))
        .filter(TeacherAssignment.is_active.is_(True))
        .scalar()
        or 0
    )

    distinct_assigned_teachers = (
        db.query(func.count(func.distinct(TeacherAssignment.teacher_id)))
        .filter(TeacherAssignment.is_active.is_(True))
        .scalar()
        or 0
    )

    return TeacherAnalyticsResponse(
        total_teachers=total_teachers,
        total_active_assignments=total_active_assignments,
        distinct_assigned_teachers=distinct_assigned_teachers,
    )
