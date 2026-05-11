from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_managers.books import BookManager
from app.db_managers.borrowing import BorrowingManager
from app.db_managers.users import UserManager
from app.models import Book
from app.schemas.books import BookCreate, BookUpdate
from app.settings import settings
from app.utils.dependencies import PaginationParams
from app.utils.schemas import SerialString

manager = BookManager()
user_manager = UserManager()
borrow_manager = BorrowingManager()


async def get_all_books(db: AsyncSession, page_params: PaginationParams):
    return await manager.get_books_with_status(db, page_params)


async def create_book(db: AsyncSession, book_create: BookCreate):
    existing = await manager.get_book(db, book_create.serial_number)
    if existing:
        raise HTTPException(status_code=400, detail="Book serial already exists")

    return await manager.create_book(db, book_create.model_dump())


async def get_book(db: AsyncSession, serial: str):
    book = await manager.get_book_with_status(db, serial)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return book


async def update_book(db: AsyncSession, book_update: BookUpdate, serial: str):
    book = await db.get(Book, serial)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_update.model_dump(exclude_unset=True)

    return await manager.update_book(db, book, update_data)


async def delete_book(db: AsyncSession, serial: SerialString, force: bool):
    book = await manager.get_book_for_update(db, serial)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not force:
        has_active = await manager.has_active_borrowings(db, serial)
        if has_active:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot delete book with active borrowings."
                    " Use force=true to override."
                ),
            )

    await manager.delete_book(db, serial)
    return None


async def borrow_book(db: AsyncSession, user_id: SerialString, serial: SerialString):
    user = await user_manager.get_user_for_update(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    book = await manager.get_book_for_update(db, serial)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing_borrow = await borrow_manager.get_active_borrowing_by_book(db, serial)
    if existing_borrow:
        raise HTTPException(status_code=400, detail="Book is currently borrowed")

    active_count = await borrow_manager.count_active_user_borrowings(db, user_id)
    if active_count >= settings.max_book_count:
        raise HTTPException(status_code=400, detail="User reached max borrowing limit")

    return await borrow_manager.add_object(
        db, {"user_serial": user_id, "book_serial": serial}
    )


async def return_book(db: AsyncSession, serial: SerialString):
    borrowing = await borrow_manager.get_active_borrowing_by_book(db, serial)
    if not borrowing:
        raise HTTPException(
            status_code=404, detail="Active booking for this book not found"
        )

    borrowing.returned_at = datetime.now()
    await db.commit()
    return {"message": "Book returned successfully"}
