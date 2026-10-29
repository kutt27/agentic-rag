"""
Local file tools with thread pool for parallel grep.

Uses concurrent.futures for parallel file processing.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from src.config import settings
from src.logging import get_logger

logger = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=8)


def list_files(pattern: str = "*.md") -> list[str]:
    """List markdown files in notes directory."""
    notes_dir = settings.notes_dir
    return sorted(str(p.relative_to(notes_dir)) for p in notes_dir.glob(pattern) if p.is_file())


def read_file(path: str, offset: int = 1, limit: Optional[int] = None) -> str:
    """Read a file with bounded ranges."""
    if limit is None:
        limit = settings.read_max_lines

    notes_dir = settings.notes_dir
    target = (notes_dir / path).resolve()

    if not target.is_relative_to(notes_dir):
        return f"Error: path {path!r} is outside the notes directory."
    if not target.exists():
        return f"Error: file not found: {path}"

    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return f"Error: {path} is not UTF-8 text."

    end = min(offset + limit - 1, len(lines))
    excerpt = lines[offset - 1 : end]

    if not excerpt:
        return f"No lines found. {path} has {len(lines)} lines."
    return "\n".join(f"{i}: {line}" for i, line in enumerate(excerpt, start=offset))


def grep(pattern: str, max_results: Optional[int] = None) -> list[str]:
    """Search files with parallel thread pool."""
    if max_results is None:
        max_results = settings.grep_max_results

    notes_dir = settings.notes_dir
    rx = re.compile(pattern, re.IGNORECASE)
    files = list(notes_dir.rglob("*.md"))

    def search_file(file: Path) -> list[str]:
        hits = []
        for i, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1):
            if rx.search(line):
                rel = file.relative_to(notes_dir)
                hits.append(f"{rel}:{i}: {line.strip()}")
                if len(hits) >= max_results:
                    return hits
        return hits

    futures = [_executor.submit(search_file, f) for f in files]
    hits = []
    for future in futures:
        hits.extend(future.result())
        if len(hits) >= max_results:
            return hits[:max_results]

    return hits