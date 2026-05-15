import ast

def parse_functions(source_code: str) -> list[dict]:
    """
    Walk the AST of a Python source file and extract
    information about every function defined in it.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        raise ValueError(f"Could not parse file: {e}")

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "args": [arg.arg for arg in node.args.args],
                "max_depth": _get_max_depth(node),
                "num_branches": _count_branches(node),
                "has_docstring": _has_docstring(node),
                "magic_numbers": _find_magic_numbers(node),
                "bad_names": _find_bad_names(node),
            })

    return functions


def _get_max_depth(node: ast.AST, current_depth: int = 0) -> int:
    """
    Recursively find the deepest nesting level inside a function.
    This is the core insight from your tree answer — you visit
    every child, and increment depth at each branching node.
    """
    NESTING_NODES = (ast.If, ast.For, ast.While, ast.Try, ast.With)

    max_d = current_depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, NESTING_NODES):
            # Going one level deeper — recurse
            child_depth = _get_max_depth(child, current_depth + 1)
            max_d = max(max_d, child_depth)
        else:
            child_depth = _get_max_depth(child, current_depth)
            max_d = max(max_d, child_depth)

    return max_d


def _count_branches(node: ast.AST) -> int:
    """Count total number of if/for/while/try branches in a function."""
    count = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
            count += 1
    return count


def _has_docstring(node: ast.FunctionDef) -> bool:
    """Check if the function has a docstring as its first statement."""
    if node.body and isinstance(node.body[0], ast.Expr):
        if isinstance(node.body[0].value, ast.Constant):
            return isinstance(node.body[0].value.value, str)
    return False


def _find_magic_numbers(node: ast.AST) -> list[int | float]:
    """
    Find numeric literals that have no explanation.
    We ignore 0 and 1 — those are almost always legitimate.
    """
    magic = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant):
            if isinstance(child.value, (int, float)):
                if child.value not in (0, 1, -1, 2):
                    magic.append(child.value)
    return magic


def _find_bad_names(node: ast.FunctionDef) -> list[str]:
    """
    Find cryptic variable and argument names — single letters
    or names under 3 characters (excluding 'i', 'j' in loops which are accepted convention).
    """
    bad = []

    # Check argument names
    for arg in node.args.args:
        name = arg.arg
        if len(name) <= 2 and name not in ("i", "j", "k", "x", "y", "z", "id"):
            bad.append(name)

    # Check variable assignments inside the function
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            name = child.id
            if len(name) <= 2 and name not in ("i", "j", "k", "x", "y", "z", "id", "_"):
                if name not in bad:
                    bad.append(name)

    return bad