# orchestrator/pp2_client.py
import io
import asyncio
import time
import yaml
import os
from datetime import datetime
import httpx
from db.mongo import get_db
from uuid import uuid4
from typing import List, Dict, Any

CONF_PATH = os.getenv("PP2_REGISTRY", "conf/registry.yaml")

def load_roster():
    with open(CONF_PATH, "r") as f:
        conf = yaml.safe_load(f)
    return conf.get("pp2", [])

async def _call_verify(client: httpx.AsyncClient, entry: Dict, img_bytes: bytes, timeout: float):
    t0 = time.perf_counter()
    try:
        files = {"image": ("img.jpg", img_bytes, "image/jpeg")}
        resp = await client.post(entry["endpoint_verify"], files=files)
        latency = (time.perf_counter() - t0) * 1000
        return entry, resp, latency, None
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        return entry, None, latency, e

async def verify_all(request_id: str, img_bytes: bytes, timeout=2.0):
    roster = load_roster()
    results = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        tasks = [_call_verify(client, r, img_bytes, timeout) for r in roster if r.get("active", True)]
        for coro in asyncio.as_completed(tasks, timeout=timeout+0.5):
            try:
                entry, resp, latency, exc = await coro
            except Exception as e:
                # generic timeout for a task
                entry, resp, latency, exc = None, None, None, e
            results.append((entry, resp, latency, exc))
    # log each service call
    await asyncio.gather(*[log_service_call(request_id, e, r, l, ex) for (e,r,l,ex) in results if e is not None])
    return results

async def log_service_call(request_id, entry, resp, latency_ms, exc):
    db = await get_db()
    doc = {
        "request_id": request_id,
        "ts": datetime.utcnow(),
        "service_type": "pp2",
        "service_name": entry["name"],
        "endpoint": entry["endpoint_verify"],
        "latency_ms": round(latency_ms or 0, 2),
        "status_code": getattr(resp, "status_code", None),
        "timeout": isinstance(exc, httpx.ReadTimeout) or (resp is None and exc is not None),
        "error": str(exc) if exc else None,
        "result": None
    }
    # attempt to parse JSON result
    try:
        if resp is not None and resp.headers.get("content-type","").startswith("application/json"):
            doc["result"] = resp.json()
    except Exception:
        doc["result"] = None
    await db.service_logs.insert_one(doc)
