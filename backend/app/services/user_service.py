from app.core.errors import NotFoundError
from app.repositories.user_repo import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def list_users(self, *, limit: int = 100, offset: int = 0):
        return await self.user_repo.list_all(limit=limit, offset=offset)

    async def set_role(self, user_id: int, role: str):
        user = await self.user_repo.update(user_id, role=role)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def update_profile(self, user_id: int, **kwargs):
        user = await self.user_repo.update(user_id, **kwargs)
        if user is None:
            raise NotFoundError("User not found")
        return user
