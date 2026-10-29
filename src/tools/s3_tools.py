"""
S3 tools for agentic RAG.

Search tools backed by S3 instead of local filesystem.
"""

from typing import Optional

from src.config import settings
from src.logging import get_logger
from src.tools.s3 import S3Client, get_s3_client

logger = get_logger(__name__)


class S3Source:
    """S3-backed source for agentic RAG."""

    def __init__(self, bucket: Optional[str] = None):
        self.client = get_s3_client(bucket=bucket)
        self.bucket = self.client.bucket

    def list_files(self, pattern: str = "*.md") -> str:
        """List markdown files in S3 bucket."""
        prefix = ""
        if pattern != "*.md":
            prefix = pattern.replace("*", "").replace("?", "")

        keys = self.client.list_objects(prefix=prefix)

        if not keys:
            return f"No files found in S3 bucket: {self.bucket}"

        return "\n".join(keys)

    def read_file(self, key: str, offset: int = 1, limit: int = 200) -> str:
        """Read file content from S3."""
        content = self.client.get_object(key)

        if content is None:
            return f"Error: file not found: {key}"

        lines = content.splitlines()
        end = min(offset + limit - 1, len(lines))
        excerpt = lines[offset - 1 : end]

        if not excerpt:
            return f"No lines found. {key} has {len(lines)} lines."

        return "\n".join(f"{i}: {line}" for i, line in enumerate(excerpt, start=offset))

    def grep(self, pattern: str, max_results: int = 30) -> str:
        """Search files in S3 - downloads and scans all files."""
        import re

        rx = re.compile(pattern, re.IGNORECASE)
        keys = self.client.list_objects()

        hits = []
        for key in keys:
            content = self.client.get_object(key)
            if content is None:
                continue

            for i, line in enumerate(content.splitlines(), start=1):
                if rx.search(line):
                    hits.append(f"{key}:{i}: {line.strip()}")
                    if len(hits) >= max_results:
                        return "\n".join(hits)

        if not hits:
            return f"No matches found for pattern: {pattern}"

        return "\n".join(hits)


def list_files(pattern: str = "*.md") -> str:
    """List files in S3 bucket."""
    source = S3Source()
    return source.list_files(pattern)


def read_file(key: str, offset: int = 1, limit: int = 200) -> str:
    """Read file from S3."""
    source = S3Source()
    return source.read_file(key, offset, limit)


def grep(pattern: str, max_results: int = 30) -> str:
    """Search files in S3."""
    source = S3Source()
    return source.grep(pattern, max_results)


if __name__ == "__main__":
    import sys

    if not settings.verify_s3():
        print("S3 not configured. Set AWS credentials and S3_BUCKET in .env")
        sys.exit(1)

    source = S3Source()

    print("Testing S3 tools...")

    print("\n1. list_files:")
    files = source.list_files()
    print(files[:500] if len(files) > 500 else files)

    print("\n2. grep('connection'):")
    hits = source.grep("connection", max_results=5)
    print(hits[:500] if len(hits) > 500 else hits)

    print("\n3. read_file:")
    content = source.read_file("notes/01-engineering-handbook.md", limit=5)
    print(content)