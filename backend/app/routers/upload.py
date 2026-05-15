from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ast_parser import parse_functions
from app.services.wtf_scorer import score_file

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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not functions:
        raise HTTPException(status_code=422, detail="No functions found in this file.")

    result = score_file(functions)

    return {
        "filename": filename,
        "line_count": len(source_code.splitlines()),
        "analysis": result
    }