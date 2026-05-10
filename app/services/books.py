from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Book, Borrowing, User
from app.schemas.books import BookCreate, BookUpdate
from app.settings import settings
from app.utils.dependencies import PaginationParams
from app.utils.schemas import SerialString


async def get_all_books(db: AsyncSession, page_params: PaginationParams):
    stmt = (
        select(
            Book,
            exists()
            .where(Borrowing.book_serial == Book.serial_number)
            .where(Borrowing.returned_at is None)
            .label("is_borrowed"),
        )
        .offset(page_params.offset)
        .limit(page_params.size)
    )

    result = await db.execute(stmt)

    books_with_status = []
    for row in result.all():
        book, is_borrowed = row
        book.is_borrowed = is_borrowed
        books_with_status.append(book)

    return books_with_status


async def create_book(db: AsyncSession, book_create: BookCreate):
    existing = await db.get(Book, book_create.serial_number)
    if existing:
        raise HTTPException(status_code=400, detail="Book serial already exists")

    new_book = Book(**book_create.model_dump())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book


async def get_book(db: AsyncSession, serial: str):
    stmt = select(
        Book,
        exists()
        .where(Borrowing.book_serial == serial)
        .where(Borrowing.returned_at is None)
        .label("is_borrowed"),
    ).where(Book.serial_number == serial)

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Book not found")

    book, is_borrowed = row
    book.is_borrowed = is_borrowed
    return book


async def update_book(db: AsyncSession, book_update: BookUpdate, serial: str):
    book = await db.get(Book, serial)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        # patch should only change columns send in payload
        setattr(book, key, value)

    await db.commit()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, serial: SerialString, force: bool):
    stmt = select(Book).where(Book.serial_number == serial).with_for_update()
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not force:
        active_stmt = select(func.count(Borrowing.id)).where(
            Borrowing.book_serial == serial, Borrowing.returned_at is None
        )
        active_result = await db.execute(active_stmt)
        active_count = active_result.scalar() or 0

        if active_count > 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Book is currently borrowed ({active_count} active).",
                    " Use force=true.",
                ),
            )

    await db.delete(book)

    return None


async def borrow_book(db: AsyncSession, user_id: SerialString, serial: SerialString):
    # block user first to not interfere with user deletion
    user_stmt = select(User).where(User.library_card_id == user_id).with_for_update()
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    book_stmt = select(Book).where(Book.serial_number == serial).with_for_update()
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    check_stmt = select(Borrowing).where(
        Borrowing.book_serial == serial, Borrowing.returned_at is None
    )
    existing_borrow = await db.execute(check_stmt)
    if existing_borrow.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Book is currently borrowed")

    count_stmt = select(func.count(Borrowing.id)).where(
        Borrowing.user_serial == user_id, Borrowing.returned_at is None
    )
    count_result = await db.execute(count_stmt)
    active_count = count_result.scalar() or 0

    if active_count >= settings.max_book_count:
        raise HTTPException(status_code=400, detail="User reached max borrowing limit")

    new_borrowing = Borrowing(user_serial=user_id, book_serial=serial)
    db.add(new_borrowing)

    await db.commit()
    await db.refresh(new_borrowing)

    return new_borrowing


async def return_book(db: AsyncSession, serial: SerialString):
    stmt = select(Borrowing).where(
        Borrowing.book_serial == serial, Borrowing.returned_at is None
    )
    result = await db.execute(stmt)
    borrowing = result.scalar_one_or_none()

    if not borrowing:
        raise HTTPException(
            status_code=404, detail="Active booking for this book not found"
        )

    borrowing.returned_at = datetime.now()
    await db.commit()
    return {"message": "Book returned successfully"}
