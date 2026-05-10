from datetime import datetime, timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import Book, Borrowing, User
from app.settings import settings


@pytest_asyncio.fixture(scope="function")
async def engine():
    engine = create_async_engine(settings.db_uri, echo=False)

    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    yield engine

    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    async with engine.connect() as conn:
        transaction = await conn.begin()
        await conn.run_sync(Base.metadata.create_all)
        session = AsyncSession(bind=conn, expire_on_commit=False)

        yield session

        await session.close()
        await conn.run_sync(Base.metadata.drop_all)
        await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def non_existing_id(seed_db):
    users, *_ = seed_db
    non_existing_id = "0" * 6
    # check prerequisites
    assert not any([user.library_card_id == non_existing_id for user in users])
    return non_existing_id


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession):
    async def mock_get_db():
        yield db_session

    app.dependency_overrides[get_db] = mock_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_db(db_session):
    users = [
        User(library_card_id="123456", name="Robert Smith"),
        User(library_card_id="123457", name="Robert Smith"),
        User(library_card_id="132456", name="John Smith"),
        User(library_card_id="654321", name="Carmela Soprano"),
    ]
    books = [
        Book(
            serial_number="123456",
            title="The Sound and the Fury",
            author="William Faulkner",
        ),
        Book(serial_number="123457", title="Godfather", author="Mario Puzo"),
        Book(serial_number="132456", title="Fluent Python", author="Luciano Ramalho"),
        Book(serial_number="132457", title="Fluent Python", author="Luciano Ramalho"),
        Book(serial_number="132458", title="Fluent Python", author="Luciano Ramalho"),
        Book(serial_number="132459", title="Fluent Python", author="Luciano Ramalho"),
        Book(serial_number="132450", title="Fluent Python", author="Luciano Ramalho"),
        Book(
            serial_number="654321",
            title="Inside The Python Virtual Machine",
            author="Obi Ike-Nwosu",
        ),
    ]
    borrowings = [
        Borrowing(
            user_serial=users[0].library_card_id, book_serial=books[0].serial_number
        ),
        *[
            Borrowing(
                user_serial=users[1].library_card_id, book_serial=book.serial_number
            )
            for book in books[1 : 1 + settings.max_book_count]
        ],
    ]
    past_borrow = datetime.now() - timedelta(days=14)
    past_return = datetime.now() - timedelta(days=7)

    historical_borrowings = [
        Borrowing(
            user_serial=users[0].library_card_id,
            book_serial=books[0].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
        Borrowing(
            user_serial=users[0].library_card_id,
            book_serial=books[1].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
        Borrowing(
            user_serial=users[1].library_card_id,
            book_serial=books[2].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
        Borrowing(
            user_serial=users[1].library_card_id,
            book_serial=books[3].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
        Borrowing(
            user_serial=users[2].library_card_id,
            book_serial=books[4].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
        Borrowing(
            user_serial=users[2].library_card_id,
            book_serial=books[5].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
        Borrowing(
            user_serial=users[3].library_card_id,
            book_serial=books[6].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
        Borrowing(
            user_serial=users[3].library_card_id,
            book_serial=books[7].serial_number,
            borrowed_at=past_borrow,
            returned_at=past_return,
        ),
    ]

    collections = (users, books, borrowings, historical_borrowings)

    for collection in collections:
        db_session.add_all(collection)

    await db_session.flush()

    for collection in collections:
        for item in collection:
            await db_session.refresh(item)

    return collections
