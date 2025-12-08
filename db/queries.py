# db/queries.py
from datetime import datetime, timedelta
from bson.son import SON

async def decisions_agg(db, days=7):
    since = datetime.utcnow() - timedelta(days=days)
    pipeline = [
        {"$match": {"ts": {"$gte": since}}},
        {"$group": {"_id": "$decision", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    cursor = db.access_logs.aggregate(pipeline)
    res = []
    async for doc in cursor:
        res.append(doc)
    return res

# implement p50/p95 by route, services etc similarly using aggregation
