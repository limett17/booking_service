import pytest


@pytest.mark.anyio
async def test_register_user_success(client):
    response = await client.post("/auth/register", json={"username": "user1", "password": "123"})
    assert response.status_code == 201


@pytest.mark.anyio
async def test_register_duplicate_user(client):
    """Тест: Нельзя зарегистрировать пользователя с существующим username"""
    await client.post("/auth/register", json={"username": "ivan", "password": "123"})
    response = await client.post("/auth/register", json={"username": "ivan", "password": "456"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Пользователь уже существует"


@pytest.mark.anyio
async def test_login_success(client):
    """Тест: Успешное получение токена"""
    await client.post("/auth/register", json={"username": "ivan", "password": "123"})
    response = await client.post("/auth/token", data={"username": "ivan", "password": "123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.anyio
async def test_login_invalid_password(client):
    await client.post("/auth/register", json={"username": "ivan", "password": "123"})
    response = await client.post("/auth/token", data={"username": "ivan", "password": "wrong"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_rooms(client):
    """Тест: Получение списка комнат"""
    response = await client.get("/rooms")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.anyio
async def test_get_room_availability_success(client):
    """Тест: Проверка сетки слотов переговорной"""
    response = await client.get("/rooms/1/availability?booking_date=2026-07-25")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.anyio
async def test_get_room_availability_not_found(client):
    """Тест: Ошибка при поиске сетки для несуществующей комнаты"""
    response = await client.get("/rooms/999/availability?booking_date=2026-07-25")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_booking_success(client):
    """Тест: Успешное бронирование слота сотрудником"""
    await client.post("/auth/register", json={"username": "ivan", "password": "123"})
    login_res = await client.post("/auth/token", data={"username": "ivan", "password": "123"})
    token = login_res.json()["access_token"]

    response = await client.post(
        "/bookings",
        json={"slot_id": 1, "date": "2026-07-25"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201


@pytest.mark.anyio
async def test_create_booking_slot_not_found(client):
    """Тест: Попытка забронировать несуществующий слот"""
    await client.post("/auth/register", json={"username": "ivan", "password": "123"})
    login_res = await client.post("/auth/token", data={"username": "ivan", "password": "123"})
    token = login_res.json()["access_token"]

    response = await client.post(
        "/bookings",
        json={"slot_id": 999, "date": "2026-07-25"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_booking_already_booked(client):
    """Тест: Попытка забронировать уже занятый слот"""
    await client.post("/auth/register", json={"username": "ivan", "password": "123"})
    login_res = await client.post("/auth/token", data={"username": "ivan", "password": "123"})
    token = login_res.json()["access_token"]

    # Бронируем первый раз
    await client.post(
        "/bookings",
        json={"slot_id": 1, "date": "2026-07-25"},
        headers={"Authorization": f"Bearer {token}"}
    )
    # Пытаемся забронировать тот же слот на ту же дату второй раз
    response = await client.post(
        "/bookings",
        json={"slot_id": 1, "date": "2026-07-25"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_employee_cannot_delete_someone_elses_booking(client):
    await client.post("/auth/register", json={"username": "user_a", "password": "123"})
    await client.post("/auth/register", json={"username": "user_b", "password": "123"})

    login_a = await client.post("/auth/token", data={"username": "user_a", "password": "123"})
    token_a = login_a.json()["access_token"]

    booking_res = await client.post(
        "/bookings",
        json={"slot_id": 1, "date": "2026-07-25"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    booking_id = booking_res.json()["id"]

    login_b = await client.post("/auth/token", data={"username": "user_b", "password": "123"})
    token_b = login_b.json()["access_token"]

    delete_res = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert delete_res.status_code == 403


@pytest.mark.anyio
async def test_admin_can_delete_any_booking(client):
    """Тест: Администратор может удалить чужую бронь"""
    await client.post("/auth/register", json={"username": "user_a", "password": "123"})
    await client.post("/auth/register", json={"username": "boss", "password": "123", "role": "admin"})

    login_a = await client.post("/auth/token", data={"username": "user_a", "password": "123"})
    token_a = login_a.json()["access_token"]

    booking_res = await client.post(
        "/bookings",
        json={"slot_id": 1, "date": "2026-07-25"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    booking_id = booking_res.json()["id"]

    login_admin = await client.post("/auth/token", data={"username": "boss", "password": "123"})
    token_admin = login_admin.json()["access_token"]

    delete_res = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert delete_res.status_code == 204


@pytest.mark.anyio
async def test_delete_booking_not_found(client):
    """Тест: Попытка удалить несуществующее бронирование"""
    await client.post("/auth/register", json={"username": "ivan", "password": "123"})
    login_res = await client.post("/auth/token", data={"username": "ivan", "password": "123"})
    token = login_res.json()["access_token"]

    response = await client.delete(
        "/bookings/999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
