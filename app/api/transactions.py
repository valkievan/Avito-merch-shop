from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.schemas.transaction import SendCoinRequest
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.cache import redis_cache
from app.db.session import get_db
from app.models.models import User
from app.models.models import Transaction
from sqlalchemy import select

router = APIRouter()

@router.post("/sendCoin")
async def send_coin(
    request: SendCoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.coins < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    if current_user.username == request.toUser:
        raise HTTPException(status_code=400, detail="Cannot send coins to yourself")
    
    recipient = await db.execute(
        select(User).where(User.username == request.toUser)
    )
    recipient = recipient.scalar_one_or_none()
    
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    current_user.coins -= request.amount
    recipient.coins += request.amount
    
    transaction = Transaction(
        from_user_id=current_user.id,
        to_user_id=recipient.id,
        amount=request.amount
    )
    
    db.add(transaction)
    await db.commit()
    
    await redis_cache.delete(f"user_info:{current_user.id}")
    await redis_cache.delete(f"user_info:{recipient.id}")
    
    return {"message": "Coins sent successfully"}
