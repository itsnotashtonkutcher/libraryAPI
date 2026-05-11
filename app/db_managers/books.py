from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_managers.base import BaseManager
from app.models import Book, Borrowing
from app.utils.dependencies import PaginationParams
from app.utils.schemas import SerialString


class BookManager(BaseManager):
    model = Book

    async def get_book(self, db: AsyncSession, book_serial: str):
        return await self.read_object(db, book_serial)

    async def create_book(self, db: AsyncSession, payload: dict):
        return await self.add_object(db, payload)

    async def get_books_with_status(
        self, db: AsyncSession, page_params: PaginationParams
    ):
        stmt = (
            select(
                self.model,
                exists()
                .where(Borrowing.book_serial == self.model.serial_number)
                .where(Borrowing.returned_at.is_(None))
                .label("is_borrowed"),
            )
            .offset(page_params.offset)
            .limit(page_params.size)
        )

        result = await db.execute(stmt)
        rows = result.all()

        books = []
        for book, is_borrowed in rows:
            book.is_borrowed = is_borrowed
            books.append(book)
        return books

    @staticmethod
    async def update_book(db: AsyncSession, book: Book, payload: dict):
        for key, value in payload.items():
            # patch should only change columns send in payload
            setattr(book, key, value)

        await db.commit()
        await db.refresh(book)
        return book

    async def get_book_with_status(self, db: AsyncSession, serial: str):
        stmt = select(
            self.model,
            exists()
            .where(Borrowing.book_serial == serial)
            .where(Borrowing.returned_at.is_(None))
            .label("is_borrowed"),
        ).where(self.model.serial_number == serial)

        result = await db.execute(stmt)
        row = result.first()
        if not row:
            return None

        book, is_borrowed = row
        book.is_borrowed = is_borrowed
        return book

    async def get_book_for_update(self, db: AsyncSession, serial: SerialString):
        stmt = (
            select(self.model)
            .where(self.model.serial_number == serial)
            .with_for_update()
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def has_active_borrowings(db: AsyncSession, serial: SerialString):
        stmt = select(func.count(Borrowing.id)).where(
            Borrowing.book_serial == serial, Borrowing.returned_at.is_(None)
        )
        result = await db.execute(stmt)
        return result.scalar() > 0

    async def delete_book(self, db: AsyncSession, serial: SerialString):
        await db.execute(delete(Borrowing).where(Borrowing.book_serial == serial))
        stmt = delete(self.model).where(self.model.serial_number == serial)
        await db.execute(stmt)
        await db.commit()
