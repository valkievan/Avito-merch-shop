from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, info, shop, transactions
from app.core.config import settings
from app.middleware.rate_limiter import RateLimiter

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(RateLimiter(
    max_requests={
        "/api/auth": 50,
        "/api/info": 2000,
        "/api/buy": 100,
        "/api/sendCoin": 100,
    },
    window_seconds=1,
    error_window_seconds=60,
    max_errors=10,
    ban_duration_seconds=10
))

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(info.router, prefix="/api", tags=["info"])
app.include_router(shop.router, prefix="/api", tags=["shop"])
app.include_router(transactions.router, prefix="/api", tags=["transactions"])
