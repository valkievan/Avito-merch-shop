import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Inventory

pytestmark = pytest.mark.asyncio


async def test_get_info_unauthorized(client: AsyncClient):
    response = await client.get("/api/info")
    assert response.status_code == 401


async def test_get_info(authorized_client: AsyncClient, db_session: AsyncSession):
    result = await db_session.execute(
        text("SELECT id FROM users WHERE username = 'testuser'")
    )
    user_id = result.scalar()

    inventory = Inventory(
        user_id=user_id,
        item_name="pen",
        quantity=2
    )
    db_session.add(inventory)
    await db_session.commit()

    response = await authorized_client.get("/api/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "coins" in data
    assert "inventory" in data
    assert "coinHistory" in data

    await db_session.commit()
    