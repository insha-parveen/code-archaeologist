def score_function(func: dict) -> dict:
    """
    Calculate a WTF score (0-100) for a single function.
    Higher = more confusing. Based on objective heuristics.
    """
    score = 0
    reasons = []

    # 1. Deep nesting — the biggest red flag
    depth = func["max_depth"]
    if depth >= 4:
        score += 35
        reasons.append(f"Deep nesting: {depth} levels (danger zone is 3+)")
    elif depth == 3:
        score += 20
        reasons.append(f"Moderate nesting: {depth} levels")
    elif depth == 2:
        score += 8
        reasons.append(f"Some nesting: {depth} levels")

    # 2. Too many branches
    branches = func["num_branches"]
    if branches >= 6:
        score += 25
        reasons.append(f"High branch count: {branches} branches")
    elif branches >= 3:
        score += 12
        reasons.append(f"Several branches: {branches}")

    # 3. Magic numbers
    magic = func["magic_numbers"]
    if len(magic) >= 3:
        score += 20
        reasons.append(f"Multiple magic numbers: {magic}")
    elif len(magic) >= 1:
        score += 10
        reasons.append(f"Magic numbers found: {magic}")

    # 4. No docstring on a complex function
    if not func["has_docstring"] and func["num_branches"] >= 2:
        score += 10
        reasons.append("No docstring on a non-trivial function")

    # 5. Bad variable names
    bad = func["bad_names"]
    if len(bad) >= 3:
        score += 15
        reasons.append(f"Cryptic names: {bad}")
    elif len(bad) >= 1:
        score += 7
        reasons.append(f"Some cryptic names: {bad}")

    # Cap at 100
    score = min(score, 100)

    return {
        "name": func["name"],
        "line_start": func["line_start"],
        "line_end": func["line_end"],
        "wtf_score": score,
        "reasons": reasons,
        "args": func["args"],
        "max_depth": func["max_depth"],
    }


def score_file(functions: list[dict]) -> dict:
    """
    Score all functions in a file and produce a leaderboard.
    """
    scored = [score_function(f) for f in functions]

    # Sort by WTF score descending — most cursed first
    scored.sort(key=lambda f: f["wtf_score"], reverse=True)

    # File-level summary
    avg_score = sum(f["wtf_score"] for f in scored) / len(scored) if scored else 0

    return {
        "functions": scored,
        "top_cursed": scored[:5],         # Top 5 WTF leaderboard
        "average_wtf": round(avg_score, 1),
        "total_functions": len(scored),
    }