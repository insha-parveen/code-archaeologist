from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.fossil_detector import detect_fossils
from app.services.ast_parser import parse_functions
from app.services.wtf_scorer import score_file
from app.services.cache import file_cache, make_file_cache_key
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class CodePayload(BaseModel):
    source_code: str
    filename: str

@router.get("/cache/stats")
def cache_stats():
    """
    Returns cache hit rates and key counts.
    Useful for monitoring in production.
    """
    return {
        "file_cache": file_cache.stats(),
        "llm_cache":  llm_cache.stats(),
    }

@router.delete("/cache/clear")
def clear_cache():
    """Clear all caches. Useful during development."""
    file_cache.clear()
    llm_cache.clear()
    return {"status": "Cache cleared"}

@router.post("/analysis/full")
def full_analysis(payload: CodePayload):
    """
    Runs all analysis on source code sent as JSON.
    This is what the frontend will call after uploading.

    Checks cache first — if code was seen before, returns instantly.
    """
    source = payload.source_code

    # Check cache first
    cache_key = make_file_cache_key(source)
    cached_result = file_cache.get(cache_key)

    if cached_result:
        logger.info("File cache hit for analysis of %s", payload.filename)
        # Update filename in cached result — same code, different filename
        cached_result = {**cached_result, "filename": payload.filename}
        cached_result["cached"] = True
        return cached_result

    logger.info("File cache miss for analysis of %s — running full analysis", payload.filename)

    # Fossil detection
    try:
        fossils = detect_fossils(source)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # WTF scoring
    try:
        functions = parse_functions(source)
        wtf = score_file(functions) if functions else {
            "functions": [],
            "top_cursed": [],
            "average_wtf": 0,
            "total_functions": 0
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    response = {
        "filename": payload.filename,
        "fossils": fossils,
        "wtf_analysis": wtf,
        "cached": False,
    }

    # Store in cache — 1 hour TTL
    file_cache.set(cache_key, response, ttl_seconds=3600)

    return response
