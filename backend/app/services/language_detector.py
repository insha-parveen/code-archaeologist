EXTENSION_MAP = {
    ".py":    "Python",
    ".js":    "JavaScript",
    ".jsx":   "JavaScript",
    ".ts":    "TypeScript",
    ".tsx":   "TypeScript",
    ".java":  "Java",
    ".go":    "Go",
    ".rs":    "Rust",
    ".cpp":   "C++",
    ".cc":    "C++",
    ".c":     "C",
    ".h":     "C/C++ Header",
    ".hpp":   "C++ Header",
    ".cs":    "C#",
    ".rb":    "Ruby",
    ".php":   "PHP",
    ".kt":    "Kotlin",
    ".swift": "Swift",
}

PYTHON_EXTENSIONS    = {".py"}
SUPPORTED_EXTENSIONS = set(EXTENSION_MAP.keys())


def get_language(filename: str) -> str:
    ext = _get_ext(filename)
    return EXTENSION_MAP.get(ext, "Unknown")


def is_python(filename: str) -> bool:
    return _get_ext(filename) in PYTHON_EXTENSIONS


def is_supported(filename: str) -> bool:
    return _get_ext(filename) in SUPPORTED_EXTENSIONS


def _get_ext(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()
