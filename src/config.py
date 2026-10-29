"""
Configuration management using pydantic-settings.

Environment-based config with validation - no hardcoded constants.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    notes_dir: Path = Field(
        default=Path("./notes"),
        description="Directory containing markdown notes",
    )

    s3_bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket for remote notes (optional)",
    )

    s3_region: str = Field(
        default="us-east-1",
        description="AWS region for S3",
    )

    aws_access_key_id: str = Field(
        default="",
        description="AWS access key ID",
    )

    aws_secret_access_key: str = Field(
        default="",
        description="AWS secret access key",
    )

    grep_max_results: int = Field(
        default=30,
        description="Maximum grep results to return",
    )

    grep_timeout_seconds: int = Field(
        default=30,
        description="Timeout for grep operations",
    )

    read_max_lines: int = Field(
        default=200,
        description="Maximum lines to read from a file",
    )

    agent_request_limit: int = Field(
        default=20,
        description="Maximum agent turns per request",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    openai_model: str = Field(
        default="gpt-4.1-nano",
        description="OpenAI model for agent",
    )

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key",
    )

    def verify_notes_dir(self) -> bool:
        """Check if notes directory exists and is accessible."""
        return self.notes_dir.exists() and self.notes_dir.is_dir()

    def verify_s3(self) -> bool:
        """Check if S3 is configured and accessible."""
        if not self.s3_bucket:
            return False
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            return False
        return True


settings = Settings()


if __name__ == "__main__":
    print(f"Notes directory: {settings.notes_dir}")
    print(f"Notes dir exists: {settings.verify_notes_dir()}")
    print(f"S3 bucket: {settings.s3_bucket}")
    print(f"OpenAI model: {settings.openai_model}")