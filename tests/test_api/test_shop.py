import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import MERCH_PRICES

pytestmark = pytest.mark.asyncio

async def test_buy_item_success(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    item = "pen"
    initial_price = MERCH_PRICES[item]
    
    response = await authorized_client.get(f"/api/buy/{item}")
    assert response.status_code == 200
    
    result = await db_session.execute(
        text("SELECT quantity FROM inventory WHERE item_name = :item"),
        {"item": item}
    )
    quantity = result.scalar()
    assert quantity == 1
    
    result = await db_session.execute(
        text("SELECT coins FROM users WHERE username = 'testuser'")
    )
    coins = result.scalar()
    assert coins == 1000 - initial_price

async def test_buy_item_insufficient_funds(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):

    await authorized_client.get("/api/buy/pink-hoody")
    await authorized_client.get("/api/buy/pink-hoody")

    response = await authorized_client.get("/api/buy/t-shirt")
    assert response.status_code == 400
    assert "Insufficient coins" in response.json()["detail"]

async def test_buy_invalid_item(authorized_client: AsyncClient):
    response = await authorized_client.get("/api/buy/invalid-item")
    assert response.status_code == 404
    assert "Invalid item" in response.json()["detail"]

async def test_buy_multiple_same_items(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    item = "pen"
    response1 = await authorized_client.get(f"/api/buy/{item}")
    response2 = await authorized_client.get(f"/api/buy/{item}")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    result = await db_session.execute(
        text("SELECT quantity FROM inventory WHERE item_name = :item"),
        {"item": item}
    )
    quantity = result.scalar()
    assert quantity == 2
    