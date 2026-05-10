import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import Borrowing


@pytest.mark.asyncio
async def test_create_book_success(test_client: AsyncClient, non_existing_id):
    payload = {
        "serial_number": non_existing_id,
        "title": "Test Book",
        "author": "Author",
    }
    response = await test_client.post("/books", json=payload)
    assert response.status_code == 201
    assert response.json()["serial_number"] == non_existing_id


@pytest.mark.asyncio
async def test_create_book_already_exists(
    test_client: AsyncClient, db_session, seed_db
):
    _, books, *__ = seed_db
    payload = {"serial_number": books[0].serial_number, "title": "New", "author": "New"}
    response = await test_client.post("/books", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_books_list(test_client: AsyncClient, db_session, seed_db):
    _, books, *__ = seed_db
    response = await test_client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == len(books)


@pytest.mark.asyncio
async def test_get_single_book_not_found(test_client: AsyncClient, non_existing_id):
    response = await test_client.get(f"/books/{non_existing_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_book(test_client: AsyncClient, db_session, seed_db):
    _, books, *__ = seed_db
    author_before = books[0].author
    response = await test_client.patch(
        f"/books/{books[0].serial_number}", json={"title": "New Title"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["author"] == author_before


@pytest.mark.asyncio
async def test_delete_borrowed_book_only_succeeds_when_force_used(
    test_client: AsyncClient, db_session, seed_db
):
    _, books, *__ = seed_db
    response = await test_client.delete(f"/books/{books[0].serial_number}")
    assert response.status_code == 400
    assert "force=true" in response.json()["detail"]

    response = await test_client.delete(f"/books/{books[0].serial_number}?force=true")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_borrow_book_success(test_client: AsyncClient, db_session, seed_db):
    users, books, *_ = seed_db
    user, book = users[3], books[-1]
    response = await test_client.post(
        f"/books/{book.serial_number}/borrow/{user.library_card_id}"
    )
    assert response.status_code == 200
    assert response.json()["book_serial"] == book.serial_number
    assert response.json()["user_serial"] == user.library_card_id


@pytest.mark.asyncio
async def test_borrow_book_fails_when_book_already_borrowed(
    test_client: AsyncClient, db_session, seed_db
):
    users, books, *_ = seed_db
    user, book = users[3], books[1]
    response = await test_client.post(
        f"/books/{book.serial_number}/borrow/{user.library_card_id}"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Book is currently borrowed"


@pytest.mark.asyncio
async def test_borrow_book_limit_reached(test_client: AsyncClient, db_session, seed_db):
    users, books, *_ = seed_db
    # second user has max number of books
    user, book = users[1], books[-1]
    response = await test_client.post(
        f"/books/{book.serial_number}/borrow/{user.library_card_id}"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User reached max borrowing limit"


@pytest.mark.asyncio
async def test_return_book(test_client: AsyncClient, db_session, seed_db):
    _, books, *__ = seed_db
    serial_number = books[0].serial_number
    response = await test_client.post(f"/books/{serial_number}/return")
    assert response.status_code == 200

    result = await db_session.execute(
        select(Borrowing).where(
            Borrowing.book_serial == serial_number, Borrowing.returned_at is None
        )
    )
    borrowing = result.scalar_one_or_none()
    # no active borrowings for that book
    assert borrowing is None


@pytest.mark.asyncio
async def test_return_book_for_not_borrowed_book_returns_404(
    test_client: AsyncClient, db_session, seed_db
):
    _, books, *__ = seed_db
    serial_number = books[-1].serial_number
    response = await test_client.post(f"/books/{serial_number}/return")
    assert response.status_code == 404
    assert response.json()["detail"] == "Active booking for this book not found"
