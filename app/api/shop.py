from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.core.security import get_current_user
from app.core.config import MERCH_PRICES
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.cache import redis_cache
from app.models.models import User, Inventory

router = APIRouter()

@router.get("/buy/{item}")
async def buy_item(
    item: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if item not in MERCH_PRICES:
        raise HTTPException(status_code=404, detail="Invalid item")
    
    price = MERCH_PRICES[item]
    if current_user.coins < price:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    current_user.coins -= price
    
    result = await db.execute(
        select(Inventory).where(
            Inventory.user_id == current_user.id,
            Inventory.item_name == item
        )
    )
    inventory_item = result.scalar_one_or_none()
    
    if inventory_item:
        inventory_item.quantity += 1
    else:
        inventory_item = Inventory(
            user_id=current_user.id,
            item_name=item,
            quantity=1
        )
        db.add(inventory_item)
    
    await db.commit()
    
    cache_key = f"user_info:{current_user.id}"
    await redis_cache.delete(cache_key)
    
    return {"message": "Item purchased successfully"}
