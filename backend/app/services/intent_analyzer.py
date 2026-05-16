import ast
import re


def analyze_intent(source_code: str, function_names: list[str]) -> dict[str, str]:
    """
    Main entry point. Returns a dict of function_name -> summary.
    Uses rule-based AST analysis — no model download required.
    """
    results = {}
    for name in function_names:
        func_source = _extract_function_source(source_code, name)
        if func_source is None:
            results[name] = "Could not extract function source."
            continue
        try:
            results[name] = _infer_intent(func_source, name)
        except Exception:
            results[name] = f"Could not analyze {name}."
    return results


def _extract_function_source(source_code: str, func_name: str) -> str | None:
    """Extract source lines for a specific function using AST."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return None

    lines = source_code.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    return None


def _infer_intent(func_source: str, func_name: str) -> str:
    """
    Infer what a function does from:
    - Its name (words split by underscores)
    - Its argument names
    - Keywords found in the body
    - Return type hints if present
    - Docstring if present
    """
    try:
        tree = ast.parse(func_source)
    except SyntaxError:
        return f"Possibly a utility function named '{func_name}'."

    func_node = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)),
        None
    )
    if func_node is None:
        return f"Function '{func_name}' could not be parsed."

    # 1. If it has a docstring, use it directly — best signal
    docstring = ast.get_docstring(func_node)
    if docstring:
        first_line = docstring.strip().splitlines()[0]
        return first_line

    # 2. Decompose function name into intent words
    name_words = _split_name(func_name)

    # 3. Collect argument names
    args = [arg.arg for arg in func_node.args.args]

    # 4. Collect string/name keywords from the body
    body_keywords = _extract_body_keywords(func_node)

    # 5. Check return annotation
    return_hint = ""
    if func_node.returns:
        return_hint = ast.unparse(func_node.returns)

    # 6. Build the summary from signals
    return _build_summary(func_name, name_words, args, body_keywords, return_hint)


def _split_name(name: str) -> list[str]:
    """Split snake_case or camelCase into words."""
    # snake_case
    words = name.split("_")
    # filter empty strings and short noise words
    return [w.lower() for w in words if len(w) > 1]


def _extract_body_keywords(func_node: ast.FunctionDef) -> list[str]:
    """
    Pull meaningful string constants, attribute names, and
    called function names from the body — these hint at intent.
    """
    keywords = []

    for node in ast.walk(func_node):
        # String constants like "email", "password", "user"
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if len(node.value) > 2:
                keywords.append(node.value.lower())

        # Called function names: open(), print(), len(), etc.
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                keywords.append(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                keywords.append(node.func.attr.lower())

        # Attribute access: obj.email, user.name, etc.
        if isinstance(node, ast.Attribute):
            keywords.append(node.attr.lower())

    return list(set(keywords))


def _build_summary(
    func_name: str,
    name_words: list[str],
    args: list[str],
    body_keywords: list[str],
    return_hint: str
) -> str:
    """
    Combine all signals into a readable plain English sentence.
    Uses a priority-ordered set of pattern rules.
    """
    all_signals = name_words + args + body_keywords
    signals = [s.lower() for s in all_signals]

    # --- Pattern rules ordered by specificity ---

    # Auth / security
    if any(w in signals for w in ["login", "auth", "authenticate", "password", "token", "jwt"]):
        return f"Handles authentication or login logic, likely validating credentials."

    # User management
    if any(w in signals for w in ["user", "account", "profile", "register", "signup"]):
        return f"Manages user data or account operations."

    # File operations
    if any(w in signals for w in ["file", "read", "write", "open", "save", "path", "load"]):
        return f"Performs file reading or writing operations."

    # Database
    if any(w in signals for w in ["db", "database", "query", "insert", "select", "fetch", "sql"]):
        return f"Executes a database query or data retrieval operation."

    # Calculation / math
    if any(w in signals for w in ["calc", "compute", "sum", "total", "score", "average", "mean", "multiply", "divide"]):
        subject = _find_subject(name_words, args)
        return f"Calculates or computes {subject}."

    # Validation
    if any(w in signals for w in ["valid", "validate", "check", "verify", "is", "has", "assert"]):
        subject = _find_subject(name_words, args)
        return f"Validates or checks {subject}."

    # Formatting / conversion
    if any(w in signals for w in ["format", "convert", "parse", "encode", "decode", "serialize", "transform"]):
        subject = _find_subject(name_words, args)
        return f"Formats or converts {subject} into a different representation."

    # Sending / notifications
    if any(w in signals for w in ["send", "email", "notify", "alert", "message", "post", "request"]):
        return f"Sends a message, notification, or external request."

    # Search / filter
    if any(w in signals for w in ["search", "find", "filter", "get", "fetch", "retrieve", "lookup"]):
        subject = _find_subject(name_words, args)
        return f"Retrieves or searches for {subject}."

    # Deletion
    if any(w in signals for w in ["delete", "remove", "clear", "reset", "clean"]):
        subject = _find_subject(name_words, args)
        return f"Deletes or removes {subject}."

    # Update / set
    if any(w in signals for w in ["update", "set", "edit", "modify", "change", "patch"]):
        subject = _find_subject(name_words, args)
        return f"Updates or modifies {subject}."

    # Generation / creation
    if any(w in signals for w in ["create", "generate", "make", "build", "new", "init", "setup"]):
        subject = _find_subject(name_words, args)
        return f"Creates or generates {subject}."

    # Return type hints give us extra signal
    if return_hint == "bool":
        return f"Returns a boolean — likely a condition check on '{func_name}'."
    if return_hint == "str":
        return f"Produces and returns a string result."
    if return_hint in ("int", "float"):
        return f"Computes and returns a numeric value."
    if return_hint.startswith("list"):
        return f"Collects and returns a list of results."

    # Greeting / display
    if any(w in signals for w in ["greet", "hello", "welcome", "display", "show", "print", "render"]):
        return f"Displays or outputs information to the user."

    # Generic fallback — at least tell them what we know from the name
    if name_words:
        readable = " ".join(name_words)
        if args:
            readable_args = ", ".join(args[:3])
            return f"Appears to {readable} using {readable_args} — intent unclear without context."
        return f"Appears to {readable} — possibly a utility or helper function."

    return f"Purpose of '{func_name}' is unclear — consider adding a docstring."

def _find_subject(name_words: list[str], args: list[str]) -> str:
    """
    Try to identify what the function is operating on —
    the 'subject' of the action.
    """
    # Skip common verb words to find the noun
    VERBS = {"get", "set", "calc", "compute", "check", "find",
              "validate", "update", "create", "delete", "is", "has"}

    subject_words = [w for w in name_words if w not in VERBS]

    if subject_words:
        return " ".join(subject_words)

    # Fall back to argument names
    meaningful_args = [a for a in args if a not in ("self", "cls") and len(a) > 1]
    if meaningful_args:
        return meaningful_args[0]

    return "the input data"