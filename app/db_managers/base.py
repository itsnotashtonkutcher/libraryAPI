from sqlalchemy import Select, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.utils.dependencies import PaginationParams


class BaseManager:
    model: type[Base] | None = None

    async def read_object(self, db: AsyncSession, pk_value):
        pk_column_name = inspect(self.model).primary_key[0].name
        pk_column = getattr(self.model, pk_column_name)
        stmt = select(self.model).where(pk_column == pk_value)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_object(self, db: AsyncSession, obj_data: dict):
        new_obj = self.model(**obj_data)
        db.add(new_obj)
        await db.commit()
        await db.refresh(new_obj)
        return new_obj

    async def get_all_objects(self, db: AsyncSession, page_params: PaginationParams):
        stmt = select(self.model)
        stmt = self.add_pagination_params_to(stmt, page_params)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def add_pagination_params_to(query: Select, page_params: PaginationParams):
        return query.offset(page_params.offset).limit(page_params.size)
