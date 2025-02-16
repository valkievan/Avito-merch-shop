from typing import Any, Optional
import json
from redis.asyncio import Redis, from_url
from app.core.config import settings


class RedisCache:
    def __init__(self):
        self._redis: Optional[Redis] = None

    async def init(self):
        if not self._redis:
            self._redis = await from_url(
                str(settings.REDIS_URL),
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )

    async def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            await self.init()
        
        try:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        except json.JSONDecodeError:
            return None

    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        if not self._redis:
            await self.init()
        
        try:
            value_str = json.dumps(value)
            if expire:
                await self._redis.setex(name=key, time=expire, value=value_str)
            else:
                await self._redis.set(name=key, value=value_str)
            return True
        except (json.JSONDecodeError, Exception):
            return False

    async def delete(self, key: str) -> bool:
        if not self._redis:
            await self.init()
        
        deleted = await self._redis.delete(key)
        return deleted > 0

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None

redis_cache = RedisCache()
