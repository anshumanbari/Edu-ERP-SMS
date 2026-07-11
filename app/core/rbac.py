from fastapi import Depends

from app.core.exceptions import ForbiddenException
from app.core.roles import Role
from app.core.security import get_current_user
from app.models.user import User


def require_roles(*allowed_roles: Role):
    """
    Dependency factory that restricts an endpoint to the given roles.

    Usage: Depends(require_roles(Role.ADMIN, Role.TEACHER))

    Raises:
        AppException (403 FORBIDDEN): If the authenticated user's role is
        not one of allowed_roles.
    """

    def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException("You do not have permission to perform this action.")
        return current_user

    return _check_role
