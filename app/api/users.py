from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.users import BorrowingResponse, UserCreate, UserResponse
from app.services import users as service
from app.utils.dependencies import PaginationParams, get_pagination_params
from app.utils.pagination import get_pagination_model_for, paginate
from app.utils.schemas import SerialString

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=get_pagination_model_for(UserResponse, "users"))
@paginate(label="users", record_model=UserResponse)
async def get_all_users(
    request: Request,  # noqa: F841
    db: AsyncSession = Depends(get_db),
    page_params: PaginationParams = Depends(get_pagination_params),
):
    return await service.get_all_users(db, page_params)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: SerialString, db: AsyncSession = Depends(get_db)):
    return await service.get_user_by_id(db, user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_user(db, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: SerialString, force: bool = False, db: AsyncSession = Depends(get_db)
):
    return await service.delete_user(db, user_id, force)


@router.get("/{user_id}/bookings", response_model=list[BorrowingResponse])
async def get_active_borrowings(user_id: str, db: AsyncSession = Depends(get_db)):
    # no pagination, because there is limited number of borrowed books
    return await service.get_active_borrowings(db, user_id)


@router.get(
    "/{user_id}/bookings/history",
    response_model=get_pagination_model_for(BorrowingResponse, "borrowings"),
)
@paginate(label="borrowings", record_model=BorrowingResponse)
async def get_historic_borrowings(
    request: Request,  # noqa: F841
    user_id: str,
    page_params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_historic_borrowings(db, page_params, user_id)
