"""
Local file tools with async I/O for better performance.

Uses asyncio.to_thread for blocking file operations.
"""

import asyncio
import re
from pathlib import Path
from typing import Optional

from src.config import settings
from src.logging import get_logger

logger = get_logger(__name__)


async def list_files_async(pattern: str = "*.md") -> list[str]:
    """List markdown files in notes directory - async version."""
    notes_dir = settings.notes_dir

    def _list() -> list[str]:
        return sorted(str(p.relative_to(notes_dir)) for p in notes_dir.glob(pattern) if p.is_file())

    return await asyncio.to_thread(_list)


async def read_file_async(path: str, offset: int = 1, limit: Optional[int] = None) -> str:
    """Read a file with async I/O. Supports bounded ranges."""
    if limit is None:
        limit = settings.read_max_lines

    notes_dir = settings.notes_dir

    def _read() -> str:
        target = (notes_dir / path).resolve()
        if not target.is_relative_to(notes_dir):
            raise ValueError(f"Path {path} is outside the notes directory")

        lines = target.read_text(encoding="utf-8").splitlines()
        end = min(offset + limit - 1, len(lines))
        excerpt = lines[offset - 1 : end]

        if not excerpt:
            return f"No lines found. {path} has {len(lines)} lines."
        return "\n".join(f"{i}: {line}" for i, line in enumerate(excerpt, start=offset))

    return await asyncio.to_thread(_read)


async def grep_async(pattern: str, max_results: Optional[int] = None) -> list[str]:
    """Search files with async I/O - parallel file reads."""
    if max_results is None:
        max_results = settings.grep_max_results

    notes_dir = settings.notes_dir
    rx = re.compile(pattern, re.IGNORECASE)

    async def search_file(file: Path) -> list[str]:
        def _search() -> list[str]:
            hits = []
            for i, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1):
                if rx.search(line):
                    rel = file.relative_to(notes_dir)
                    hits.append(f"{rel}:{i}: {line.strip()}")
                    if len(hits) >= max_results:
                        return hits
            return hits

        return await asyncio.to_thread(_search)

    files = list(notes_dir.rglob("*.md"))
    results = await asyncio.gather(*[search_file(f) for f in files])

    hits = []
    for result in results:
        hits.extend(result)
        if len(hits) >= max_results:
            return hits[:max_results]

    return hits


if __name__ == "__main__":
    import asyncio

    async def main():
        print("Testing async tools...")

        print("\n1. list_files_async:")
        files = await list_files_async()
        print(f"  Found {len(files)} files")

        print("\n2. grep_async('connection'):")
        hits = await grep_async("connection")
        for hit in hits[:5]:
            print(f"  {hit}")

        print("\n3. read_file_async:")
        content = await read_file_async("01-engineering-handbook.md", limit=5)
        print(content)

    asyncio.run(main())