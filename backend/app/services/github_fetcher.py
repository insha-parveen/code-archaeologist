import re
import time
import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# GitHub API limits
# Unauthenticated: 60 requests/hour
# Authenticated: 5000 requests/hour
# We always use authenticated if token available

GITHUB_API_BASE  = "https://api.github.com"
GITHUB_RAW_BASE  = "https://raw.githubusercontent.com"
REQUEST_TIMEOUT  = 15.0
MAX_FILE_SIZE    = 1 * 1024 * 1024   # 1MB per file
MAX_REPO_FILES   = 20                # Max files to analyze per repo
SUPPORTED_EXTENSIONS = {".py"}
BACKOFF_SECONDS  = 2.0


@dataclass
class FetchedFile:
    filename:   str
    path:       str
    source_code: str
    size_bytes: int


class GitHubFetchError(Exception):
    """Raised when GitHub fetch fails for any known reason."""


def _get_headers() -> dict:
    """
    Build request headers.
    Uses GITHUB_TOKEN from env if available — increases rate limit
    from 60 to 5000 requests/hour.
    """
    import os
    headers = {
        "Accept":     "application/vnd.github.v3+json",
        "User-Agent": "code-archaeologist/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _make_request(url: str, attempt: int = 1) -> httpx.Response:
    """
    Make a single HTTP request with timeout and retry logic.
    Handles rate limiting with exponential backoff.
    """
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(url, headers=_get_headers())

        # Rate limit hit
        if response.status_code == 403:
            reset_time = response.headers.get("X-RateLimit-Reset")
            raise GitHubFetchError(
                "GitHub API rate limit exceeded. "
                "Add a GITHUB_TOKEN to your .env file for higher limits. "
                f"Resets at timestamp: {reset_time}"
            )

        # Not found
        if response.status_code == 404:
            raise GitHubFetchError(
                "Repository or file not found. "
                "Check the URL is correct and the repo is public."
            )

        # Other errors — retry up to 3 times
        if response.status_code >= 500:
            if attempt < 3:
                logger.warning(
                    "GitHub API error %d, retrying attempt %d",
                    response.status_code, attempt + 1
                )
                time.sleep(BACKOFF_SECONDS * attempt)
                return _make_request(url, attempt + 1)
            raise GitHubFetchError(
                f"GitHub API returned {response.status_code}. "
                "Try again shortly."
            )

        response.raise_for_status()
        return response

    except httpx.TimeoutException:
        if attempt < 3:
            time.sleep(BACKOFF_SECONDS * attempt)
            return _make_request(url, attempt + 1)
        raise GitHubFetchError(
            "GitHub request timed out after 3 attempts. "
            "Check your internet connection."
        )

    except httpx.NetworkError as e:
        raise GitHubFetchError(f"Network error: {str(e)}")


# ── URL Parsing ────────────────────────────────────────────────────

def parse_github_url(url: str) -> dict:
    """
    Parse any GitHub URL into its components.
    Returns: {type, owner, repo, branch, path}

    Handles all these formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/blob/main/path/to/file.py
    - https://github.com/owner/repo/tree/main/folder
    """
    url = url.strip().rstrip("/")

    # Pattern: file URL with blob
    # https://github.com/owner/repo/blob/branch/path/to/file.py
    file_pattern = re.compile(
        r"https?://github\.com/"
        r"(?P<owner>[^/]+)/"
        r"(?P<repo>[^/]+)/"
        r"blob/"
        r"(?P<branch>[^/]+)/"
        r"(?P<path>.+)"
    )

    # Pattern: repo or tree URL
    # https://github.com/owner/repo
    # https://github.com/owner/repo/tree/branch/folder
    repo_pattern = re.compile(
        r"https?://github\.com/"
        r"(?P<owner>[^/]+)/"
        r"(?P<repo>[^/]+)"
        r"(?:/tree/(?P<branch>[^/]+)(?:/(?P<folder>.+))?)?"
    )

    file_match = file_pattern.match(url)
    if file_match:
        path = file_match.group("path")
        ext  = "." + path.rsplit(".", 1)[-1] if "." in path else ""

        if ext not in SUPPORTED_EXTENSIONS:
            raise GitHubFetchError(
                f"Unsupported file type '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        return {
            "type":   "file",
            "owner":  file_match.group("owner"),
            "repo":   file_match.group("repo"),
            "branch": file_match.group("branch"),
            "path":   path,
        }

    repo_match = repo_pattern.match(url)
    if repo_match:
        return {
            "type":   "repo",
            "owner":  repo_match.group("owner"),
            "repo":   repo_match.group("repo"),
            "branch": repo_match.group("branch") or "main",
            "folder": repo_match.group("folder") or "",
        }

    raise GitHubFetchError(
        "Invalid GitHub URL. Paste a file URL "
        "(ending in .py) or a repository URL."
    )


# ── Single File Fetch ──────────────────────────────────────────────

def fetch_file(owner: str, repo: str,
               branch: str, path: str) -> FetchedFile:
    """
    Fetch a single file. Tries main branch first,
    falls back to master if 404.
    """
    def _try_fetch(b: str) -> httpx.Response:
        raw_url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{b}/{path}"
        logger.info("Fetching: %s", raw_url)
        return _make_request(raw_url), raw_url

    # Try the given branch first
    try:
        response, url = _try_fetch(branch)
    except GitHubFetchError as e:
        # If 404 and branch was main, try master
        if "not found" in str(e).lower() and branch == "main":
            try:
                response, url = _try_fetch("master")
            except GitHubFetchError:
                raise GitHubFetchError(
                    f"File not found on branches 'main' or 'master'. "
                    f"Check the URL path is correct: {path}"
                )
        else:
            raise

    content_bytes = response.content

    if len(content_bytes) > MAX_FILE_SIZE:
        raise GitHubFetchError(
            f"File too large ({len(content_bytes) // 1024}KB). "
            f"Max size is {MAX_FILE_SIZE // 1024}KB."
        )

    try:
        source_code = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise GitHubFetchError(
            "File appears to be binary or non-UTF-8 encoded."
        )

    filename = path.split("/")[-1]
    return FetchedFile(
        filename=filename,
        path=path,
        source_code=source_code,
        size_bytes=len(content_bytes),
    )

# ── Repository File Tree ───────────────────────────────────────────

def fetch_repo_files(owner: str, repo: str,
                     branch: str, folder: str = "") -> list[FetchedFile]:
    """
    Fetch all supported files from a repository.

    Uses GitHub Trees API with recursive=1 to get the full
    file tree in ONE request — much more efficient than
    traversing directories one by one.
    """
    # First get the default branch if we guessed wrong
    branch = _resolve_branch(owner, repo, branch)

    # Get full tree in one API call
    tree_url = (
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/"
        f"git/trees/{branch}?recursive=1"
    )

    logger.info("Fetching repo tree: %s", tree_url)
    response = _make_request(tree_url)
    tree_data = response.json()

    if tree_data.get("truncated"):
        logger.warning(
            "Repository tree was truncated — repo may be too large. "
            "Only partial results will be shown."
        )

    # Filter to supported files only
    all_items = tree_data.get("tree", [])
    py_files  = [
        item for item in all_items
        if item["type"] == "blob"
        and _is_supported(item["path"])
        and (not folder or item["path"].startswith(folder))
        and item.get("size", 0) <= MAX_FILE_SIZE
    ]

    if not py_files:
        raise GitHubFetchError(
            f"No supported files found in this repository. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # Limit to MAX_REPO_FILES to avoid rate limits
    if len(py_files) > MAX_REPO_FILES:
        logger.warning(
            "Repo has %d files, limiting to %d",
            len(py_files), MAX_REPO_FILES
        )
        py_files = py_files[:MAX_REPO_FILES]

    # Fetch each file — with small delay to respect rate limits
    fetched = []
    for i, item in enumerate(py_files):
        try:
            file = fetch_file(owner, repo, branch, item["path"])
            fetched.append(file)
            # Small delay between requests to be a good API citizen
            if i < len(py_files) - 1:
                time.sleep(0.1)
        except GitHubFetchError as e:
            logger.warning("Skipping %s: %s", item["path"], e)
            continue

    if not fetched:
        raise GitHubFetchError(
            "Could not fetch any files from this repository."
        )

    return fetched


def _resolve_branch(owner: str, repo: str, branch: str) -> str:
    """
    Get the default branch from GitHub API.
    Falls back gracefully if API call fails.
    """
    repo_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    try:
        response = _make_request(repo_url)
        return response.json().get("default_branch", branch)
    except GitHubFetchError as e:
        logger.warning(
            "Could not resolve branch for %s/%s: %s. "
            "Using '%s' as default.",
            owner, repo, e, branch
        )
        # Try common defaults
        return branch


def _is_supported(path: str) -> bool:
    """Check if a file path has a supported extension."""
    ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
    return ext in SUPPORTED_EXTENSIONS


# ── Main Entry Point ───────────────────────────────────────────────

def fetch_from_github(url: str) -> list[FetchedFile]:
    """
    Main entry point. Accepts any GitHub URL and returns
    a list of FetchedFile objects ready for analysis.

    Single file URL → returns list with one item
    Repo URL        → returns list with up to MAX_REPO_FILES items
    """
    parsed = parse_github_url(url)

    if parsed["type"] == "file":
        file = fetch_file(
            parsed["owner"],
            parsed["repo"],
            parsed["branch"],
            parsed["path"],
        )
        return [file]

    else:
        return fetch_repo_files(
            parsed["owner"],
            parsed["repo"],
            parsed["branch"],
            parsed.get("folder", ""),
        )
