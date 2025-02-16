import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.models.models import User

async def create_test_user(
    db_session: AsyncSession,
    username: str,
    password: str = "testpass"
) -> dict:
    from app.core.security import get_password_hash
    
    password_hash = get_password_hash(password)
    user = User(
        username=username,
        password_hash=password_hash,
        coins=1000
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    access_token = create_access_token(data={"sub": username})
    return {
        "username": username,
        "token": access_token
    }

@pytest.mark.asyncio
async def test_successful_coin_transfer(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: dict
):
    recipient = await create_test_user(db_session, "recipient_user")
    
    response = await client.post(
        "/api/sendCoin",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={
            "toUser": "recipient_user",
            "amount": 500
        }
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Coins sent successfully"

    sender_info = await client.get(
        "/api/info",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert sender_info.status_code == 200
    assert sender_info.json()["coins"] == 500

    recipient_info = await client.get(
        "/api/info",
        headers={"Authorization": f"Bearer {recipient['token']}"}
    )
    assert recipient_info.status_code == 200
    assert recipient_info.json()["coins"] == 1500

    sender_history = sender_info.json()["coinHistory"]
    recipient_history = recipient_info.json()["coinHistory"]

    assert len(sender_history["sent"]) == 1
    assert sender_history["sent"][0]["toUser"] == "recipient_user"
    assert sender_history["sent"][0]["amount"] == 500

    assert len(recipient_history["received"]) == 1
    assert recipient_history["received"][0]["fromUser"] == test_user["username"]
    assert recipient_history["received"][0]["amount"] == 500

@pytest.mark.asyncio
async def test_insufficient_coins_transfer(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: dict
):
    await create_test_user(db_session, "rich_recipient")

    response = await client.post(
        "/api/sendCoin",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={
            "toUser": "rich_recipient",
            "amount": 2000
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient coins"

@pytest.mark.asyncio
async def test_self_transfer_prevention(
    client: AsyncClient,
    test_user: dict
):
    response = await client.post(
        "/api/sendCoin",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={
            "toUser": test_user["username"],
            "amount": 100
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot send coins to yourself"

@pytest.mark.asyncio
async def test_transfer_to_nonexistent_user(
    client: AsyncClient,
    test_user: dict
):
    response = await client.post(
        "/api/sendCoin",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={
            "toUser": "nonexistent_user",
            "amount": 100
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipient not found"

@pytest.mark.asyncio
async def test_multiple_transfers(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: dict
):
    user2 = await create_test_user(db_session, "user2")
    user3 = await create_test_user(db_session, "user3")

    transfers = [
        (test_user["token"], "user2", 200),
        (test_user["token"], "user3", 300),
        (user2["token"], "user3", 100)
    ]

    for token, recipient, amount in transfers:
        response = await client.post(
            "/api/sendCoin",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "toUser": recipient,
                "amount": amount
            }
        )
        assert response.status_code == 200

    async def get_user_info(token: str) -> dict:
        response = await client.get(
            "/api/info",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

    user1_info = await get_user_info(test_user["token"])
    user2_info = await get_user_info(user2["token"])
    user3_info = await get_user_info(user3["token"])

    assert user1_info["coins"] == 500
    assert user2_info["coins"] == 1100
    assert user3_info["coins"] == 1400
    