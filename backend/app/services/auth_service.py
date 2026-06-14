from dataclasses import dataclass

import jwt as pyjwt

from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import create_token, decode_token, hash_password, verify_password


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self, user_repo, *, jwt_secret: str, access_minutes: int,
                 refresh_minutes: int, session=None, workspace_repo=None,
                 membership_repo=None) -> None:
        self.user_repo = user_repo
        self.jwt_secret = jwt_secret
        self.access_minutes = access_minutes
        self.refresh_minutes = refresh_minutes
        # Optional: required only for register(), which provisions a workspace.
        self.session = session
        self.workspace_repo = workspace_repo
        self.membership_repo = membership_repo

    async def register(self, *, email: str, password: str, name: str):
        if await self.user_repo.get_by_email(email):
            raise ConflictError("Email already registered")
        user = await self.user_repo.create(
            email=email, password_hash=hash_password(password), name=name
        )
        # Every new user gets a personal workspace they own — otherwise they'd
        # have nowhere to put projects/snippets/bookmarks.
        if self.workspace_repo is not None and self.membership_repo is not None:
            ws = await self.workspace_repo.create(
                name=f"{name}'s Workspace", slug=f"ws-{user.id}", created_by=user.id
            )
            await self.membership_repo.add(workspace_id=ws.id, user_id=user.id, role="owner")
            await self.session.commit()
        return user

    async def login(self, *, email: str, password: str) -> TokenPair:
        user = await self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        return self._issue(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Not a refresh token")
        return self._issue(int(payload["sub"]))

    async def get_user(self, access_token: str):
        payload = self._decode(access_token)
        if payload.get("type") != "access":
            raise UnauthorizedError("Not an access token")
        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if user is None:
            raise UnauthorizedError("User no longer exists")
        return user

    def _issue(self, user_id: int) -> TokenPair:
        return TokenPair(
            access_token=create_token(subject=str(user_id), token_type="access",
                                      secret=self.jwt_secret, minutes=self.access_minutes),
            refresh_token=create_token(subject=str(user_id), token_type="refresh",
                                       secret=self.jwt_secret, minutes=self.refresh_minutes),
        )

    def _decode(self, token: str) -> dict:
        try:
            return decode_token(token, secret=self.jwt_secret)
        except pyjwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc
