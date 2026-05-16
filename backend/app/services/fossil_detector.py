import ast
import re


def detect_fossils(source_code: str) -> dict:
    """
    Main entry point. Returns all dead code found in the file.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        raise ValueError(f"Could not parse file: {e}")

    unused_functions = _find_unused_functions(tree)
    unused_variables = _find_unused_variables(tree)
    commented_code   = _find_commented_code(source_code)

    total = len(unused_functions) + len(unused_variables) + len(commented_code)

    return {
        "unused_functions": unused_functions,
        "unused_variables": unused_variables,
        "commented_code_blocks": commented_code,
        "total_fossils": total,
        "fossil_free": total == 0
    }


def _find_unused_functions(tree: ast.AST) -> list[dict]:
    """
    Step 1: Collect all defined function names and their line numbers.
    Step 2: Collect all called function names anywhere in the file.
    Step 3: Defined - Called = Unused.
    """
    # Collect definitions
    defined = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined[node.name] = node.lineno

    # Collect calls
    called = set()
    for node in ast.walk(tree):
        # Direct calls: greet("Rahul")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            # Method calls on objects: obj.method()
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)

    # Subtract — ignore private helpers starting with _ by convention
    unused = []
    for name, line in defined.items():
        if name not in called and not name.startswith("__"):
            unused.append({
                "name": name,
                "line": line,
                "type": "unused_function"
            })

    return unused


def _find_unused_variables(tree: ast.AST) -> list[dict]:
    """
    Step 1: Collect all variable assignments per function scope.
    Step 2: Collect all variable reads in that same scope.
    Step 3: Assigned - Read = Unused.

    We check per function scope, not globally — a variable
    assigned in one function is invisible to another.
    """
    unused = []

    # Check global scope + each function independently
    scopes = [tree]
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            scopes.append(node)

    for scope in scopes:
        assigned = {}  # name -> line number
        used = set()   # names that are read

        for node in ast.walk(scope):
            # Assignments: x = 5 or a, b = 1, 2
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Don't overwrite if already tracked
                        if target.id not in assigned:
                            assigned[target.id] = node.lineno

            # Augmented assignments: x += 1 (this IS a read too)
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    used.add(node.target.id)

            # Variable reads: anywhere a Name is loaded (read)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used.add(node.id)

        # Subtract
        for name, line in assigned.items():
            if name not in used and name != "_":
                unused.append({
                    "name": name,
                    "line": line,
                    "type": "unused_variable"
                })

    return unused


def _find_commented_code(source_code: str) -> list[dict]:
    """
    Find comment lines that look like real code left behind —
    these are fossils that a developer commented out but never deleted.

    We use simple pattern matching on each line, no AST needed here
    because comments are stripped before AST parsing.
    """
    # Patterns that strongly suggest commented-out code
    CODE_PATTERNS = [
        r"#\s*(def |class |return |import |from |if |for |while |print\(|assert )",
        r"#\s*\w+\s*=\s*.+",        # assignment: # x = 5
        r"#\s*\w+\(.*\)",           # function call: # greet("Rahul")
    ]

    fossils = []
    lines = source_code.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        # Skip pure documentation comments (short, no code patterns)
        if len(stripped) < 5:
            continue
        for pattern in CODE_PATTERNS:
            if re.search(pattern, stripped):
                fossils.append({
                    "line": i,
                    "content": stripped,
                    "type": "commented_code"
                })
                break  # One match per line is enough

    return fossils