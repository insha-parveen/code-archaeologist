import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ast_parser import parse_functions
from app.services.wtf_scorer import score_file
from app.services.fossil_detector import detect_fossils
from app.services.story_generator import generate_story
from app.services.llm_analyzer import (
    analyze_all_functions,
    generate_code_story,
    LLMServiceError,
)
from app.services.universal_parser import (
    parse_functions_universal,
    detect_fossils_universal,
)
from app.services.language_detector import (
    get_language, is_python, is_supported, SUPPORTED_EXTENSIONS
)
from app.services.cache import file_cache, make_file_cache_key
router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 1 * 1024 * 1024
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename

    if not is_supported(filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: "
                   f"{', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    content_bytes = await file.read()

    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File too large. Max 1MB."
        )

    try:
        source_code = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="File must be UTF-8 encoded."
        )

    # Check file cache first
    cache_key    = make_file_cache_key(source_code)
    cached_result = file_cache.get(cache_key)

    if cached_result:
        logger.info("File cache hit for %s", filename)
        # Update filename in cached result — same code, different filename
        cached_result = {**cached_result, "filename": filename}
        cached_result["cached"] = True
        return cached_result

    # Cache miss — run full analysis
    logger.info("File cache miss for %s — running full analysis", filename)
    language = get_language(filename)

    try:
        if is_python(filename):
            functions = parse_functions(source_code)
            fossils   = detect_fossils(source_code)
        else:
            functions = parse_functions_universal(source_code, language)
            fossils   = detect_fossils_universal(source_code, language)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {str(e)}")

    wtf = score_file(functions) if functions else {
        "functions": [], "top_cursed": [],
        "average_wtf": 0, "total_functions": 0
    }

    llm_results = analyze_all_functions(source_code, wtf["functions"])

    for fn in wtf["functions"]:
        result = llm_results.get(fn["name"], {})
        fn["summary"]     = result.get("summary", "No summary available.")
        fn["refactoring"] = result.get("refactoring", None)

    for fn in wtf["top_cursed"]:
        result = llm_results.get(fn["name"], {})
        fn["summary"]     = result.get("summary", "No summary available.")
        fn["refactoring"] = result.get("refactoring", None)

    llm_narrative = generate_code_story(filename, wtf, fossils)
    rule_story    = generate_story(source_code, wtf, fossils)

    story = {
        "narrative":         llm_narrative or rule_story["narrative"],
        "chapters":          rule_story["chapters"],
        "development_style": rule_story["development_style"],
    }

    response = {
        "filename":    filename,
        "language":    language,
        "line_count":  len(source_code.splitlines()),
        "source_code": source_code,
        "fossils":     fossils,
        "wtf_analysis": wtf,
        "story":       story,
        "cached":      False,
    }

    # Store in cache — 1 hour TTL
    file_cache.set(cache_key, response, ttl_seconds=3600)

    return response

