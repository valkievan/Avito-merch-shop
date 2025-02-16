import asyncio
import pytest_asyncio
from typing import AsyncGenerator, Dict
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.core.security import create_access_token
from app.models.models import User

TEST_DATABASE_URL = settings.POSTGRES_URL

engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> Dict[str, str]:
    from app.core.security import get_password_hash
    password = "testpass"
    password_hash = get_password_hash(password)
    
    user = User(
        username="testuser",
        password_hash=password_hash,
        coins=1000
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "username": "testuser",
        "password": password,
        "token": access_token
    }

@pytest_asyncio.fixture(scope="function")
async def authorized_client(client: AsyncClient, test_user: Dict[str, str]) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {test_user['token']}"
    return client
