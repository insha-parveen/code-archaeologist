from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.github_fetcher import fetch_from_github, GitHubFetchError
from app.services.ast_parser import parse_functions
from app.services.wtf_scorer import score_file
from app.services.fossil_detector import detect_fossils
from app.services.story_generator import generate_story
from app.services.llm_analyzer import analyze_all_functions, generate_code_story
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_LINES_FOR_ANALYSIS = 800


class GithubRequest(BaseModel):
    url: str


def _analyze_source(source_code: str, filename: str) -> dict:
    """
    Run complete analysis pipeline on a single file.
    Raises plain Exception on failure — never HTTPException.
    HTTPException is only for the router layer, not service layer.
    """
    lines         = source_code.splitlines()
    was_truncated = False

    # Truncate large files
    if len(lines) > MAX_LINES_FOR_ANALYSIS:
        logger.warning(
            "File %s has %d lines, truncating to %d",
            filename, len(lines), MAX_LINES_FOR_ANALYSIS
        )
        source_code   = "\n".join(lines[:MAX_LINES_FOR_ANALYSIS])
        was_truncated = True

    # Parse — never crash the whole request on one file failure
    functions = []
    fossils   = {
        "unused_functions":      [],
        "unused_variables":      [],
        "commented_code_blocks": [],
        "total_fossils":         0,
        "fossil_free":           True,
    }

    try:
        functions = parse_functions(source_code)
    except Exception as e:
        logger.warning("AST parse failed for %s: %s", filename, e)
        # Continue with empty functions — still show fossils and story

    try:
        fossils = detect_fossils(source_code)
    except Exception as e:
        logger.warning("Fossil detection failed for %s: %s", filename, e)

    # WTF scoring
    wtf = score_file(functions) if functions else {
        "functions":      [],
        "top_cursed":     [],
        "average_wtf":    0,
        "total_functions": 0,
    }

    # LLM analysis — limit to 10 functions to avoid rate limits
    llm_results = {}
    functions_for_llm = wtf["functions"][:10]

    if functions_for_llm:
        try:
            llm_results = analyze_all_functions(
                source_code, functions_for_llm
            )
        except Exception as e:
            logger.warning(
                "LLM analysis failed for %s: %s", filename, e
            )

    # Attach LLM results
    for fn in wtf["functions"]:
        result = llm_results.get(fn["name"], {})
        fn["summary"]     = result.get("summary", "No summary available.")
        fn["refactoring"] = result.get("refactoring", None)

    for fn in wtf["top_cursed"]:
        result = llm_results.get(fn["name"], {})
        fn["summary"]     = result.get("summary", "No summary available.")
        fn["refactoring"] = result.get("refactoring", None)

    # Story generation
    llm_narrative = None
    try:
        llm_narrative = generate_code_story(filename, wtf, fossils)
    except Exception as e:
        logger.warning("Story generation failed for %s: %s", filename, e)

    rule_story = generate_story(source_code, wtf, fossils)

    story = {
        "narrative":         llm_narrative or rule_story["narrative"],
        "chapters":          rule_story["chapters"],
        "development_style": rule_story["development_style"],
    }

    return {
        "filename":       filename,
        "language":       _detect_language(filename),
        "line_count":     len(lines),
        "truncated":      was_truncated,
        "analyzed_lines": min(len(lines), MAX_LINES_FOR_ANALYSIS),
        "source_code":    source_code,
        "fossils":        fossils,
        "wtf_analysis":   wtf,
        "story":          story,
    }


def _detect_language(filename: str) -> str:
    """Simple language detection from extension."""
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C",
        ".cs": "C#", ".rb": "Ruby", ".php": "PHP",
        ".kt": "Kotlin", ".swift": "Swift",
    }
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext_map.get(ext, "Unknown")


@router.post("/github")
def analyze_github_url(request: GithubRequest):
    """
    Fetch and analyze files from a GitHub URL.
    Single file → returns one result.
    Repo URL    → returns array of results.
    """
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="GitHub URL cannot be empty."
        )

    # Fetch files from GitHub
    try:
        files = fetch_from_github(url)
    except GitHubFetchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error fetching from GitHub")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error fetching from GitHub: {str(e)}"
        )

    results = []
    errors  = []

    for file in files:
        try:
            result = _analyze_source(file.source_code, file.filename)
            result["github_path"] = file.path
            results.append(result)
            logger.info(
                "Successfully analyzed %s (%d lines)",
                file.filename, result["line_count"]
            )
        except Exception as e:
            logger.exception("Failed to analyze %s", file.path)
            errors.append({
                "file":  file.path,
                "error": str(e)
            })

    # If nothing succeeded, give a helpful error
    if not results:
        error_details = "; ".join(
            f"{e['file']}: {e['error']}" for e in errors
        )
        raise HTTPException(
            status_code=422,
            detail=f"Could not analyze any files. Details: {error_details}"
        )

    return {
        "source":      "github",
        "url":         url,
        "total_files": len(results),
        "results":     results,
        "errors":      errors,
    }
