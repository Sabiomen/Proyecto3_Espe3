# orchestrator/fuse.py
from statistics import mean
from typing import List, Tuple

def decide_identity(results: List[Tuple[dict, object, float, object]], global_threshold=0.75, margin=0.15):
    """
    results: list of tuples (entry, resp, latency, exc)
    - entry: roster entry
    - resp: httpx.Response or None
    - exc: exception or None

    Return: decision, identity, candidates
    """
    candidates = []
    for entry, resp, latency, exc in results:
        if resp is None or exc:
            continue
        try:
            js = resp.json() if resp.headers.get("content-type","").startswith("application/json") else {}
        except Exception:
            js = {}
        score = (js.get("score") if isinstance(js.get("score"), (int,float)) else None) or (js.get("confidence") if isinstance(js.get("confidence"), (int,float)) else None)
        if score is None:
            continue
        candidates.append({"name": entry["name"], "score": float(score)})

    # sort by score desc
    candidates.sort(key=lambda x: x["score"], reverse=True)
    if not candidates:
        return "unknown", None, []
    top = candidates[0]
    if top["score"] >= global_threshold:
        # check margin to next
        second_score = candidates[1]["score"] if len(candidates) > 1 else 0.0
        if (top["score"] - second_score) >= margin:
            return "identified", top, candidates
        else:
            return "ambiguous", None, candidates
    else:
        return "unknown", None, candidates