"""
Source router for multi-source agentic RAG.

Allows agent to choose between local filesystem and S3 at runtime.
"""

import re
from typing import Optional

from src.config import settings
from src.logging import get_logger
from src.tools.local import list_files as local_list_files, read_file as local_read_file, grep as local_grep
from src.tools.s3_tools import (
    S3Source,
    list_files as s3_list_files,
    read_file as s3_read_file,
    grep as s3_grep,
)

logger = get_logger(__name__)


class SourceRouter:
    """Route tool calls between local and S3 sources."""

    def __init__(self, default_source: str = "auto"):
        self.default_source = default_source
        self._s3_source: Optional[S3Source] = None

    @property
    def s3_source(self) -> Optional[S3Source]:
        """Lazy-load S3 source."""
        if self._s3_source is None and settings.verify_s3():
            self._s3_source = S3Source()
        return self._s3_source

    def determine_source(self, context: Optional[str] = None) -> str:
        """Determine which source to use based on context."""
        if context is None:
            context = ""

        context_lower = context.lower()

        s3_keywords = ["s3", "remote", "cloud", "bucket", "aws"]
        local_keywords = ["local", "disk", "filesystem", "notes/"]

        s3_score = sum(1 for kw in s3_keywords if kw in context_lower)
        local_score = sum(1 for kw in local_keywords if kw in context_lower)

        if settings.verify_s3() and s3_score > local_score:
            return "s3"
        elif s3_score < local_score:
            return "local"

        if settings.verify_s3() and settings.verify_notes_dir():
            return "hybrid"
        elif settings.verify_s3():
            return "s3"
        else:
            return "local"

    def list_files(self, pattern: str = "*.md", source: Optional[str] = None) -> str:
        """List files from specified or auto-detected source."""
        source = source or self.determine_source()

        if source == "local":
            files = local_list_files(pattern)
            return "\n".join(files) if files else f"No files matched pattern: {pattern}"

        if source == "s3":
            return s3_list_files(pattern)

        return s3_list_files(pattern) + "\n\n--- Local ---\n" + ("\n".join(local_list_files(pattern)))

    def read_file(
        self, path: str, offset: int = 1, limit: int = 200, source: Optional[str] = None
    ) -> str:
        """Read file from specified or auto-detected source."""
        source = source or self.determine_source(path)

        if source == "local":
            return local_read_file(path, offset, limit)

        if source == "s3":
            return s3_read_file(path, offset, limit)

        s3_content = s3_read_file(path, offset, limit)
        if not s3_content.startswith("Error:"):
            return s3_content

        return local_read_file(path, offset, limit)

    def grep(
        self, pattern: str, max_results: int = 30, source: Optional[str] = None
    ) -> str:
        """Grep from specified or auto-detected source."""
        source = source or self.determine_source()

        if source == "local":
            hits = local_grep(pattern, max_results)
            return "\n".join(hits) if hits else f"No matches found for pattern: {pattern}"

        if source == "s3":
            return s3_grep(pattern, max_results)

        s3_hits = s3_grep(pattern, max_results // 2)
        local_hits = local_grep(pattern, max_results // 2)

        return s3_hits + "\n\n--- Local ---\n" + ("\n".join(local_hits) if local_hits else "No local matches")


def list_files(pattern: str = "*.md", source: Optional[str] = None) -> str:
    """List files with source routing."""
    router = SourceRouter()
    return router.list_files(pattern, source)


def read_file(path: str, offset: int = 1, limit: int = 200, source: Optional[str] = None) -> str:
    """Read file with source routing."""
    router = SourceRouter()
    return router.read_file(path, offset, limit, source)


def grep(pattern: str, max_results: int = 30, source: Optional[str] = None) -> str:
    """Grep with source routing."""
    router = SourceRouter()
    return router.grep(pattern, max_results, source)


if __name__ == "__main__":
    router = SourceRouter()

    print("Testing source router...")

    print("\n1. List files (auto):")
    files = router.list_files()
    print(files[:500] if len(files) > 500 else files)

    print("\n2. Grep 'connection' (auto):")
    hits = router.grep("connection", max_results=5)
    print(hits[:500] if len(hits) > 500 else hits)

    print("\n3. Read file (auto):")
    content = router.read_file("notes/01-engineering-handbook.md", limit=5)
    print(content)