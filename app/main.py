from fastapi import FastAPI

from app.core.config import settings
from app.core.database import Base, engine
from app.core.error_handlers import register_exception_handlers
from app.core.logger import setup_logging
from app.core.middleware import RequestLoggingMiddleware, StandardResponseMiddleware

# Configure application-wide logging before anything else runs
setup_logging()

# Register ORM models so SQLAlchemy can detect and create their tables
from app.models.student import Student  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.academic_session import AcademicSession  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.program import Program  # noqa: F401
from app.models.semester import Semester  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.section import Section  # noqa: F401
from app.models.enrollment import Enrollment  # noqa: F401
from app.models.teacher_assignment import TeacherAssignment  # noqa: F401
from app.models.classroom import Classroom  # noqa: F401
from app.models.timetable import Timetable  # noqa: F401
from app.models.examination import Examination  # noqa: F401
from app.models.exam_mark import ExamMark  # noqa: F401
from app.models.result import Result  # noqa: F401
from app.models.fee_structure import FeeStructure  # noqa: F401
from app.models.fee_payment import FeePayment  # noqa: F401

# Routers
from app.routers.student import router as student_router
from app.routers.teacher import router as teacher_router
from app.routers.auth import router as auth_router
from app.routers.academic_session import router as academic_session_router
from app.routers.department import router as department_router
from app.routers.program import router as program_router
from app.routers.semester import router as semester_router
from app.routers.course import router as course_router
from app.routers.subject import router as subject_router
from app.routers.attendance import router as attendance_router
from app.routers.section import router as section_router
from app.routers.enrollment import router as enrollment_router
from app.routers.teacher_assignment import router as teacher_assignment_router
from app.routers.classroom import router as classroom_router
from app.routers.timetable import router as timetable_router
from app.routers.examination import router as examination_router
from app.routers.exam_mark import router as exam_mark_router
from app.routers.result import router as result_router
from app.routers.fee_structure import router as fee_structure_router
from app.routers.fee_payment import router as fee_payment_router

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Student Management System — Backend API built with FastAPI",
)

# ---------------------------------------------------------------------------
# Register centralized exception handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Wrap successful responses in the standard API response envelope
# ---------------------------------------------------------------------------
app.add_middleware(StandardResponseMiddleware)

# ---------------------------------------------------------------------------
# Log every request's method, path, status code, and duration
# ---------------------------------------------------------------------------
app.add_middleware(RequestLoggingMiddleware)

# ---------------------------------------------------------------------------
# Task 1 — Register the students router
# ---------------------------------------------------------------------------
app.include_router(student_router)

# ---------------------------------------------------------------------------
# Register the teachers router
# ---------------------------------------------------------------------------
app.include_router(teacher_router)

# ---------------------------------------------------------------------------
# Register the authentication router
# ---------------------------------------------------------------------------
app.include_router(auth_router)

# ---------------------------------------------------------------------------
# Register the academic sessions router
# ---------------------------------------------------------------------------
app.include_router(academic_session_router)

# ---------------------------------------------------------------------------
# Register the departments router
# ---------------------------------------------------------------------------
app.include_router(department_router)

# ---------------------------------------------------------------------------
# Register the programs router
# ---------------------------------------------------------------------------
app.include_router(program_router)

# ---------------------------------------------------------------------------
# Register the semesters router
# ---------------------------------------------------------------------------
app.include_router(semester_router)

# ---------------------------------------------------------------------------
# Register the courses router
# ---------------------------------------------------------------------------
app.include_router(course_router)

# ---------------------------------------------------------------------------
# Register the subjects router
# ---------------------------------------------------------------------------
app.include_router(subject_router)

# ---------------------------------------------------------------------------
# Register the attendance router
# ---------------------------------------------------------------------------
app.include_router(attendance_router)

# ---------------------------------------------------------------------------
# Register the sections router
# ---------------------------------------------------------------------------
app.include_router(section_router)

# ---------------------------------------------------------------------------
# Register the enrollments router
# ---------------------------------------------------------------------------
app.include_router(enrollment_router)

# ---------------------------------------------------------------------------
# Register the teacher assignments router
# ---------------------------------------------------------------------------
app.include_router(teacher_assignment_router)

# ---------------------------------------------------------------------------
# Register the classrooms router
# ---------------------------------------------------------------------------
app.include_router(classroom_router)

# ---------------------------------------------------------------------------
# Register the timetables router
# ---------------------------------------------------------------------------
app.include_router(timetable_router)

# ---------------------------------------------------------------------------
# Register the examinations router
# ---------------------------------------------------------------------------
app.include_router(examination_router)

# ---------------------------------------------------------------------------
# Register the exam marks router
# ---------------------------------------------------------------------------
app.include_router(exam_mark_router)

# ---------------------------------------------------------------------------
# Register the results router
# ---------------------------------------------------------------------------
app.include_router(result_router)

# ---------------------------------------------------------------------------
# Register the fee structures router
# ---------------------------------------------------------------------------
app.include_router(fee_structure_router)

# ---------------------------------------------------------------------------
# Register the fee payments router
# ---------------------------------------------------------------------------
app.include_router(fee_payment_router)


# ---------------------------------------------------------------------------
# Root health-check endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def health_check():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "Running Successfully",
    }