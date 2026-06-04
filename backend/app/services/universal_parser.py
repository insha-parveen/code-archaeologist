import json
import logging
import re
import time
from app.services.llm_analyzer import _call_llm, LLMServiceError

logger = logging.getLogger(__name__)

MAX_CHARS_PER_CHUNK     = 6000
MAX_FUNCTIONS_PER_BATCH = 5
MAX_CHUNKS              = 5
CHUNK_OVERLAP           = 200


class ParserError(Exception):
    pass


def parse_functions_universal(
    source_code: str,
    language: str
) -> list[dict]:
    """
    Universal LLM-based function parser for non-Python files.
    Falls back to regex if LLM fails.
    """
    if not source_code.strip():
        return []

    if len(source_code) <= MAX_CHARS_PER_CHUNK:
        return _parse_chunk(source_code, language, offset_lines=0)

    logger.info(
        "File too large for single pass (%d chars), chunking...",
        len(source_code)
    )
    return _parse_large_file(source_code, language)


def _parse_large_file(source_code: str, language: str) -> list[dict]:
    lines           = source_code.splitlines()
    total_lines     = len(lines)
    functions       = []
    seen_names      = set()
    avg_chars       = max(1, len(source_code) // total_lines)
    lines_per_chunk = MAX_CHARS_PER_CHUNK // avg_chars
    overlap_lines   = CHUNK_OVERLAP // avg_chars
    chunk_num       = 0
    start_line      = 0

    while start_line < total_lines and chunk_num < MAX_CHUNKS:
        end_line     = min(start_line + lines_per_chunk, total_lines)
        chunk_source = "\n".join(lines[start_line:end_line])

        logger.info(
            "Parsing chunk %d: lines %d-%d",
            chunk_num + 1, start_line + 1, end_line
        )

        chunk_fns = _parse_chunk(
            chunk_source, language, offset_lines=start_line
        )

        for fn in chunk_fns:
            if fn["name"] not in seen_names:
                seen_names.add(fn["name"])
                functions.append(fn)

        start_line = end_line - overlap_lines
        chunk_num += 1

    if chunk_num >= MAX_CHUNKS:
        logger.warning(
            "File exceeded max chunks (%d). Analysis may be incomplete.",
            MAX_CHUNKS
        )

    return functions


def _parse_chunk(
    source_code: str,
    language: str,
    offset_lines: int = 0,
    attempt: int = 1
) -> list[dict]:
    prompt = _build_parse_prompt(source_code, language)

    try:
        raw = _call_llm(prompt, max_tokens=2000)
        if not raw:
            return _regex_fallback(source_code, language, offset_lines)

        cleaned = _clean_json_response(raw)
        parsed  = json.loads(cleaned)

        if not isinstance(parsed, list):
            return _regex_fallback(source_code, language, offset_lines)

        functions = []
        for item in parsed:
            fn = _sanitize_function(item, offset_lines)
            if fn:
                functions.append(fn)

        return functions

    except json.JSONDecodeError:
        logger.warning("JSON parse failed, using regex fallback")
        return _regex_fallback(source_code, language, offset_lines)

    except LLMServiceError as e:
        error_str = str(e).lower()
        if "rate" in error_str and attempt <= 3:
            wait = 2 ** attempt
            logger.warning(
                "Rate limit hit, waiting %ds (attempt %d/3)", wait, attempt
            )
            time.sleep(wait)
            return _parse_chunk(
                source_code, language, offset_lines, attempt + 1
            )
        logger.error("LLM unavailable: %s. Using regex fallback.", e)
        return _regex_fallback(source_code, language, offset_lines)


def _build_parse_prompt(source_code: str, language: str) -> str:
    return f"""Analyze this {language} code and extract ALL function/method definitions.

Return ONLY a valid JSON array. No explanation, no markdown, no backticks.

Each object must have exactly these fields:
- "name": string — function/method name
- "line_start": integer — 1-indexed line where function starts
- "line_end": integer — 1-indexed line where function ends
- "args": array of strings — parameter names only, no types
- "max_depth": integer — maximum nesting level (0 = flat)
- "num_branches": integer — count of if/for/while/switch/try
- "has_docstring": boolean — has doc comment
- "magic_numbers": array of numbers — unexplained literals (exclude 0,1,-1,2)
- "bad_names": array of strings — cryptic names (single letters except i,j,k,x,y,z)

Code:
{source_code}

JSON array only:"""


def _clean_json_response(raw: str) -> str:
    raw = re.sub(r"```(?:json)?\s*", "", raw)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start != -1 and end > start:
        return raw[start:end]
    return raw


def _sanitize_function(item: dict, offset_lines: int = 0) -> dict | None:
    if not isinstance(item, dict):
        return None

    name = item.get("name", "")
    if not name or not isinstance(name, str):
        return None

    SKIP = {"if", "for", "while", "switch", "else",
            "try", "catch", "class", "interface"}
    if name.lower() in SKIP:
        return None

    def safe_int(val, default=0) -> int:
        try:
            return max(0, int(val))
        except (TypeError, ValueError):
            return default

    def safe_list(val) -> list:
        return val if isinstance(val, list) else []

    return {
        "name":          name.strip(),
        "line_start":    safe_int(item.get("line_start"), 1) + offset_lines,
        "line_end":      safe_int(item.get("line_end"), 1) + offset_lines,
        "args":          [str(a) for a in safe_list(item.get("args"))],
        "max_depth":     safe_int(item.get("max_depth")),
        "num_branches":  safe_int(item.get("num_branches")),
        "has_docstring": bool(item.get("has_docstring", False)),
        "magic_numbers": safe_list(item.get("magic_numbers")),
        "bad_names":     [str(b) for b in safe_list(item.get("bad_names"))],
    }


def _regex_fallback(
    source_code: str,
    language: str,
    offset_lines: int = 0
) -> list[dict]:
    logger.info("Using regex fallback parser for %s", language)

    patterns = {
        "Python":     r"^def\s+(\w+)\s*\(",
        "JavaScript": r"(?:^|\s)(?:async\s+)?function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\w+|\([^)]*\))\s*=>",
        "TypeScript": r"(?:^|\s)(?:async\s+)?function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\w+|\([^)]*\))\s*=>",
        "Java":       r"(?:public|private|protected|static|void|int|String|boolean|\s)+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{",
        "Go":         r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(",
        "Rust":       r"^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[<(]",
        "C++":        r"^[\w:]+\s+[\w:]+::(\w+)\s*\(|^(?!if|for|while|switch)[\w:]+\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{",
        "C":          r"^(?!if|for|while|switch|return)[\w]+\s+(\w+)\s*\([^)]*\)\s*\{",
        "C#":         r"(?:public|private|protected|static|override|virtual|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{",
        "Ruby":       r"^\s*def\s+(\w+)",
        "PHP":        r"(?:public|private|protected|static|\s)*function\s+(\w+)\s*\(",
        "Kotlin":     r"(?:fun\s+)(?:\w+\s+)?(\w+)\s*[(<]",
        "Swift":      r"(?:func\s+)(\w+)\s*[(<]",
    }

    pattern = patterns.get(language)
    if not pattern:
        pattern = r"(?:function|def|func|fn)\s+(\w+)\s*[(<(]"

    functions = []
    lines     = source_code.splitlines()
    seen      = set()

    SKIP = {"if", "for", "while", "switch", "else",
            "try", "catch", "return", "new"}

    for i, line in enumerate(lines, start=1):
        match = re.search(pattern, line.strip())
        if match:
            name = next(
                (g for g in match.groups() if g is not None), None
            )
            if name and name not in SKIP and name not in seen:
                seen.add(name)
                functions.append({
                    "name":          name,
                    "line_start":    i + offset_lines,
                    "line_end":      min(i + 20 + offset_lines, len(lines)),
                    "args":          [],
                    "max_depth":     0,
                    "num_branches":  0,
                    "has_docstring": False,
                    "magic_numbers": [],
                    "bad_names":     [],
                })

    return functions


def detect_fossils_universal(
    source_code: str,
    language: str
) -> dict:
    """
    Language-agnostic fossil detection using regex.
    Works for all supported languages.
    """
    lines = source_code.splitlines()

    if language in ("Python", "Ruby"):
        comment_chars = ["#"]
    else:
        comment_chars = ["//"]

    CODE_KEYWORDS = [
        "function", "def ", "func ", "fn ", "class ",
        "return", "import", "if ", "for ", "while ",
        "print(", "console.log", "var ", "let ", "const ",
        "public ", "private ", "void ", "int ", "string ",
        "System.out", "fmt.Print",
    ]

    commented_blocks = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        for cc in comment_chars:
            if stripped.startswith(cc):
                content = stripped[len(cc):].strip()
                if len(content) > 3 and any(
                    kw in content for kw in CODE_KEYWORDS
                ):
                    commented_blocks.append({
                        "line":    i,
                        "content": stripped,
                        "type":    "commented_code"
                    })
                break

    unused_functions = _find_unused_functions_regex(source_code, language)
    total = len(unused_functions) + len(commented_blocks)

    return {
        "unused_functions":      unused_functions,
        "unused_variables":      [],
        "commented_code_blocks": commented_blocks,
        "total_fossils":         total,
        "fossil_free":           total == 0,
    }


def _find_unused_functions_regex(
    source_code: str,
    language: str
) -> list[dict]:
    lines = source_code.splitlines()

    def_patterns = {
        "Python":     r"^def\s+(\w+)\s*\(",
        "JavaScript": r"^(?:async\s+)?function\s+(\w+)\s*\(",
        "TypeScript": r"^(?:async\s+)?function\s+(\w+)\s*\(",
        "Go":         r"^func\s+(\w+)\s*\(",
        "Rust":       r"^(?:pub\s+)?fn\s+(\w+)\s*[(<]",
        "Ruby":       r"^\s*def\s+(\w+)",
        "PHP":        r"^function\s+(\w+)\s*\(",
        "Kotlin":     r"^fun\s+(\w+)\s*[(<]",
        "Swift":      r"^func\s+(\w+)\s*[(<]",
    }

    pattern = def_patterns.get(language, "")
    if not pattern:
        return []

    defined = {}
    for i, line in enumerate(lines, start=1):
        match = re.search(pattern, line.strip())
        if match:
            name = match.group(1)
            defined[name] = i

    call_pattern = re.compile(r"\b(\w+)\s*\(")
    called = set()
    for line in lines:
        for match in call_pattern.finditer(line):
            called.add(match.group(1))

    unused = []
    for name, line in defined.items():
        if name not in called and not name.startswith("_"):
            unused.append({
                "name": name,
                "line": line,
                "type": "unused_function"
            })

    return unused
