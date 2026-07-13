from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dashboard.schemas.students import (
    CourseCount,
    SemesterCount,
    EnrollmentStatusCount,
    StudentAnalyticsResponse,
)
from app.models.enrollment import Enrollment
from app.models.student import Student


def get_student_analytics(db: Session) -> StudentAnalyticsResponse:
    """
    Student counts from the Student module, plus enrollment status breakdown
    from the Enrollment module. Groupings return an empty list rather than
    fabricated categories when there is no data yet.
    """
    total_students = db.query(func.count(Student.id)).scalar() or 0

    course_rows = (
        db.query(Student.course, func.count(Student.id)).group_by(Student.course).all()
    )
    students_by_course = [CourseCount(course=course, count=count) for course, count in course_rows]

    semester_rows = (
        db.query(Student.semester, func.count(Student.id)).group_by(Student.semester).all()
    )
    students_by_semester = [
        SemesterCount(semester=semester, count=count) for semester, count in semester_rows
    ]

    total_enrollments = db.query(func.count(Enrollment.id)).scalar() or 0
    status_rows = (
        db.query(Enrollment.status, func.count(Enrollment.id)).group_by(Enrollment.status).all()
    )
    enrollments_by_status = [
        EnrollmentStatusCount(status=status, count=count) for status, count in status_rows
    ]

    return StudentAnalyticsResponse(
        total_students=total_students,
        students_by_course=students_by_course,
        students_by_semester=students_by_semester,
        total_enrollments=total_enrollments,
        enrollments_by_status=enrollments_by_status,
    )
