from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_managers.base import BaseManager
from app.models import Borrowing
from app.utils.schemas import SerialString


class BorrowingManager(BaseManager):
    model = Borrowing

    async def get_active_borrowing_by_book(
        self, db: AsyncSession, serial: SerialString
    ):
        stmt = select(self.model).where(
            self.model.book_serial == serial, self.model.returned_at.is_(None)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_active_user_borrowings(
        self, db: AsyncSession, user_id: SerialString
    ):
        stmt = select(func.count(self.model.id)).where(
            self.model.user_serial == user_id, self.model.returned_at.is_(None)
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
