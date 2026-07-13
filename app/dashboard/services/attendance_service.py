from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dashboard.schemas.attendance import AttendanceAnalyticsResponse, AttendanceStatusCount
from app.models.attendance import Attendance


def get_attendance_analytics(db: Session) -> AttendanceAnalyticsResponse:
    """
    Attendance status breakdown and overall present-rate, computed only from
    recorded Attendance rows. Returns a null percentage rather than a
    fabricated one when no attendance has been recorded yet.
    """
    total_records = db.query(func.count(Attendance.id)).scalar() or 0

    status_rows = (
        db.query(Attendance.status, func.count(Attendance.id)).group_by(Attendance.status).all()
    )
    attendance_by_status = [
        AttendanceStatusCount(status=status, count=count) for status, count in status_rows
    ]

    present_count = next((count for status, count in status_rows if status == "present"), 0)
    overall_attendance_percentage = (
        (present_count / total_records * 100) if total_records > 0 else None
    )

    return AttendanceAnalyticsResponse(
        total_records=total_records,
        attendance_by_status=attendance_by_status,
        overall_attendance_percentage=overall_attendance_percentage,
    )
