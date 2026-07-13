from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dashboard.schemas.academic import AcademicAnalyticsResponse
from app.models.academic_session import AcademicSession
from app.models.course import Course
from app.models.department import Department
from app.models.program import Program
from app.models.section import Section
from app.models.semester import Semester
from app.models.subject import Subject


def get_academic_analytics(db: Session) -> AcademicAnalyticsResponse:
    """
    Structural counts across the academic setup modules (Department, Program,
    Semester, Course, Subject, Section, Academic Session).
    """
    total_departments = db.query(func.count(Department.id)).scalar() or 0
    total_programs = db.query(func.count(Program.id)).scalar() or 0
    total_semesters = db.query(func.count(Semester.id)).scalar() or 0
    total_courses = db.query(func.count(Course.id)).scalar() or 0
    total_subjects = db.query(func.count(Subject.id)).scalar() or 0
    total_sections = db.query(func.count(Section.id)).scalar() or 0
    total_academic_sessions = db.query(func.count(AcademicSession.id)).scalar() or 0

    current_session = (
        db.query(AcademicSession).filter(AcademicSession.is_current.is_(True)).first()
    )
    current_academic_session = current_session.session_name if current_session else None

    return AcademicAnalyticsResponse(
        total_departments=total_departments,
        total_programs=total_programs,
        total_semesters=total_semesters,
        total_courses=total_courses,
        total_subjects=total_subjects,
        total_sections=total_sections,
        total_academic_sessions=total_academic_sessions,
        current_academic_session=current_academic_session,
    )
