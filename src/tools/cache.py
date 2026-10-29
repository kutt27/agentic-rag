"""
Caching layer with mtime-based invalidation.

LRU cache that automatically invalidates when files change on disk.
"""

import functools
import os
from pathlib import Path
from typing import Optional, TypeVar

from src.config import settings
from src.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class FileCache:
    """LRU cache with mtime-based invalidation for file contents."""

    def __init__(self, maxsize: int = 128):
        self._cache: dict[str, tuple[str, float]] = {}
        self._maxsize = maxsize

    def get(self, path: str) -> Optional[str]:
        """Get cached content if present and up-to-date."""
        if path not in self._cache:
            return None

        content, cached_mtime = self._cache[path]
        try:
            current_mtime = os.path.getmtime(path)
            if current_mtime > cached_mtime:
                del self._cache[path]
                logger.info(f"cache: invalidated {path}")
                return None
        except OSError:
            del self._cache[path]
            return None

        return content

    def set(self, path: str, content: str) -> None:
        """Cache content with current mtime."""
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return

        if len(self._cache) >= self._maxsize:
            oldest = min(self._cache.items(), key=lambda x: x[1][1])
            del self._cache[oldest[0]]
            logger.info(f"cache: evicted {oldest[0]}")

        self._cache[path] = (content, mtime)
        logger.info(f"cache: stored {path}")

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("cache: cleared")


_file_cache = FileCache(maxsize=64)


def cached_read_file(path: str) -> str:
    """Read file with LRU caching."""
    notes_dir = settings.notes_dir
    target = (notes_dir / path).resolve()

    if not target.is_relative_to(notes_dir):
        return f"Error: path {path!r} is outside the notes directory."

    cache_key = str(target)

    cached = _file_cache.get(cache_key)
    if cached is not None:
        logger.info(f"cache: hit {path}")
        return cached

    content = target.read_text(encoding="utf-8")
    _file_cache.set(cache_key, content)
    return content


def cached_grep(pattern: str, max_results: int = 30) -> list[str]:
    """Grep with cached file reads."""
    import re

    notes_dir = settings.notes_dir
    rx = re.compile(pattern, re.IGNORECASE)
    hits: list[str] = []

    files = list(notes_dir.rglob("*.md"))

    for file in files:
        content = cached_read_file(str(file.relative_to(notes_dir)))
        if content.startswith("Error:"):
            continue

        rel = file.relative_to(notes_dir)
        for i, line in enumerate(content.splitlines(), start=1):
            if rx.search(line):
                hits.append(f"{rel}:{i}: {line.strip()}")
                if len(hits) >= max_results:
                    return hits

    return hits


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {"entries": len(_file_cache._cache), "maxsize": _file_cache._maxsize}


if __name__ == "__main__":
    print("Testing cached tools...")

    print("\n1. First read (cache miss):")
    content = cached_read_file("01-engineering-handbook.md")
    print(f"  Read {len(content)} chars")

    print("\n2. Second read (cache hit):")
    content2 = cached_read_file("01-engineering-handbook.md")
    print(f"  Read {len(content2)} chars")

    print(f"\nCache stats: {get_cache_stats()}")

    print("\n3. Grep with cache:")
    hits = cached_grep("connection")
    print(f"  Found {len(hits)} hits")