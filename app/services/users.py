from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_managers.users import UserManager
from app.schemas.users import UserCreate
from app.utils.dependencies import PaginationParams
from app.utils.schemas import SerialString

manager = UserManager()


async def get_all_users(db: AsyncSession, page_params: PaginationParams):
    return await manager.get_all_users(db, page_params)


async def get_user_by_id(db: AsyncSession, user_id: SerialString):
    user = await manager.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


async def create_user(db: AsyncSession, payload: UserCreate):
    existing_user = await manager.get_user_by_id(db, payload.library_card_id)

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this ID already exists")

    return await manager.create_user(db, payload)


async def delete_user(db: AsyncSession, user_id: SerialString, force: bool):
    # to not interfere with borrowing, select for update
    user = await manager.get_user_for_update(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not force:
        has_active_borrowings = await manager.has_active_borrowings(db, user_id)
        if has_active_borrowings:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot delete user with active borrowings."
                    " Use force=true to override."
                ),
            )

    await manager.delete_user(db, user_id)

    return None


async def get_active_borrowings(
    db: AsyncSession, user_id: str, page_params: PaginationParams
):
    user = await manager.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await manager.get_active_borrowings(db, user_id, page_params)


async def get_historic_borrowings(
    db: AsyncSession, page_params: PaginationParams, user_id: str
):
    user = await manager.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await manager.get_historic_borrowings(db, user_id, page_params)
