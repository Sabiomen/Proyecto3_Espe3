import os
import motor.motor_asyncio
from functools import lru_cache

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ufro_master")

_client = None

async def get_client():
    global _client
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    return _client

async def get_db():
    client = await get_client()
    return client[DB_NAME]