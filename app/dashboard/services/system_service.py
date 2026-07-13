from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dashboard.schemas.system import RoleCount, SystemAnalyticsResponse
from app.models.user import User


def get_system_analytics(db: Session) -> SystemAnalyticsResponse:
    """
    Authenticated-user counts by role, plus the running application's
    identity/version — the only "system" facts available without inventing
    infrastructure metrics no module currently tracks.
    """
    total_users = db.query(func.count(User.id)).scalar() or 0

    role_rows = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = [
        RoleCount(role=role.value if hasattr(role, "value") else str(role), count=count)
        for role, count in role_rows
    ]

    return SystemAnalyticsResponse(
        total_users=total_users,
        users_by_role=users_by_role,
        app_name=settings.app_name,
        app_version=settings.app_version,
    )
