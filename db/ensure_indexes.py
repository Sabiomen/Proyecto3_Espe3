import asyncio
from datetime import timedelta
from db.mongo import get_db

async def main():
    db = await get_db()

    # access_logs
    await db.access_logs.create_index([("ts", -1)])
    await db.access_logs.create_index([("user.type", 1), ("ts", -1)])
    await db.access_logs.create_index([("route", 1), ("ts", -1)])
    await db.access_logs.create_index([("decision", 1), ("ts", -1)])

    # service_logs
    await db.service_logs.create_index([("service_name", 1), ("ts", -1)])
    await db.service_logs.create_index([("service_type", 1), ("ts", -1)])
    await db.service_logs.create_index([("status_code", 1), ("ts", -1)])

    # TTL: si guardas image_hash_ts (timestamp cuando se guardó), expirar hashes en 7 días:
    # (solo si usas campo input.image_hash_ts con tipo datetime)
    await db.access_logs.create_index("input.image_hash_ts", expireAfterSeconds=7243600)

    print("Índices creados.")

if name == "main":
    asyncio.run(main())