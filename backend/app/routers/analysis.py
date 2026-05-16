from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.fossil_detector import detect_fossils
from app.services.ast_parser import parse_functions
from app.services.wtf_scorer import score_file

router = APIRouter()


class CodePayload(BaseModel):
    source_code: str
    filename: str


@router.post("/analysis/full")
def full_analysis(payload: CodePayload):
    """
    Runs all analysis on source code sent as JSON.
    This is what the frontend will call after uploading.
    """
    source = payload.source_code

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

    return {
        "filename": payload.filename,
        "fossils": fossils,
        "wtf_analysis": wtf,
    }