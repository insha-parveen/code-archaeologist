import re
import ast


# --- Signal detection patterns ---

PANIC_NAME_PATTERNS = [
    r"fix.*final", r"final.*fix", r"new.*new", r"v\d+",
    r"_final", r"_last", r"_real", r"_actual",
    r"dont.*touch", r"do.*not.*touch", r"please.*work"
]

PANIC_COMMENT_PATTERNS = [
    r"#\s*(HACK|XXX|WORKAROUND|DO NOT TOUCH|DON'T TOUCH|FIXME|WTF|WHY)",
    r"#\s*(i don't know|no idea|not sure why|magic|somehow)",
    r"#\s*(please|just|literally|actually|basically)\s+work",
]

TODO_PATTERNS = [
    r"#\s*(TODO|FIXME|TBD|TO DO|TO-DO)",
]

EXPLORATORY_NAME_PATTERNS = [
    r"^(test|temp|tmp|foo|bar|baz|debug|trial|try)",
    r"_(temp|tmp|old|backup|unused|deprecated)$",
]

MATURE_SIGNALS = [
    r"\"\"\"",          # Has docstring
    r"->",              # Has return type hint
    r":\s*(int|str|float|bool|list|dict|tuple|set)",  # Has type hints
]


def generate_story(source_code: str, wtf_analysis: dict, fossils: dict) -> dict:
    """
    Main entry point. Analyzes the source code and returns
    a structured story with chapters and a narrative summary.
    """
    lines = source_code.splitlines()

    # Collect all signals from the file
    signals = _collect_signals(source_code, lines, wtf_analysis, fossils)

    # Group signals into chapters
    chapters = _build_chapters(signals, wtf_analysis)

    # Write the overall narrative
    narrative = _write_narrative(chapters, signals)

    return {
        "narrative": narrative,
        "chapters": chapters,
        "signals": signals,
        "development_style": _classify_style(signals),
    }


def _collect_signals(
    source_code: str,
    lines: list[str],
    wtf_analysis: dict,
    fossils: dict
) -> dict:
    """
    Scan the entire file for story signals.
    Returns a structured dict of everything we found.
    """
    signals = {
        "panic_names": [],
        "panic_comments": [],
        "todos": [],
        "exploratory_names": [],
        "mature_functions": [],
        "has_docstrings": 0,
        "has_type_hints": 0,
        "total_todos": 0,
        "total_hacks": 0,
        "avg_wtf": wtf_analysis.get("average_wtf", 0),
        "total_fossils": fossils.get("total_fossils", 0),
    }

    # Scan each line for comment patterns
    for i, line in enumerate(lines, start=1):
        stripped = line.strip().lower()

        for pattern in PANIC_COMMENT_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                signals["panic_comments"].append({
                    "line": i,
                    "content": line.strip()
                })
                signals["total_hacks"] += 1
                break

        for pattern in TODO_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                signals["todos"].append({
                    "line": i,
                    "content": line.strip()
                })
                signals["total_todos"] += 1
                break

    # Scan function names for patterns
    for fn in wtf_analysis.get("functions", []):
        name = fn["name"].lower()

        # Check for panic naming
        for pattern in PANIC_NAME_PATTERNS:
            if re.search(pattern, name):
                signals["panic_names"].append(fn["name"])
                break

        # Check for exploratory naming
        for pattern in EXPLORATORY_NAME_PATTERNS:
            if re.search(pattern, name):
                signals["exploratory_names"].append(fn["name"])
                break

    # Check for mature signals in source
    if '"""' in source_code or "'''" in source_code:
        signals["has_docstrings"] = source_code.count('"""') // 2
    if "->" in source_code:
        signals["has_type_hints"] += source_code.count("->")
    if ": int" in source_code or ": str" in source_code:
        signals["has_type_hints"] += 1

    # Identify mature functions — low WTF + has docstring
    for fn in wtf_analysis.get("functions", []):
        if fn["wtf_score"] < 20:
            signals["mature_functions"].append(fn["name"])

    return signals


def _build_chapters(signals: dict, wtf_analysis: dict) -> list[dict]:
    """
    Each chapter represents a distinct phase of development
    visible in the code. We build chapters from evidence.
    """
    chapters = []
    functions = wtf_analysis.get("functions", [])

    # Chapter: Early Exploration
    if signals["exploratory_names"] or signals["total_fossils"] > 2:
        evidence = []
        if signals["exploratory_names"]:
            evidence.append(f"Exploratory function names: {', '.join(signals['exploratory_names'])}")
        if signals["total_fossils"] > 2:
            evidence.append(f"{signals['total_fossils']} dead code artifacts found — signs of trial and error")
        chapters.append({
            "title": "Early Exploration",
            "icon": "🌱",
            "description": "The codebase shows signs of initial, exploratory development. "
                           "Functions were tried, abandoned, and left behind.",
            "evidence": evidence,
            "severity": "low"
        })

    # Chapter: Panic-Driven Development
    if signals["panic_names"] or signals["total_hacks"] > 0:
        evidence = []
        if signals["panic_names"]:
            evidence.append(f"Panic-named functions: {', '.join(signals['panic_names'])}")
        if signals["total_hacks"] > 0:
            evidence.append(f"{signals['total_hacks']} HACK/WORKAROUND comment(s) found")
        if signals["avg_wtf"] > 60:
            evidence.append(f"Average WTF score of {signals['avg_wtf']} — code written under pressure")
        chapters.append({
            "title": "Panic-Driven Development",
            "icon": "🔥",
            "description": "Clear signs of deadline pressure. Functions were patched rather than "
                           "designed, and comments suggest the developer knew it was messy.",
            "evidence": evidence,
            "severity": "high"
        })

    # Chapter: Incomplete Work
    if signals["total_todos"] > 0:
        evidence = [f"{signals['total_todos']} TODO/FIXME comment(s) left unresolved"]
        for todo in signals["todos"][:3]:  # Show max 3
            evidence.append(f"Line {todo['line']}: {todo['content']}")
        chapters.append({
            "title": "Unfinished Business",
            "icon": "📋",
            "description": "The developer left notes about work that was never completed. "
                           "These TODOs represent known gaps in the implementation.",
            "evidence": evidence,
            "severity": "medium"
        })

    # Chapter: High Complexity Period
    high_wtf_fns = [f for f in functions if f["wtf_score"] >= 70]
    if high_wtf_fns:
        evidence = []
        for fn in high_wtf_fns[:3]:
            evidence.append(f"{fn['name']}() — WTF score {fn['wtf_score']}: {fn['reasons'][0] if fn['reasons'] else ''}")
        chapters.append({
            "title": "The Complexity Spiral",
            "icon": "🌀",
            "description": "Certain functions grew beyond their original purpose — "
                           "accumulating branches, nesting, and magic numbers over time.",
            "evidence": evidence,
            "severity": "high"
        })

    # Chapter: Maturity / Clean Code
    if signals["mature_functions"] or signals["has_docstrings"] > 0 or signals["has_type_hints"] > 0:
        evidence = []
        if signals["mature_functions"]:
            evidence.append(f"Clean functions: {', '.join(signals['mature_functions'])}")
        if signals["has_docstrings"] > 0:
            evidence.append(f"{signals['has_docstrings']} docstring(s) found — developer was being thoughtful")
        if signals["has_type_hints"] > 0:
            evidence.append(f"Type hints present — signs of a more careful, mature implementation")
        chapters.append({
            "title": "Signs of Maturity",
            "icon": "✨",
            "description": "Not all is lost. Parts of this codebase show clean naming, "
                           "documentation, and structured thinking.",
            "evidence": evidence,
            "severity": "positive"
        })

    # If no chapters were generated — the code is surprisingly clean
    if not chapters:
        chapters.append({
            "title": "Surprisingly Clean",
            "icon": "🏆",
            "description": "This codebase shows no major red flags. "
                           "Either it was written carefully, or it has been well maintained.",
            "evidence": ["Low average WTF score", "No panic patterns detected"],
            "severity": "positive"
        })

    return chapters


def _write_narrative(chapters: list[dict], signals: dict) -> str:
    """
    Write a 2-3 sentence plain English summary of the
    codebase's overall story.
    """
    avg_wtf = signals["avg_wtf"]
    total_fossils = signals["total_fossils"]
    chapter_titles = [c["title"] for c in chapters]

    # Build narrative from what we found
    parts = []

    if avg_wtf >= 70:
        parts.append("This codebase tells a story of pressure and urgency — "
                     "functions were written fast and never revisited.")
    elif avg_wtf >= 40:
        parts.append("This codebase shows a mixed history — "
                     "some careful work alongside rushed patches.")
    else:
        parts.append("This codebase appears relatively well-maintained "
                     "with signs of thoughtful development.")

    if total_fossils > 3:
        parts.append(f"With {total_fossils} dead code artifacts, "
                     "there are clear signs of iterative trial-and-error development.")
    elif total_fossils > 0:
        parts.append(f"{total_fossils} fossil(s) remain from earlier versions — "
                     "small traces of the code's evolution.")

    if "Panic-Driven Development" in chapter_titles:
        parts.append("The presence of HACK comments and panic-named functions "
                     "suggests at least one deadline-driven sprint.")
    elif "Signs of Maturity" in chapter_titles:
        parts.append("The cleaner sections suggest the developer grew more "
                     "confident and deliberate over time.")

    return " ".join(parts)


def _classify_style(signals: dict) -> str:
    """
    Give the overall codebase a single development style label.
    """
    avg_wtf = signals["avg_wtf"]
    has_panic = bool(signals["panic_names"] or signals["total_hacks"] > 0)
    has_todos = signals["total_todos"] > 0
    is_mature = bool(signals["mature_functions"]) and signals["has_docstrings"] > 0

    if avg_wtf >= 70 and has_panic:
        return "Deadline Survivor"
    if avg_wtf >= 50 and has_todos:
        return "Work In Progress"
    if avg_wtf < 20 and is_mature:
        return "Clean & Intentional"
    if signals["total_fossils"] > 3:
        return "Iterative Explorer"
    if has_panic:
        return "Patched Together"
    return "Mixed History"
