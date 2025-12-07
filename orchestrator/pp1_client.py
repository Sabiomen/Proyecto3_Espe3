# orchestrator/pp1_client.py
import os
import httpx
from datetime import datetime
from db.mongo import get_db

PP1_URL = os.getenv("PP1_URL", "http://localhost:8081/ask")

async def ask_normativa(request_id: str, question: str, timeout=5.0):
    db = await get_db()
    doc = {
        "request_id": request_id,
        "ts": datetime.utcnow(),
        "service_type": "pp1",
        "service_name": "UFRO-RAG",
        "endpoint": PP1_URL,
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            resp = await client.post(PP1_URL, json={"question": question})
        doc.update({
            "latency_ms": round(resp.elapsed.total_seconds() * 1000, 2),
            "status_code": resp.status_code,
            "timeout": False,
            "result": resp.json() if resp.headers.get("content-type","",).startswith("application/json") else None
        })
    except Exception as e:
        doc.update({
            "latency_ms": None,
            "status_code": None,
            "timeout": True,
            "error": str(e)
        })
    await db.service_logs.insert_one(doc)
    return doc.get("result")
