from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, email: str, password_hash: str, name: str) -> User:
        user = User(email=email, password_hash=password_hash, name=name)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        res = await self.session.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_ids(self, user_ids: list[int]) -> list[User]:
        if not user_ids:
            return []
        res = await self.session.execute(select(User).where(User.id.in_(user_ids)))
        return list(res.scalars().all())

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        res = await self.session.execute(
            select(User).order_by(User.created_at).limit(limit).offset(offset)
        )
        return list(res.scalars().all())

    async def update(self, user_id: int, **kwargs) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        for key, val in kwargs.items():
            setattr(user, key, val)
        await self.session.commit()
        await self.session.refresh(user)
        return user
