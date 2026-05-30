import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

MODEL = "llama-3.1-8b-instant"


def _call_llm(prompt: str, max_tokens: int = 200) -> str | None:
    """
    Core LLM call — single responsibility function.
    All other functions in this service use this.
    If Groq changes their API or we switch providers,
    we change ONE function, not ten. DRY principle.
    """
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
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"LLM call failed: {e}")
        return None


def analyze_function_intent(func_name: str, source_code: str) -> str:
    """
    Generate a plain English summary of what a function does.
    Prompt engineering: be specific about format and length.
    """
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

    result = _call_llm(prompt, max_tokens=80)
    return result if result else f"Analysis unavailable for {func_name}."


def generate_refactoring_suggestion(
    func_name: str,
    source_code: str,
    wtf_score: int,
    reasons: list[str]
) -> str | None:
    """
    For high-WTF functions, generate a specific refactoring suggestion.
    We pass the WTF reasons so the model has context about WHY
    the code is problematic — produces more targeted suggestions.
    """
    if wtf_score < 40:
        return None

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

    result = _call_llm(prompt, max_tokens=120)
    return result


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

    return _call_llm(prompt, max_tokens=200)


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
