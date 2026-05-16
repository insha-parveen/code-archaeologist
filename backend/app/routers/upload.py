from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ast_parser import parse_functions
from app.services.wtf_scorer import score_file
from app.services.fossil_detector import detect_fossils

router = APIRouter()

ALLOWED_EXTENSIONS = {".py"}
MAX_FILE_SIZE = 1 * 1024 * 1024


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Only .py files are supported.")

    content_bytes = await file.read()

    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 1MB.")

    try:
        source_code = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    # Parse and score
    try:
        functions = parse_functions(source_code)
        fossils = detect_fossils(source_code)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    wtf = score_file(functions) if functions else {
        "functions": [],
        "top_cursed": [],
        "average_wtf": 0,
        "total_functions": 0
    }

    return {
        "filename": filename,
        "line_count": len(source_code.splitlines()),
        "source_code": source_code,   # we'll need this on the frontend
        "fossils": fossils,
        "wtf_analysis": wtf,
    }