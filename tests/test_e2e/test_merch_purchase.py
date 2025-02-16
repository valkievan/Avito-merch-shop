import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import MERCH_PRICES

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

class TestMerchPurchaseFlow:
    async def test_full_purchase_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        register_response = await client.post("/api/auth", json={
            "username": "buyer_user",
            "password": "secure_pass123"
        })
        assert register_response.status_code == 200
        token = register_response.json()["token"]
        
        client.headers["Authorization"] = f"Bearer {token}"
        
        initial_info_response = await client.get("/api/info")
        assert initial_info_response.status_code == 200
        initial_info = initial_info_response.json()
        assert len(initial_info["inventory"]) == 0
        
        purchases = [
            ("powerbank", MERCH_PRICES["powerbank"]),
            ("umbrella", MERCH_PRICES["umbrella"]),
            ("hoody", MERCH_PRICES["hoody"])
        ]
        
        total_spent = 0
        for item, price in purchases:
            purchase_response = await client.get(f"/api/buy/{item}")
            assert purchase_response.status_code == 200
            total_spent += price
            
            info_response = await client.get("/api/info")
            assert info_response.status_code == 200
            current_info = info_response.json()
            assert current_info["coins"] == 1000 - total_spent
            
            inventory = current_info["inventory"]
            assert any(
                item_info["type"] == item and item_info["quantity"] > 0 
                for item_info in inventory
            )
        
        expensive_item = "pink-hoody"
        remaining_balance = 1000 - total_spent
        assert MERCH_PRICES[expensive_item] > remaining_balance
        
        failed_purchase_response = await client.get(f"/api/buy/{expensive_item}")
        assert failed_purchase_response.status_code == 400
        assert "Insufficient coins" in failed_purchase_response.json()["detail"]
        
        final_info_response = await client.get("/api/info")
        assert final_info_response.status_code == 200
        final_info = final_info_response.json()
        
        assert final_info["coins"] == 1000 - total_spent
        
        final_inventory = final_info["inventory"]
        for item, _ in purchases:
            item_in_inventory = next(
                (i for i in final_inventory if i["type"] == item),
                None
            )
            assert item_in_inventory is not None
            assert item_in_inventory["quantity"] == 1
        
        assert len(final_inventory) == len(purchases)
        
        async with db_session.begin():
            result = await db_session.execute(
                text("SELECT coins FROM users WHERE username = 'buyer_user'")
            )
            db_coins = result.scalar()
            assert db_coins == 1000 - total_spent
            
            result = await db_session.execute(
                text(
                """
                SELECT item_name, quantity 
                FROM inventory 
                WHERE user_id = (
                    SELECT id FROM users WHERE username = 'buyer_user'
                )
                """
                )
            )
            db_inventory = result.fetchall()
            assert len(db_inventory) == len(purchases)
            
            for item, _ in purchases:
                item_exists = any(
                    row.item_name == item and row.quantity == 1 
                    for row in db_inventory
                )
                assert item_exists

    async def test_concurrent_purchase_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        register_response = await client.post("/api/auth", json={
            "username": "concurrent_buyer",
            "password": "secure_pass123"
        })
        assert register_response.status_code == 200
        token = register_response.json()["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        
        import asyncio
        
        item = "pen"
        price = MERCH_PRICES[item]
        purchase_count = 1
        
        async def make_purchase():
            return await client.get(f"/api/buy/{item}")
        
        purchase_tasks = [make_purchase() for _ in range(purchase_count)]
        responses = await asyncio.gather(*purchase_tasks)
        
        assert all(r.status_code == 200 for r in responses)
        
        final_info = (await client.get("/api/info")).json()
        
        assert final_info["coins"] == 1000 - (price * purchase_count)
        
        inventory_item = next(
            (i for i in final_info["inventory"] if i["type"] == item),
            None
        )
        assert inventory_item is not None
        assert inventory_item["quantity"] == purchase_count
        
        async with db_session.begin():
            result = await db_session.execute(
                text(
                """
                SELECT quantity 
                FROM inventory 
                WHERE user_id = (
                    SELECT id FROM users WHERE username = 'concurrent_buyer'
                ) AND item_name = :item
                """),
                {"item": item}
            )
            db_quantity = result.scalar()
            assert db_quantity == purchase_count

    async def test_purchase_with_exact_remaining_balance(
        self,
        client: AsyncClient
    ):
        register_response = await client.post("/api/auth", json={
            "username": "exact_balance_buyer",
            "password": "secure_pass123"
        })
        assert register_response.status_code == 200
        token = register_response.json()["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        
        purchase_plan = [
            ("hoody", 300),
            ("powerbank", 200),
            ("umbrella", 200),
            ("t-shirt", 80),
            ("book", 50),
            ("wallet", 50),
            ("cup", 20),
            ("pen", 10),
            ("socks", 10)
        ]
        
        for item, _ in purchase_plan:
            response = await client.get(f"/api/buy/{item}")
            assert response.status_code == 200
        
        final_info = (await client.get("/api/info")).json()
        
        assert final_info["coins"] == 80
        
        inventory = final_info["inventory"]
        for item, _ in purchase_plan:
            assert any(
                i["type"] == item and i["quantity"] == 1 
                for i in inventory
            )
        
        response = await client.get("/api/buy/powerbank")
        assert response.status_code == 400
        assert "Insufficient coins" in response.json()["detail"]
        