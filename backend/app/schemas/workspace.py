from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Tenant roles a member can hold. Mirrors app.core.policy.Role.
_ROLE = r"^(owner|admin|editor|member|viewer)$"
_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class WorkspaceIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    plan: str


class WorkspaceWithRoleOut(WorkspaceOut):
    role: str  # the requesting user's role in this workspace


class MemberOut(BaseModel):
    user_id: int
    name: str
    email: str
    avatar_url: str | None = None
    role: str
    status: str


class RolePatch(BaseModel):
    role: str = Field(pattern=_ROLE)


class InviteIn(BaseModel):
    email: str = Field(pattern=_EMAIL, max_length=255)
    role: str = Field(default="member", pattern=_ROLE)


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    expires_at: datetime
    accepted_at: datetime | None = None


class InviteCreatedOut(InviteOut):
    # Raw token returned once, at creation time, so it can be emailed / linked.
    token: str


class AcceptInviteIn(BaseModel):
    token: str = Field(min_length=10)
