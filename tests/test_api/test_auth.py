import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.asyncio

async def test_register_new_user(client: AsyncClient, db_session: AsyncSession):
    response = await client.post("/api/auth", json={
        "username": "newuser",
        "password": "password123"
    })
    
    assert response.status_code == 200
    assert "token" in response.json()
    
    async with db_session.begin():
        result = await db_session.execute(text("SELECT coins FROM users WHERE username = 'newuser'"))
        user_coins = result.scalar()
        assert user_coins == 1000

async def test_login_existing_user(client: AsyncClient, test_user: dict):
    response = await client.post("/api/auth", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    
    assert response.status_code == 200
    assert "token" in response.json()

async def test_login_wrong_password(client: AsyncClient, test_user: dict):
    response = await client.post("/api/auth", json={
        "username": test_user["username"],
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401

async def test_login_invalid_username(client: AsyncClient):
    response = await client.post("/api/auth", json={
        "username": "nonexistent",
        "password": "password123"
    })
    
    assert response.status_code == 200
    assert "token" in response.json()
    