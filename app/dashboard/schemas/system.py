from typing import List

from pydantic import BaseModel, ConfigDict


class RoleCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    count: int


class SystemAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_users: int
    users_by_role: List[RoleCount]
    app_name: str
    app_version: str
