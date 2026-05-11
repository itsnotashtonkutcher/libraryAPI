import asyncio
from unittest.mock import patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_all_users_returns_all_users(test_client: AsyncClient, seed_db):
    users, *_ = seed_db

    response = await test_client.get("/users")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["users"]) == len(users)
    all_users_card_ids = [user["library_card_id"] for user in data["users"]]
    for user in users:
        assert user.library_card_id in all_users_card_ids


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "page, size, expected_length",
    [
        (1, 10, 4),
        (1, 4, 4),
        (2, 2, 2),
        (2, 3, 1),
        (1500, 3, 0),
    ],
)
async def test_get_all_users_pagination_for_valid_parameters(
    test_client: AsyncClient, seed_db, page, size, expected_length
):
    response = await test_client.get(f"/users?page={page}&size={size}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["users"]) == expected_length


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "page, size",
    [
        # non positive values
        (-1, 10),
        (1, -4),
        (0, 0),
        # too much on one page requested
        (10, 1000),
        # other
        ("wow", 4),
        (1.3, 4),
    ],
)
async def test_get_all_users_pagination_for_invalid_parameters_returns_422(
    test_client: AsyncClient, seed_db, page, size
):
    response = await test_client.get(f"/users?page={page}&size={size}")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_user_by_id_success(test_client: AsyncClient, seed_db):
    users, *_ = seed_db
    target_user = users[0]

    response = await test_client.get(f"/users/{target_user.library_card_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["library_card_id"] == target_user.library_card_id
    assert response.json()["name"] == target_user.name


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(
    test_client: AsyncClient, seed_db, non_existing_id
):

    response = await test_client.get(f"/users/{non_existing_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert f"User with ID {non_existing_id} not found" == response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_success(test_client: AsyncClient, seed_db, non_existing_id):
    new_user_data = {"library_card_id": non_existing_id, "name": "Tony Soprano"}

    response = await test_client.post("/users", json=new_user_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["library_card_id"] == non_existing_id


@pytest.mark.asyncio
async def test_create_user_already_exists(test_client: AsyncClient, seed_db):
    users, *_ = seed_db
    duplicate_data = {"library_card_id": users[0].library_card_id, "name": "Mr. Santa"}

    response = await test_client.post("/users", json=duplicate_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User with this ID already exists" == response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_user_not_found(
    test_client: AsyncClient, seed_db, non_existing_id
):
    response = await test_client.delete(f"/users/{non_existing_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_delete_user_no_active_borrowings_success(
    test_client: AsyncClient, seed_db
):
    users, *_ = seed_db
    user_id = users[2].library_card_id

    response = await test_client.delete(f"/users/{user_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    check = await test_client.get(f"/users/{user_id}")
    assert check.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_user_with_active_borrowings_fails_without_force(
    test_client: AsyncClient, seed_db
):
    users, _, active_borrowings, _ = seed_db
    user_id = active_borrowings[0].user_serial

    response = await test_client.delete(f"/users/{user_id}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Cannot delete user with active borrowings. Use force=true to override."
        == response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_delete_user_with_active_borrowings_force_success(
    test_client: AsyncClient, seed_db
):
    users, _, active_borrowings, _ = seed_db
    user_id = active_borrowings[0].user_serial

    response = await test_client.delete(f"/users/{user_id}?force=true")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    user_check = await test_client.get(f"/users/{user_id}")
    assert user_check.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.skip(reason="Locks does not work for this kind of async sessions.")
@pytest.mark.asyncio
async def test_concurrency_with_book_borrowing(test_client, seed_db, db_session):
    users, books, _, _ = seed_db
    user_id = users[0].library_card_id
    book_serial = books[2].serial_number
    original_execute = AsyncSession.execute

    async def mocked_execute(self, stmt, *args, **kwargs):
        result = await original_execute(self, stmt, *args, **kwargs)
        await asyncio.sleep(1.0)
        return result

    with patch.object(
        AsyncSession, "execute", autospec=True, side_effect=mocked_execute
    ):
        delete_task = asyncio.create_task(
            test_client.delete(f"/users/{user_id}?force=true")
        )
        await asyncio.sleep(0.5)

        borrow_task = asyncio.create_task(
            test_client.post(f"/books/{book_serial}/borrow/{user_id}")
        )

        delete_res, borrow_res = await asyncio.gather(delete_task, borrow_task)

    assert delete_res.status_code == status.HTTP_204_NO_CONTENT
    assert borrow_res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_active_bookings(test_client: AsyncClient, seed_db):
    users, _, borrowings, _ = seed_db
    user_id = users[1].library_card_id

    response = await test_client.get(f"/users/{user_id}/bookings")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_count = len([b for b in borrowings if b.user_serial == user_id])
    assert len(data["borrowings"]) == expected_count
    assert all(b["returned_at"] is None for b in data["borrowings"])


@pytest.mark.asyncio
async def test_get_historic_bookings(test_client: AsyncClient, seed_db):
    users, _, _, historical = seed_db
    user_id = users[0].library_card_id

    response = await test_client.get(f"/users/{user_id}/bookings/history")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_count = len([h for h in historical if h.user_serial == user_id])
    assert len(data["borrowings"]) == expected_count
    assert all(b["returned_at"] is not None for b in data["borrowings"])


@pytest.mark.asyncio
async def test_get_bookings_user_not_found(
    test_client: AsyncClient, seed_db, non_existing_id
):
    res_active = await test_client.get(f"/users/{non_existing_id}/bookings")
    res_history = await test_client.get(f"/users/{non_existing_id}/bookings/history")

    assert res_active.status_code == status.HTTP_404_NOT_FOUND
    assert res_history.status_code == status.HTTP_404_NOT_FOUND
