from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    total_users: int
    total_workspaces: int
    active_subscriptions: int
    workspaces_by_plan: dict[str, int]


class AdminWorkspaceItem(BaseModel):
    id: str
    name: str
    plan: str
    plan_status: str
    storage_used_bytes: int
    created_at: str


class AdminUserItem(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_superadmin: bool
    created_at: str
