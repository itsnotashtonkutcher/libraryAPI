from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.books import BookCreate, BookResponse, BookUpdate, BookWithStatus
from app.schemas.users import BorrowingResponse
from app.services import books as service
from app.utils.dependencies import PaginationParams, get_pagination_params
from app.utils.pagination import get_pagination_model_for, paginate
from app.utils.schemas import SerialString

router = APIRouter(prefix="/books", tags=["books"])


# CRUD operations for Books


@router.get("", response_model=get_pagination_model_for(BookWithStatus, "books"))
@paginate(label="books", record_model=BookWithStatus)
async def get_all_books(
    request: Request,  # noqa: F841
    db: AsyncSession = Depends(get_db),
    page_params: PaginationParams = Depends(get_pagination_params),
):
    return await service.get_all_books(db, page_params)


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book_create: BookCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_book(db, book_create)


@router.get("/{serial}", response_model=BookWithStatus)
async def get_book(serial: SerialString, db: AsyncSession = Depends(get_db)):
    return await service.get_book(db, serial)


@router.patch("/{serial}", response_model=BookResponse)
async def update_book(
    serial: SerialString, book_update: BookUpdate, db: AsyncSession = Depends(get_db)
):
    return await service.update_book(db, book_update, serial)


@router.delete("/{serial}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    serial: SerialString, force: bool = False, db: AsyncSession = Depends(get_db)
):
    return await service.delete_book(db, serial, force)


# operations for borrowings


@router.post("/{serial}/borrow/{user_id}", response_model=BorrowingResponse)
async def borrow_book(
    serial: SerialString, user_id: SerialString, db: AsyncSession = Depends(get_db)
):
    return await service.borrow_book(db, user_id, serial)


@router.post("/{serial}/return", status_code=status.HTTP_200_OK)
async def return_book(serial: SerialString, db: AsyncSession = Depends(get_db)):
    return await service.return_book(db, serial)
