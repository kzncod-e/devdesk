import pytest

from app.core.errors import ConflictError, UnauthorizedError
from app.services.auth_service import AuthService


class FakeUserRepo:
    def __init__(self):
        self.users = {}
        self._next = 1

    async def create(self, *, email, password_hash, name):
        user = type("U", (), {"id": self._next, "email": email,
                              "password_hash": password_hash, "name": name})()
        self.users[email] = user
        self._next += 1
        return user

    async def get_by_email(self, email):
        return self.users.get(email)

    async def get_by_id(self, user_id):
        return next((u for u in self.users.values() if u.id == user_id), None)


def make_service():
    return AuthService(FakeUserRepo(), jwt_secret="test", access_minutes=15,
                       refresh_minutes=60 * 24 * 7)


@pytest.mark.asyncio
async def test_register_then_login_returns_tokens():
    svc = make_service()
    user = await svc.register(email="a@b.c", password="pw123456", name="A")
    assert user.id == 1
    tokens = await svc.login(email="a@b.c", password="pw123456")
    assert tokens.access_token and tokens.refresh_token


@pytest.mark.asyncio
async def test_register_duplicate_email_raises_conflict():
    svc = make_service()
    await svc.register(email="a@b.c", password="pw123456", name="A")
    with pytest.raises(ConflictError):
        await svc.register(email="a@b.c", password="other123", name="B")


@pytest.mark.asyncio
async def test_login_wrong_password_raises_unauthorized():
    svc = make_service()
    await svc.register(email="a@b.c", password="pw123456", name="A")
    with pytest.raises(UnauthorizedError):
        await svc.login(email="a@b.c", password="wrong")


@pytest.mark.asyncio
async def test_refresh_rejects_access_token():
    svc = make_service()
    await svc.register(email="a@b.c", password="pw123456", name="A")
    tokens = await svc.login(email="a@b.c", password="pw123456")
    with pytest.raises(UnauthorizedError):
        await svc.refresh(tokens.access_token)  # wrong token type
    new_tokens = await svc.refresh(tokens.refresh_token)
    assert new_tokens.access_token
