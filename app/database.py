import re
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.settings import settings

engine = create_async_engine(settings.db_uri, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # add underscore between each word
        name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", cls.__name__).lower()

        # add plural form
        if name.endswith("y"):
            name = name[:-1] + "ies"
        elif not name.endswith("s"):
            name = name + "s"

        return name
