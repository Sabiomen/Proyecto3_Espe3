# api/app.py
import os
import base64
from fastapi import FastAPI, File, Form, UploadFile, Header, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from uuid import uuid4
from time import perf_counter
from datetime import datetime
import hashlib
import asyncio

from db.mongo import get_db
from orchestrator.pp2_client import verify_all
from orchestrator.pp1_client import ask_normativa
from orchestrator.fuse import decide_identity

app = FastAPI(title="UFRO MCP ORCHESTRATOR")

THRESHOLD = float(os.getenv("THRESHOLD", "0.75"))
MARGIN = float(os.getenv("MARGIN", "0.15"))
PP2_TIMEOUT = float(os.getenv("PP2_TIMEOUT", "2.0"))
GLOBAL_TIMEOUT = float(os.getenv("GLOBAL_TIMEOUT", "5.0"))
MAX_IMAGE_MB = int(os.getenv("MAX_IMAGE_MB", "5"))



@app.post("/identify-and-answer")
async def identify_and_answer(
    request: Request,
    image: UploadFile = File(...),
    question: str = Form(None),
    x_user_id: str = Header(None),
    x_user_type: str = Header("external"),
    authorization: str = Header(None),
):
    # basic validations
    if image.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="file must be image")
    content = await image.read()
    if len(content) > MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="image too large")
    # request id and timing
    request_id = str(uuid4())
    t0 = perf_counter()
    db = await get_db()

    # compute hash (store only hash & ts)
    image_hash = hashlib.sha256(content).hexdigest()

    # trigger PP2 calls in parallel
    pp2_task = asyncio.create_task(verify_all(request_id, content, timeout=PP2_TIMEOUT))
    # optional PP1 depends on decision; we will wait for PP2 then conditionally call PP1
    try:
        pp2_results = await asyncio.wait_for(pp2_task, timeout=GLOBAL_TIMEOUT)
    except asyncio.TimeoutError:
        # log and return partial
        await db.access_logs.insert_one({
            "request_id": request_id,
            "ts": datetime.utcnow(),
            "route": "/identify-and-answer",
            "user": {"id": x_user_id, "type": x_user_type},
            "input": {"has_image": True, "has_question": bool(question), "image_hash": image_hash, "size_bytes": len(content)},
            "decision": "unknown",
            "identity": None,
            "timing_ms": round((perf_counter()-t0)*1000,2),
            "status_code": 504,
            "errors": "pp2_global_timeout",
            "pp2_summary": {"queried": None, "timeouts": None},
            "pp1_used": False
        })
        raise HTTPException(status_code=504, detail="PP2 calls timed out")

    decision, identity, candidates = decide_identity(pp2_results, global_threshold=THRESHOLD, margin=MARGIN)

    normativa_answer = None
    if question and decision == "identified":
        # call PP1
        pp1_result = await ask_normativa(request_id, question)
        normativa_answer = pp1_result

    # build response
    t_total = round((perf_counter()-t0)*1000,2)
    resp = {
        "decision": decision,
        "identity": identity,
        "candidates": candidates,
        "normativa_answer": normativa_answer,
        "timing_ms": t_total,
        "request_id": request_id
    }

    # summarize pp2 stats
    queried = len([r for r in pp2_results if r[0] is not None])
    timeouts = len([1 for r in pp2_results if r[3] is not None])
    await db.access_logs.insert_one({
        "request_id": request_id,
        "ts": datetime.utcnow(),
        "route": "/identify-and-answer",
        "user": {"id": x_user_id, "type": x_user_type},
        "input": {"has_image": True, "has_question": bool(question), "image_hash": image_hash, "size_bytes": len(content), "image_hash_ts": datetime.utcnow()},
        "decision": decision,
        "identity": identity,
        "timing_ms": t_total,
        "status_code": 200,
        "errors": None,
        "pp2_summary": {"queried": queried, "timeouts": timeouts},
        "pp1_used": bool(question)
    })
    return JSONResponse(status_code=200, content=resp)

@app.get("/healthz")
async def healthz():
    db = await get_db()
    try:
        # ping a lightweight command
        await db.command("ping")
        ok = True
    except Exception:
        ok = False
    return {"status":"ok" if ok else "fail", "pp2_count": None}

# --- Metrics endpoints minimal examples (expand in db/queries.py) ---
@app.get("/metrics/decisions")
async def metrics_decisions(days: int = 7):
    from db.queries import decisions_agg
    db = await get_db()
    return await decisions_agg(db, days)
