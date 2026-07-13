from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.dashboard.schemas.academic import AcademicAnalyticsResponse
from app.dashboard.schemas.attendance import AttendanceAnalyticsResponse
from app.dashboard.schemas.examination import ExaminationAnalyticsResponse
from app.dashboard.schemas.fees import FeesAnalyticsResponse
from app.dashboard.schemas.students import StudentAnalyticsResponse
from app.dashboard.schemas.summary import DashboardSummaryResponse
from app.dashboard.schemas.system import SystemAnalyticsResponse
from app.dashboard.schemas.teachers import TeacherAnalyticsResponse
from app.dashboard.services import (
    academic_service,
    attendance_service,
    examination_service,
    fees_service,
    student_service,
    summary_service,
    system_service,
    teacher_service,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.TEACHER))],
)


# ---------------------------------------------------------------------------
# GET /dashboard/summary  — Top-line counts across modules
# ---------------------------------------------------------------------------
@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Retrieve top-line summary analytics",
)
def get_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    """
    Top-line counts across Students, Teachers, Enrollments, Examinations, and
    Fee Structures. Requires the **admin** or **teacher** role.
    """
    return summary_service.get_summary(db)


# ---------------------------------------------------------------------------
# GET /dashboard/students  — Student analytics
# ---------------------------------------------------------------------------
@router.get(
    "/students",
    response_model=StudentAnalyticsResponse,
    summary="Retrieve student analytics",
)
def get_student_analytics(db: Session = Depends(get_db)) -> StudentAnalyticsResponse:
    """
    Student counts and enrollment status breakdown. Requires the **admin** or
    **teacher** role.
    """
    return student_service.get_student_analytics(db)


# ---------------------------------------------------------------------------
# GET /dashboard/teachers  — Teacher analytics
# ---------------------------------------------------------------------------
@router.get(
    "/teachers",
    response_model=TeacherAnalyticsResponse,
    summary="Retrieve teacher analytics",
)
def get_teacher_analytics(db: Session = Depends(get_db)) -> TeacherAnalyticsResponse:
    """
    Teacher counts and active assignment coverage. Requires the **admin** or
    **teacher** role.
    """
    return teacher_service.get_teacher_analytics(db)


# ---------------------------------------------------------------------------
# GET /dashboard/academic  — Academic structure analytics
# ---------------------------------------------------------------------------
@router.get(
    "/academic",
    response_model=AcademicAnalyticsResponse,
    summary="Retrieve academic structure analytics",
)
def get_academic_analytics(db: Session = Depends(get_db)) -> AcademicAnalyticsResponse:
    """
    Counts of Departments, Programs, Semesters, Courses, Subjects, Sections,
    and Academic Sessions, plus the current academic session. Requires the
    **admin** or **teacher** role.
    """
    return academic_service.get_academic_analytics(db)


# ---------------------------------------------------------------------------
# GET /dashboard/attendance  — Attendance analytics
# ---------------------------------------------------------------------------
@router.get(
    "/attendance",
    response_model=AttendanceAnalyticsResponse,
    summary="Retrieve attendance analytics",
)
def get_attendance_analytics(db: Session = Depends(get_db)) -> AttendanceAnalyticsResponse:
    """
    Attendance status breakdown and overall attendance percentage. Requires
    the **admin** or **teacher** role.
    """
    return attendance_service.get_attendance_analytics(db)


# ---------------------------------------------------------------------------
# GET /dashboard/examinations  — Examination & result analytics
# ---------------------------------------------------------------------------
@router.get(
    "/examinations",
    response_model=ExaminationAnalyticsResponse,
    summary="Retrieve examination and result analytics",
)
def get_examination_analytics(db: Session = Depends(get_db)) -> ExaminationAnalyticsResponse:
    """
    Examination and exam mark volume, plus result pass/fail distribution.
    Requires the **admin** or **teacher** role.
    """
    return examination_service.get_examination_analytics(db)


# ---------------------------------------------------------------------------
# GET /dashboard/fees  — Fees analytics
# ---------------------------------------------------------------------------
@router.get(
    "/fees",
    response_model=FeesAnalyticsResponse,
    summary="Retrieve fees analytics",
)
def get_fees_analytics(db: Session = Depends(get_db)) -> FeesAnalyticsResponse:
    """
    Fee structure totals, amounts due/collected, and payment status
    (paid/pending/overdue) breakdown. Requires the **admin** or **teacher** role.
    """
    return fees_service.get_fees_analytics(db)


# ---------------------------------------------------------------------------
# GET /dashboard/system  — System analytics
# ---------------------------------------------------------------------------
@router.get(
    "/system",
    response_model=SystemAnalyticsResponse,
    summary="Retrieve system analytics",
)
def get_system_analytics(db: Session = Depends(get_db)) -> SystemAnalyticsResponse:
    """
    Registered user counts by role, and running application identity/version.
    Requires the **admin** or **teacher** role.
    """
    return system_service.get_system_analytics(db)
