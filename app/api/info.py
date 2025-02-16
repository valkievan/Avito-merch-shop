from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.core.security import get_current_user
from app.schemas.info import InfoResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.cache import redis_cache
from app.models.models import User, Inventory, Transaction

router = APIRouter()

@router.get("/info", response_model=InfoResponse)
async def get_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"user_info:{current_user.id}"
    cached_data = await redis_cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    result = await db.execute(
        select(Inventory).where(Inventory.user_id == current_user.id)
    )
    inventory = result.scalars().all()
    
    result = await db.execute(
        select(Transaction, User.username.label('from_username'))
        .join(User, Transaction.from_user_id == User.id)
        .where(Transaction.to_user_id == current_user.id)
    )
    received = result.all()
    
    result = await db.execute(
        select(Transaction, User.username.label('to_username'))
        .join(User, Transaction.to_user_id == User.id)
        .where(Transaction.from_user_id == current_user.id)
    )
    sent = result.all()
    
    response = InfoResponse(
        coins=current_user.coins,
        inventory=[
            {"type": item.item_name, "quantity": item.quantity}
            for item in inventory
        ],
        coinHistory={
            "received": [
                {"fromUser": row.from_username, "amount": row.Transaction.amount}
                for row in received
            ],
            "sent": [
                {"toUser": row.to_username, "amount": row.Transaction.amount}
                for row in sent
            ]
        }
    )
    
    await redis_cache.set(cache_key, response.model_dump(), expire=300)
    return response
