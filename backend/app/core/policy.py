"""Workspace-scoped RBAC policy.

The permission matrix lives in code (fast, versioned, testable). The database only
stores *role assignments* on `memberships.role` — never the permissions themselves.

This is intentionally separate from the legacy global `users.role` (admin|manager|
member), which now only governs DevDesk *staff* tooling. Tenant access is decided
here, per (user, workspace).
"""
from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    MEMBER = "member"
    VIEWER = "viewer"


class Perm(str, Enum):
    CONTENT_READ = "content:read"
    CONTENT_WRITE = "content:write"
    CONTENT_DELETE = "content:delete"
    COMMENT_WRITE = "comment:write"
    MEMBER_MANAGE = "member:manage"
    WORKSPACE_MANAGE = "workspace:manage"
    WORKSPACE_DELETE = "workspace:delete"
    BILLING_MANAGE = "billing:manage"


# Highest → lowest. Used to forbid escalating someone above your own level.
ROLE_RANK: dict[str, int] = {
    Role.OWNER: 50,
    Role.ADMIN: 40,
    Role.EDITOR: 30,
    Role.MEMBER: 20,
    Role.VIEWER: 10,
}

_VIEWER = {Perm.CONTENT_READ}
_MEMBER = _VIEWER | {Perm.CONTENT_WRITE, Perm.COMMENT_WRITE}
_EDITOR = _MEMBER | {Perm.CONTENT_DELETE}
_ADMIN = _EDITOR | {Perm.MEMBER_MANAGE, Perm.WORKSPACE_MANAGE}
_OWNER = _ADMIN | {Perm.WORKSPACE_DELETE, Perm.BILLING_MANAGE}

ROLE_PERMS: dict[str, set[Perm]] = {
    Role.OWNER: _OWNER,
    Role.ADMIN: _ADMIN,
    Role.EDITOR: _EDITOR,
    Role.MEMBER: _MEMBER,
    Role.VIEWER: _VIEWER,
}


def can(role: str, perm: Perm) -> bool:
    """True if `role` grants `perm`. Unknown roles grant nothing."""
    return perm in ROLE_PERMS.get(role, set())


def rank(role: str) -> int:
    return ROLE_RANK.get(role, 0)


def is_valid_role(role: str) -> bool:
    return role in ROLE_PERMS
