from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, get_password_hash, verify_password
from app.schemas.auth import AuthRequest, AuthResponse
from app.db.session import get_db
from app.models.models import User

router = APIRouter()

@router.post("/auth", response_model=AuthResponse)
async def authenticate(auth_data: AuthRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.username == auth_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            username=auth_data.username,
            password_hash=get_password_hash(auth_data.password),
            coins=1000
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not verify_password(auth_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"token": access_token}
