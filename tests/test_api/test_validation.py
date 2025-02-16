import asyncio
from datetime import timedelta
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


async def test_invalid_token_format(client: AsyncClient):
    client.headers["Authorization"] = "Invalid token"
    response = await client.get("/api/info")
    assert response.status_code == 401

async def test_expired_token(client: AsyncClient):
    token = create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(seconds=1)
    )
    await asyncio.sleep(2)
    
    client.headers["Authorization"] = f"Bearer {token}"
    response = await client.get("/api/info")
    assert response.status_code == 401

async def test_validation_username_format(client: AsyncClient):
    response = await client.post("/api/auth", json={
        "username": "user@#$%",
        "password": "password123"
    })
    assert response.status_code == 200

async def test_validation_coin_amount(authorized_client: AsyncClient):
    response = await authorized_client.post("/api/sendCoin", json={
        "toUser": "recipient",
        "amount": 0
    })
    assert response.status_code == 422
    
    response = await authorized_client.post("/api/sendCoin", json={
        "toUser": "recipient",
        "amount": 10.5
    })
    assert response.status_code == 422
    