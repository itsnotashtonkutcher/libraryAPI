from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Borrowing, User
from app.schemas.users import UserCreate
from app.utils.dependencies import PaginationParams
from app.utils.schemas import SerialString


async def get_all_users(db: AsyncSession, page_params: PaginationParams):
    stmt = select(User).offset(page_params.offset).limit(page_params.size)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return users


async def get_user_by_id(db: AsyncSession, user_id: SerialString):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


async def create_user(db: AsyncSession, payload: UserCreate):
    stmt = select(User).where(User.library_card_id == payload.library_card_id)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this ID already exists")

    new_user = User(**payload.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def delete_user(db: AsyncSession, user_id: SerialString, force: bool):
    # to not interfere with borrowing, select for update
    stmt = select(User).where(User.library_card_id == user_id).with_for_update()
    result = await db.execute(stmt)

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not force:
        active_stmt = select(Borrowing).where(
            Borrowing.user_serial == user_id, Borrowing.returned_at is None
        )
        active_result = await db.execute(active_stmt)
        has_active_bookings = active_result.scalars().first() is not None
        if has_active_bookings:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot delete user with active bookings.",
                    "Use force=true to override.",
                ),
            )

    del_borrowings_stmt = delete(Borrowing).where(Borrowing.user_serial == user_id)
    await db.execute(del_borrowings_stmt)

    await db.delete(user)
    await db.commit()

    return None


async def get_active_borrowings(db: AsyncSession, user_id: str):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(Borrowing).where(
        Borrowing.user_serial == user_id, Borrowing.returned_at is None
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_historic_borrowings(
    db: AsyncSession, page_params: PaginationParams, user_id: str
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = (
        select(Borrowing)
        .where(Borrowing.user_serial == user_id, Borrowing.returned_at is not None)
        .offset(page_params.offset)
        .limit(page_params.size)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
