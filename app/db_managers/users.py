from collections.abc import Sequence

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_managers.base import BaseManager
from app.models import Borrowing, User
from app.schemas.users import UserCreate
from app.utils.dependencies import PaginationParams
from app.utils.schemas import SerialString


class UserManager(BaseManager):
    model = User

    async def get_all_users(
        self, db: AsyncSession, page_params: PaginationParams
    ) -> Sequence[User]:
        return await self.get_all_objects(db, page_params)

    async def get_user_by_id(self, db: AsyncSession, user_id: SerialString) -> User:
        return await self.read_object(db, user_id)

    async def create_user(self, db: AsyncSession, payload: UserCreate) -> User:
        return await self.add_object(db, payload.model_dump())

    async def get_user_for_update(self, db: AsyncSession, user_id: SerialString):
        stmt = (
            select(self.model)
            .where(self.model.library_card_id == user_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def has_active_borrowings(db: AsyncSession, user_id: SerialString):
        active_exists_stmt = (
            exists(Borrowing)
            .where(Borrowing.user_serial == user_id, Borrowing.returned_at.is_(None))
            .select()
        )

        active_result = await db.execute(active_exists_stmt)
        return active_result.scalar()

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: SerialString) -> None:
        await db.execute(delete(Borrowing).where(Borrowing.user_serial == user_id))
        stmt = delete(User).where(User.library_card_id == user_id)
        await db.execute(stmt)
        await db.commit()

    async def get_active_borrowings(
        self, db: AsyncSession, user_id: str, page_params: PaginationParams
    ):
        stmt = select(Borrowing).where(
            Borrowing.user_serial == user_id, Borrowing.returned_at.is_(None)
        )
        stmt = self.add_pagination_params_to(stmt, page_params)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_historic_borrowings(
        self, db: AsyncSession, user_id: str, page_params: PaginationParams
    ):
        stmt = select(Borrowing).where(
            Borrowing.user_serial == user_id, Borrowing.returned_at.is_not(None)
        )
        stmt = self.add_pagination_params_to(stmt, page_params)
        result = await db.execute(stmt)
        return result.scalars().all()
