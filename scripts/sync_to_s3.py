"""
Sync local notes directory to S3 bucket.

Upload local markdown files to S3 for remote access.
"""

import sys
from pathlib import Path

from src.config import settings
from src.logging import setup_logging, get_logger
from src.tools.s3 import get_s3_client, S3Client

setup_logging(log_level=settings.log_level)
logger = get_logger(__name__)


def sync_to_s3(
    local_dir: Path | None = None,
    s3_prefix: str = "notes/",
    dry_run: bool = False,
) -> dict:
    """Sync local notes to S3 bucket."""
    local_dir = local_dir or settings.notes_dir

    if not local_dir.exists():
        logger.error(f"Local directory not found: {local_dir}")
        return {"error": f"Local directory not found: {local_dir}"}

    s3_client = get_s3_client()

    if not s3_client.test_connection():
        logger.error("S3 connection test failed")
        return {"error": "S3 connection test failed"}

    files = list(local_dir.rglob("*.md"))
    logger.info(f"Found {len(files)} markdown files to sync")

    uploaded = []
    skipped = []
    errors = []

    for file in files:
        relative_path = file.relative_to(local_dir)
        s3_key = s3_prefix + str(relative_path)

        content = file.read_text(encoding="utf-8")

        if dry_run:
            logger.info(f"[DRY RUN] Would upload: {s3_key}")
            uploaded.append(s3_key)
            continue

        success = s3_client.put_object(s3_key, content)
        if success:
            uploaded.append(s3_key)
            logger.info(f"Uploaded: {s3_key}")
        else:
            errors.append(s3_key)
            logger.error(f"Failed: {s3_key}")

    result = {
        "uploaded": len(uploaded),
        "skipped": len(skipped),
        "errors": len(errors),
        "total": len(files),
    }

    logger.info(f"Sync complete: {result}")
    return result


def sync_from_s3(
    s3_prefix: str = "notes/",
    local_dir: Path | None = None,
    dry_run: bool = False,
) -> dict:
    """Sync files from S3 to local directory."""
    local_dir = local_dir or settings.notes_dir

    s3_client = get_s3_client()

    if not s3_client.test_connection():
        logger.error("S3 connection test failed")
        return {"error": "S3 connection test failed"}

    keys = s3_client.list_objects(prefix=s3_prefix)
    logger.info(f"Found {len(keys)} files in S3 to sync")

    downloaded = []
    errors = []

    local_dir.mkdir(parents=True, exist_ok=True)

    for key in keys:
        content = s3_client.get_object(key)
        if content is None:
            errors.append(key)
            continue

        relative_path = Path(key).relative_to(s3_prefix)
        local_path = local_dir / relative_path

        if dry_run:
            logger.info(f"[DRY RUN] Would download: {key} -> {local_path}")
            downloaded.append(key)
            continue

        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(content, encoding="utf-8")
        downloaded.append(key)
        logger.info(f"Downloaded: {key} -> {local_path}")

    result = {
        "downloaded": len(downloaded),
        "errors": len(errors),
        "total": len(keys),
    }

    logger.info(f"Sync complete: {result}")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync notes to/from S3")
    parser.add_argument(
        "direction",
        choices=["to-s3", "from-s3"],
        help="Sync direction",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument(
        "--prefix",
        default="notes/",
        help="S3 prefix/path",
    )

    args = parser.parse_args()

    if not settings.verify_s3():
        print("Error: S3 not configured. Set AWS credentials and S3_BUCKET in .env")
        sys.exit(1)

    if args.direction == "to-s3":
        result = sync_to_s3(s3_prefix=args.prefix, dry_run=args.dry_run)
    else:
        result = sync_from_s3(s3_prefix=args.prefix, dry_run=args.dry_run)

    print(f"\nResult: {result}")