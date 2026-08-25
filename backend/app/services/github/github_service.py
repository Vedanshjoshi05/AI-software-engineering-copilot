"""
GitHub API integration.

Equivalent to the original services/githubService.js. Fetches repository
tree/blobs via the GitHub REST API and filters down to source files
worth indexing, ignoring node_modules, .git, generated files, binaries,
lockfiles, and large files.
"""

from __future__ import annotations

import base64

import httpx

from app.core.config import settings

ALLOWED_EXTENSIONS = (
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".java",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".vue",
)

IGNORED_DIRECTORIES = (
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    ".git/",
    ".github/",
    ".claude/",
    ".codesandbox/",
    ".next/",
    "vendor/",
    "fixtures/",
    "__fixtures__/",
    "__snapshots__/",
    ".cache/",
    "tmp/",
    "temp/",
    "__tests__/",
    "tests/",
    "test/",
)

IGNORED_FILES = (
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "composer.lock",
    "tsconfig.json",
    "jsconfig.json",
    ".eslintrc.js",
    ".eslintrc.json",
    ".eslintrc.cjs",
    "eslint.config.js",
    "eslint.config.mjs",
    "babel.config.js",
    "jest.config.js",
    "jest.config.ts",
    "vite.config.js",
    "vite.config.ts",
    "webpack.config.js",
)

TEST_FILE_SUFFIXES = (
    ".test.js",
    ".test.jsx",
    ".test.ts",
    ".test.tsx",
    ".spec.js",
    ".spec.jsx",
    ".spec.ts",
    ".spec.tsx",
    "-test.js",
    "-test.jsx",
)


class GitHubApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def _github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return headers


def parse_github_url(github_url: str) -> tuple[str, str]:
    """Parse a GitHub URL into (owner, repo). Raises ValueError if invalid."""
    from urllib.parse import urlparse

    parsed = urlparse(github_url)
    parts = [p for p in parsed.path.split("/") if p]

    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL")

    owner, repo = parts[0], parts[1]
    repo = repo.removesuffix(".git")

    if not owner or not repo:
        raise ValueError("Invalid GitHub repository URL")

    return owner, repo


async def fetch_repository_metadata(
    owner: str, repo: str, client: httpx.AsyncClient | None = None
) -> dict:
    owned_client = client is None
    client = client or httpx.AsyncClient(timeout=15.0)
    try:
        response = await client.get(
            f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}",
            headers=_github_headers(),
        )
        if response.status_code == 404:
            raise GitHubApiError("GitHub repository not found or not accessible", 404)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        raise GitHubApiError(
            f"GitHub API error: {error}", error.response.status_code
        ) from error
    finally:
        if owned_client:
            await client.aclose()


async def get_repository_tree(
    owner: str, repo: str, branch: str = "main", client: httpx.AsyncClient | None = None
) -> dict:
    owned_client = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    try:
        response = await client.get(
            f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}",
            params={"recursive": "1"},
            headers=_github_headers(),
        )
        if response.status_code == 404:
            raise GitHubApiError("GitHub repository branch or tree not found", 404)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        raise GitHubApiError(
            f"GitHub API error: {error}", error.response.status_code
        ) from error
    finally:
        if owned_client:
            await client.aclose()


async def get_file_content(
    owner: str, repo: str, sha: str, client: httpx.AsyncClient | None = None
) -> str:
    owned_client = client is None
    client = client or httpx.AsyncClient(timeout=15.0)
    try:
        response = await client.get(
            f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/git/blobs/{sha}",
            headers=_github_headers(),
        )
        response.raise_for_status()
        blob = response.json()

        if not blob.get("content"):
            raise GitHubApiError("GitHub blob does not contain content")

        return base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
    except httpx.HTTPStatusError as error:
        raise GitHubApiError(
            f"GitHub API error: {error}", error.response.status_code
        ) from error
    finally:
        if owned_client:
            await client.aclose()


def filter_source_files(tree: list[dict]) -> list[dict]:
    """Keep only blobs that look like useful source code for RAG."""
    filtered = []

    for item in tree:
        if item.get("type") != "blob":
            continue

        path = item.get("path", "").lower()
        file_name = path.split("/")[-1]

        if any(file_name.endswith(suffix) for suffix in TEST_FILE_SUFFIXES):
            continue

        if any(directory in path for directory in IGNORED_DIRECTORIES):
            continue

        if file_name in IGNORED_FILES:
            continue

        if not any(path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            continue

        filtered.append(item)

    return filtered
