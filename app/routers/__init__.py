from fastapi import APIRouter

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
from app.dashboard.router import router as dashboard_router

# ---------------------------------------------------------------------------
# Central API router — aggregates every domain router in one place so
# app/main.py only has to include a single router. Each sub-router already
# carries its own prefix/tags, so mounting them here with no extra prefix
# preserves every existing URL exactly as-is.
# ---------------------------------------------------------------------------
api_router = APIRouter()

api_router.include_router(student_router)
api_router.include_router(teacher_router)
api_router.include_router(auth_router)
api_router.include_router(academic_session_router)
api_router.include_router(department_router)
api_router.include_router(program_router)
api_router.include_router(semester_router)
api_router.include_router(course_router)
api_router.include_router(subject_router)
api_router.include_router(attendance_router)
api_router.include_router(section_router)
api_router.include_router(enrollment_router)
api_router.include_router(teacher_assignment_router)
api_router.include_router(classroom_router)
api_router.include_router(timetable_router)
api_router.include_router(examination_router)
api_router.include_router(exam_mark_router)
api_router.include_router(result_router)
api_router.include_router(fee_structure_router)
api_router.include_router(fee_payment_router)
api_router.include_router(dashboard_router)

__all__ = ["api_router"]
