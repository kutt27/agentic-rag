"""
S3 client wrapper with session management.

Handles boto3 session creation, credential validation, and resource cleanup.
"""

import boto3
import botocore.exceptions
from botocore.config import Config
from typing import Optional

from src.config import settings
from src.logging import get_logger

logger = get_logger(__name__)


class S3Client:
    """Wrapper for boto3 S3 operations."""

    def __init__(self, bucket: Optional[str] = None, region: Optional[str] = None):
        self.bucket = bucket or settings.s3_bucket
        self.region = region or settings.s3_region
        self._client = None
        self._resource = None

    @property
    def client(self):
        """Lazy-load S3 client."""
        if self._client is None:
            logger.info(f"Creating S3 client for bucket: {self.bucket}")
            self._client = boto3.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                config=Config(
                    retries={"max_attempts": 3},
                    connect_timeout=5,
                    read_timeout=10,
                ),
            )
        return self._client

    @property
    def resource(self):
        """Lazy-load S3 resource (higher-level API)."""
        if self._resource is None:
            self._resource = boto3.resource(
                "s3",
                region_name=self.region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
        return self._resource

    def test_connection(self) -> bool:
        """Test S3 connectivity."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"S3 connection test successful: {self.bucket}")
            return True
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.warning(f"S3 connection test failed: {error_code}")
            return False
        except Exception as e:
            logger.warning(f"S3 connection test error: {e}")
            return False

    def list_objects(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        """List objects in bucket with optional prefix filter."""
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix, MaxKeys=max_keys)

            keys = []
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        if key.endswith(".md"):
                            keys.append(key)

            logger.info(f"S3 listed {len(keys)} markdown files")
            return sorted(keys)

        except botocore.exceptions.ClientError as e:
            logger.error(f"S3 list failed: {e}")
            return []

    def get_object(self, key: str) -> Optional[str]:
        """Get object content by key."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"]
            content = body.read().decode("utf-8")
            logger.info(f"S3 get_object: {key}")
            return content

        except botocore.exceptions.ClientError as e:
            logger.error(f"S3 get_object failed for {key}: {e}")
            return None

    def put_object(self, key: str, content: str) -> bool:
        """Put object content (upload file)."""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/markdown",
            )
            logger.info(f"S3 put_object: {key}")
            return True

        except botocore.exceptions.ClientError as e:
            logger.error(f"S3 put_object failed for {key}: {e}")
            return False

    def delete_object(self, key: str) -> bool:
        """Delete object by key."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"S3 delete_object: {key}")
            return True

        except botocore.exceptions.ClientError as e:
            logger.error(f"S3 delete_object failed for {key}: {e}")
            return False

    def close(self) -> None:
        """Clean up client connections."""
        if self._client:
            self._client = None
        if self._resource:
            self._resource = None
        logger.info("S3 client closed")


_s3_client: Optional[S3Client] = None


def get_s3_client(bucket: Optional[str] = None) -> S3Client:
    """Get or create global S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client(bucket=bucket)
    return _s3_client


if __name__ == "__main__":
    print("Testing S3 client...")

    if not settings.verify_s3():
        print("S3 not configured. Set AWS credentials and S3_BUCKET in .env")
    else:
        client = get_s3_client()

        if client.test_connection():
            print(f"Connected to S3 bucket: {client.bucket}")

            keys = client.list_objects()
            print(f"Found {len(keys)} markdown files")

            if keys:
                content = client.get_object(keys[0])
                print(f"First file: {keys[0][:50]}...")
                print(f"Content length: {len(content or '')}")
        else:
            print("Could not connect to S3")