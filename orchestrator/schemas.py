# orchestrator/schemas.py
from pydantic import BaseModel
from typing import Optional, List, Any

class Identity(BaseModel):
    name: str
    score: float

class NormativaAnswer(BaseModel):
    text: str
    citations: Optional[List[dict]] = []

class IdentifyAndAnswerResponse(BaseModel):
    decision: str
    identity: Optional[Identity] = None
    candidates: Optional[List[Identity]] = []
    normativa_answer: Optional[NormativaAnswer] = None
    timing_ms: float
    request_id: str
class HealthzResponse(BaseModel):
    status: str = "ok"