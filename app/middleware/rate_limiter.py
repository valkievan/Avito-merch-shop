from fastapi import Request
from app.db.cache import redis_cache
from typing import Optional, Dict
from fastapi.responses import JSONResponse


class RateLimiter:
    def __init__(
        self,
        window_seconds: int = 1,
        max_requests: Dict[str, int] = None,
        error_window_seconds: int = 60,
        max_errors: int = 50,
        ban_duration_seconds: int = 5,
    ):
        self.rate_limits = max_requests or {
            "/api/auth": 50,
            "/api/info": 200,
            "/api/buy": 100,
            "/api/sendCoin": 100
        }
        self.window_seconds = window_seconds
        self.error_window_seconds = error_window_seconds
        self.max_errors = max_errors
        self.ban_duration_seconds = ban_duration_seconds

    async def is_banned(self, client_ip: str) -> bool:
        ban_key = f"ban:{client_ip}"
        return bool(await redis_cache.get(ban_key))

    async def record_error(self, client_ip: str) -> bool:
        error_key = f"errors:{client_ip}"
        
        errors = await redis_cache.get(error_key)
        current_errors = int(errors) if errors else 0
        
        current_errors += 1
        await redis_cache.set(
            error_key,
            current_errors,
            expire=self.error_window_seconds
        )
        
        if current_errors >= self.max_errors:
            ban_key = f"ban:{client_ip}"
            await redis_cache.set(
                ban_key,
                "1",
                expire=self.ban_duration_seconds
            )
            return True
        return False

    async def check_rate_limit(
        self,
        endpoint: str,
        client_ip: str
    ) -> Optional[int]:
        rate_limit = None
        for path, limit in self.rate_limits.items():
            if endpoint.startswith(path):
                rate_limit = limit
                break
        
        if not rate_limit:
            return None
        
        key = f"ratelimit:{endpoint}:{client_ip}"
        
        try:
            current_count = await redis_cache.get(key)
            if not current_count:
                await redis_cache.set(key, 1, expire=self.window_seconds)
                return rate_limit - 1
            
            count = int(current_count)
            if count >= rate_limit:
                return 0
            
            await redis_cache.set(key, count + 1, expire=self.window_seconds)
            return rate_limit - (count + 1)
        except:
            return rate_limit

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host

        if await self.is_banned(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many errors. Please try again later."}
            )
        
        remaining = await self.check_rate_limit(request.url.path, client_ip)
        if remaining is not None and remaining < 0:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        
        response = await call_next(request)

        if response.status_code >= 500:
            should_ban = await self.record_error(client_ip)
            if should_ban:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many errors. Please try again later."}
                )
        
        return response
    