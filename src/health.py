"""
Health checks for agentic RAG.

Verifies all components are accessible and functioning.
"""

import sys
from typing import Optional

from src.config import settings
from src.logging import get_logger
from src.tools.s3 import get_s3_client

logger = get_logger(__name__)


class HealthCheck:
    """Health check for all system components."""

    def __init__(self):
        self.checks = []

    def check_local_notes(self) -> dict:
        """Check if local notes directory is accessible."""
        notes_dir = settings.notes_dir

        if not notes_dir.exists():
            return {
                "name": "local_notes",
                "status": "error",
                "message": f"Notes directory not found: {notes_dir}",
            }

        if not notes_dir.is_dir():
            return {
                "name": "local_notes",
                "status": "error",
                "message": f"Notes path exists but is not a directory: {notes_dir}",
            }

        files = list(notes_dir.glob("*.md"))
        return {
            "name": "local_notes",
            "status": "ok",
            "message": f"Found {len(files)} markdown files",
            "file_count": len(files),
        }

    def check_s3(self) -> dict:
        """Check if S3 is accessible."""
        if not settings.verify_s3():
            return {
                "name": "s3",
                "status": "disabled",
                "message": "S3 not configured",
            }

        try:
            client = get_s3_client()
            if client.test_connection():
                keys = client.list_objects()
                return {
                    "name": "s3",
                    "status": "ok",
                    "message": f"Connected to {client.bucket}",
                    "file_count": len(keys),
                }
            else:
                return {
                    "name": "s3",
                    "status": "error",
                    "message": "Could not connect to S3 bucket",
                }
        except Exception as e:
            return {
                "name": "s3",
                "status": "error",
                "message": f"S3 error: {e}",
            }

    def check_openai(self) -> dict:
        """Check if OpenAI is configured."""
        if not settings.openai_api_key:
            return {
                "name": "openai",
                "status": "disabled",
                "message": "OpenAI API key not set",
            }

        return {
            "name": "openai",
            "status": "ok",
            "message": f"Model configured: {settings.openai_model}",
            "model": settings.openai_model,
        }

    def check_ripgrep(self) -> dict:
        """Check if ripgrep is available."""
        import shutil

        rg = shutil.which("rg")
        if not rg:
            return {
                "name": "ripgrep",
                "status": "warning",
                "message": "ripgrep not installed",
            }

        return {
            "name": "ripgrep",
            "status": "ok",
            "message": f"Found: {rg}",
        }

    def run_all(self) -> list[dict]:
        """Run all health checks."""
        return [
            self.check_local_notes(),
            self.check_s3(),
            self.check_openai(),
            self.check_ripgrep(),
        ]

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        checks = self.run_all()

        for check in checks:
            if check["status"] == "error":
                return False

        return True


def run_health_checks(verbose: bool = True) -> dict:
    """Run all health checks and return summary."""
    health = HealthCheck()
    checks = health.run_all()

    errors = sum(1 for c in checks if c["status"] == "error")
    warnings = sum(1 for c in checks if c["status"] == "warning")
    ok = sum(1 for c in checks if c["status"] == "ok")

    result = {
        "healthy": errors == 0,
        "checks": checks,
        "summary": {"ok": ok, "warning": warnings, "error": errors},
    }

    if verbose:
        print("Health Checks:")
        for check in checks:
            status_icon = {
                "ok": "✓",
                "warning": "⚠",
                "error": "✗",
                "disabled": "○",
            }.get(check["status"], "?")

            print(f"  {status_icon} {check['name']}: {check['message']}")

        print(f"\nSummary: {ok} ok, {warnings} warning, {errors} error")

    return result


if __name__ == "__main__":
    run_health_checks()