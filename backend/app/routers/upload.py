from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

ALLOWED_EXTENSIONS = {".py"}  # Only Python files for now
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB limit

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Check file extension
    filename = file.filename
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Only .py files are supported right now.")

    # 2. Read file content
    content_bytes = await file.read()

    # 3. Check file size
    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 1MB.")

    # 4. Decode bytes to string
    try:
        source_code = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

    return {
        "filename": filename,
        "size_bytes": len(content_bytes),
        "line_count": len(source_code.splitlines()),
        "preview": source_code[:300],  # First 300 characters as preview
        "status": "received"
    }