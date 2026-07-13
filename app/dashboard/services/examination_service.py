from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dashboard.schemas.examination import ExaminationAnalyticsResponse, ResultStatusCount
from app.models.exam_mark import ExamMark
from app.models.examination import Examination
from app.models.result import Result


def get_examination_analytics(db: Session) -> ExaminationAnalyticsResponse:
    """
    Examination volume from the Examination/Exam Mark modules, plus pass/fail
    distribution from the Result module. Results have not necessarily been
    generated for every exam mark, so average_result_percentage is null
    rather than fabricated when no Result rows exist yet.
    """
    total_examinations = db.query(func.count(Examination.id)).scalar() or 0
    total_exam_marks_recorded = db.query(func.count(ExamMark.id)).scalar() or 0

    average_result_percentage = db.query(func.avg(Result.percentage)).scalar()

    status_rows = db.query(Result.status, func.count(Result.id)).group_by(Result.status).all()
    results_by_status = [ResultStatusCount(status=status, count=count) for status, count in status_rows]

    total_results_published = (
        db.query(func.count(Result.id)).filter(Result.is_published.is_(True)).scalar() or 0
    )

    return ExaminationAnalyticsResponse(
        total_examinations=total_examinations,
        total_exam_marks_recorded=total_exam_marks_recorded,
        average_result_percentage=average_result_percentage,
        results_by_status=results_by_status,
        total_results_published=total_results_published,
    )
