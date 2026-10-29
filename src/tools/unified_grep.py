"""
Unified grep using ripgrep for local + S3.

Uses ripgrep for local files (fast) and falls back to S3 for remote.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from src.config import settings
from src.logging import get_logger
from src.tools.s3_tools import S3Source

logger = get_logger(__name__)


def _ripgrep_install_hint() -> str:
    """Return the most relevant ripgrep install command for this OS."""
    import platform
    system = platform.system()
    if system == "Darwin":
        return "Install with `brew install ripgrep`."
    if system == "Windows":
        return "Install with `winget install BurntSushi.ripgrep.MSVC`."
    return "Install with `sudo apt-get install ripgrep`."


def _is_ripgrep_available() -> bool:
    """Check if ripgrep is installed."""
    return shutil.which("rg") is not None


def grep_local(
    pattern: str,
    max_results: Optional[int] = None,
    context: int = 0,
) -> str:
    """Grep local files using ripgrep."""
    if not _is_ripgrep_available():
        return f"Error: ripgrep ('rg') is not installed. {_ripgrep_install_hint()}"

    if max_results is None:
        max_results = settings.grep_max_results

    cmd = [
        "rg", "--line-number", "--no-heading", "--ignore-case", "--no-config",
        "--sortr=modified", "--max-count", str(max_results), "--glob", "*.md",
        *(["--context", str(context)] if context > 0 else []),
        "--", pattern, ".",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=settings.notes_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=settings.grep_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return f"Error: grep timed out after {settings.grep_timeout_seconds}s."

    if result.returncode == 2:
        return f"Error: invalid pattern {pattern!r}: {result.stderr.strip()}"

    if not result.stdout.strip():
        return f"No matches found for pattern: {pattern}"

    return result.stdout


def grep_s3(pattern: str, max_results: int = 30) -> str:
    """Grep S3 files."""
    s3_source = S3Source()
    return s3_source.grep(pattern, max_results)


def grep(
    pattern: str,
    max_results: Optional[int] = None,
    context: int = 0,
    source: str = "auto",
) -> str:
    """Unified grep across sources."""
    if source == "local":
        return grep_local(pattern, max_results, context)

    if source == "s3":
        return grep_s3(pattern, max_results)

    if not settings.verify_s3():
        return grep_local(pattern, max_results, context)

    s3_hits = grep_s3(pattern, max_results // 2)
    local_hits = grep_local(pattern, max_results // 2, context)

    lines = []
    lines.append("--- S3 ---")
    lines.append(s3_hits)
    lines.append("\n--- Local ---")
    lines.append(local_hits)

    return "\n".join(lines)


if __name__ == "__main__":
    print("Testing unified grep...")

    print("\n1. grep_local('connection'):")
    result = grep_local("connection", max_results=5)
    print(result)

    print("\n2. grep with source='local':")
    result = grep("connection", max_results=5, source="local")
    print(result)