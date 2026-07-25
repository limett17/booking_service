import os

os.environ["SECRET_KEY"] = "TEST_SECRET_KEY_FOR_PYTEST_ONLY_SUPER_LONG"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from datetime import time

import database
import models
from main import app

test_engine = create_async_engine(os.environ["DATABASE_URL"])
TestSessionMaker = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def client():
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

    async with TestSessionMaker() as session:
        async with session.begin():
            room1 = models.RoomModel(id=1, name="Тестовая Альфа")
            room2 = models.RoomModel(id=2, name="Тестовая Бета")
            session.add_all([room1, room2])
            await session.flush()

            slot1 = models.SlotModel(id=1, room_id=1, start_time=time(9, 0), end_time=time(11, 0))
            slot2 = models.SlotModel(id=2, room_id=1, start_time=time(11, 0), end_time=time(13, 0))
            session.add_all([slot1, slot2])

    async def override_get_db():
        async with TestSessionMaker() as session:
            yield session

    app.dependency_overrides[database.get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


