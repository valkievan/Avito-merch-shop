import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User


pytestmark = pytest.mark.asyncio

async def test_create_recipient(db_session: AsyncSession) -> User:
    recipient = User(
        username="newuser",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LedYQNB8UHUHzh/Ue",
        coins=1000
    )
    db_session.add(recipient)
    await db_session.commit()
    return recipient

async def test_send_coins_success(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    await test_create_recipient(db_session)
    
    response = await authorized_client.post("/api/sendCoin", json={
        "toUser": "newuser",
        "amount": 100
    })
    
    assert response.status_code == 200
    
    async with db_session.begin():
        result = await db_session.execute(
            text("SELECT coins FROM users WHERE username = 'testuser'")
        )
        sender_coins = result.scalar()
        assert sender_coins == 900

        result = await db_session.execute(
            text("SELECT coins FROM users WHERE username = 'newuser'")
        )
        recipient_coins = result.scalar()
        assert recipient_coins == 1100

async def test_send_coins_insufficient_funds(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    await test_create_recipient(db_session)
    
    response = await authorized_client.post("/api/sendCoin", json={
        "toUser": "newuser",
        "amount": 2000
    })
    
    assert response.status_code == 400
    assert "Insufficient coins" in response.json()["detail"]

async def test_send_coins_invalid_recipient(authorized_client: AsyncClient):
    response = await authorized_client.post("/api/sendCoin", json={
        "toUser": "nonexistent",
        "amount": 100
    })
    
    assert response.status_code == 404
    assert "Recipient not found" in response.json()["detail"]

async def test_send_coins_yourself(authorized_client: AsyncClient):
    response = await authorized_client.post("/api/sendCoin", json={
        "toUser": "testuser",
        "amount": 50
    })
    
    assert response.status_code == 400
    assert "Cannot send coins to yourself" in response.json()["detail"]

async def test_send_coins_negative_amount(authorized_client: AsyncClient):
    response = await authorized_client.post("/api/sendCoin", json={
        "toUser": "newuser",
        "amount": -100
    })
    
    assert response.status_code == 422
    