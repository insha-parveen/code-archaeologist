import logging
import os
import time
from groq import (
    Groq,
    APIError,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    GroqError,
)
from app.services.cache import llm_cache, make_function_cache_key
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "Missing required environment variable GROQ_API_KEY for Groq API access. "
        "Set GROQ_API_KEY in your environment or .env file."
    )

DEFAULT_GROQ_TIMEOUT = 10.0
DEFAULT_GROQ_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 1.0

logger = logging.getLogger(__name__)

client = Groq(
    api_key=GROQ_API_KEY,
    timeout=DEFAULT_GROQ_TIMEOUT,
    max_retries=0,
)

MODEL = "llama-3.1-8b-instant"


class LLMServiceError(Exception):
    """Raised when the Groq LLM cannot produce a valid analysis."""


def _call_llm(prompt: str, max_tokens: int = 200) -> str:
    """
    Core LLM call — single responsibility function.
    All other functions in this service use this.
    If Groq changes their API or we switch providers,
    we change ONE function, not ten. DRY principle.
    """
    for attempt in range(1, DEFAULT_GROQ_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software engineer "
                                   "specializing in code analysis and review. "
                                   "Be concise, precise, and insightful."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            text = response.choices[0].message.content.strip()
            if not text:
                raise LLMServiceError("LLM returned an empty response.")
            return text

        except (APITimeoutError, APIConnectionError, RateLimitError, GroqError, APIError) as e:
            logger.error(
                "Groq LLM request failed on attempt %d/%d: %s",
                attempt,
                DEFAULT_GROQ_ATTEMPTS,
                e,
                exc_info=True,
            )
            if attempt == DEFAULT_GROQ_ATTEMPTS:
                raise LLMServiceError("Groq LLM service unavailable.") from e
            time.sleep(DEFAULT_BACKOFF_SECONDS * attempt)

        except Exception as e:
            logger.exception("Unexpected error during Groq LLM request.")
            raise LLMServiceError("Unexpected LLM service failure.") from e


def analyze_function_intent(func_name: str, source_code: str) -> str:
    """
    Generate a plain English summary.
    Cached — same function code returns instantly on repeat calls.
    """
    # Check cache first
    cache_key = make_function_cache_key(func_name, source_code)
    cached    = llm_cache.get(cache_key)
    if cached:
        logger.info("LLM cache hit for function: %s", func_name)
        return cached

    prompt = f"""Analyze this function and write ONE sentence describing its purpose.

Rules:
- One sentence only, maximum 20 words
- Focus on PURPOSE not implementation details
- If name doesn't match behavior, say so briefly
- If incomplete, say "Appears to be an incomplete [description]"
- No preamble — start directly with the description

Function: {func_name}
```
{source_code}
```"""

    try:
        result = _call_llm(prompt, max_tokens=80)
        # Store in cache — 24 hours TTL
        llm_cache.set(cache_key, result, ttl_seconds=86400)
        return result
    except LLMServiceError:
        return f"Analysis unavailable for {func_name}."


def generate_refactoring_suggestion(
    func_name: str,
    source_code: str,
    wtf_score: int,
    reasons: list[str]
) -> str | None:
    if wtf_score < 40:
        return None

    # Include wtf_score in cache key — same code with different
    # score should get different suggestion
    cache_key = make_function_cache_key(
        f"{func_name}_refactor_{wtf_score}", source_code
    )
    cached = llm_cache.get(cache_key)
    if cached:
        logger.info("LLM cache hit for refactoring: %s", func_name)
        return cached

    reasons_text = "\n".join(f"- {r}" for r in reasons)

    prompt = f"""This function has a complexity score of {wtf_score}/100.

Problems identified:
{reasons_text}

Function: {func_name}
```
{source_code}
```

Give ONE specific refactoring suggestion in 2 sentences maximum.
Be direct. Name the exact change to make. No preamble."""

    try:
        result = _call_llm(prompt, max_tokens=120)
        llm_cache.set(cache_key, result, ttl_seconds=86400)
        return result
    except LLMServiceError:
        return f"Refactoring suggestion unavailable for {func_name}."


def generate_code_story(
    filename: str,
    wtf_analysis: dict,
    fossils: dict,
) -> str | None:
    """
    Generate a narrative description of the codebase's history.
    We compress the analysis into structured context instead of
    sending raw code — this is called context compression,
    critical for token efficiency in production GenAI systems.
    """
    avg_wtf         = wtf_analysis.get("average_wtf", 0)
    total_functions = wtf_analysis.get("total_functions", 0)
    total_fossils   = fossils.get("total_fossils", 0)
    unused_fns      = len(fossils.get("unused_functions", []))
    top_cursed      = wtf_analysis.get("top_cursed", [])

    cursed_summary = "\n".join(
        f"- {f['name']}(): score {f['wtf_score']}, "
        f"issues: {', '.join(f['reasons'][:2])}"
        for f in top_cursed[:3]
    ) or "None"

    prompt = f"""You are a software archaeologist. Write a 3-sentence narrative
story about this codebase's development history based on these metrics:

File: {filename}
Functions: {total_functions}
Average complexity score: {avg_wtf}/100
Dead code artifacts: {total_fossils}
Unused functions: {unused_fns}

Most complex functions:
{cursed_summary}

Write like a detective describing a crime scene — specific, dramatic, insightful.
Synthesize the metrics into a story. Do NOT list the numbers back.
3 sentences maximum."""

    try:
        return _call_llm(prompt, max_tokens=200)
    except LLMServiceError:
        return f"Code story unavailable for {filename}."


def analyze_all_functions(
    source_code: str,
    functions: list[dict]
) -> dict[str, dict]:
    """
    Run intent analysis and refactoring suggestions
    for all functions in the file.
    We call the LLM once per function — acceptable for
    Groq's free tier of 14,400 calls/day.
    In production you'd use async calls for parallel execution.
    """
    results = {}
    lines   = source_code.splitlines()

    for fn in functions:
        name       = fn["name"]
        line_start = fn.get("line_start", 1)
        line_end   = fn.get("line_end", len(lines))

        func_source = "\n".join(lines[line_start - 1 : line_end])

        summary = analyze_function_intent(name, func_source)

        refactoring = generate_refactoring_suggestion(
            name,
            func_source,
            fn.get("wtf_score", 0),
            fn.get("reasons", [])
        )

        results[name] = {
            "summary":     summary,
            "refactoring": refactoring,
        }

    return results
