"""Object storage for Excel reports using Supabase Storage.

Provides upload and signed URL generation for Excel reports, enabling
horizontal scaling by removing filesystem dependencies.

Architecture:
- Bucket: excel-reports (auto-created if not exists)
- File path: {timestamp}_{search_id}.xlsx
- TTL: 60 minutes (signed URL expiry)
- Graceful fallback: Returns None if upload fails
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

BUCKET_NAME = "excel-reports"
SIGNED_URL_TTL = 3600  # 60 minutes in seconds


def _get_storage():
    """Get Supabase storage client.

    Returns:
        Supabase storage instance.

    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set.
    """
    from supabase_client import get_supabase
    sb = get_supabase()
    return sb.storage


def _ensure_bucket_exists() -> None:
    """Ensure the excel-reports bucket exists, create if not.

    This is called once at module initialization to avoid repeated checks.
    """
    try:
        storage = _get_storage()
        # List buckets to check if ours exists
        buckets = storage.list_buckets()
        bucket_names = [b.name for b in buckets] if buckets else []

        if BUCKET_NAME not in bucket_names:
            logger.info(f"Creating Supabase Storage bucket: {BUCKET_NAME}")
            storage.create_bucket(
                BUCKET_NAME,
                options={"public": False}  # Private bucket, use signed URLs
            )
            logger.info(f"Bucket created: {BUCKET_NAME}")
        else:
            logger.debug(f"Bucket already exists: {BUCKET_NAME}")

    except Exception as e:
        logger.warning(f"Failed to ensure bucket exists (will retry on upload): {e}")


def upload_excel(buffer_bytes: bytes, search_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Upload Excel to Supabase Storage, return file_id and signed URL.

    Args:
        buffer_bytes: Excel file content as bytes
        search_id: Optional search ID for filename (generates UUID if None)

    Returns:
        Dict with keys:
            - file_id: Unique identifier for the file
            - file_path: Storage path (for debugging)
            - signed_url: Temporary download URL (valid for SIGNED_URL_TTL seconds)
            - expires_in: TTL in seconds
        None if upload fails (caller should handle gracefully)

    Example:
        >>> excel_buffer = create_excel(licitacoes)
        >>> result = upload_excel(excel_buffer.read(), search_id="abc123")
        >>> if result:
        ...     print(result['signed_url'])
    """
    file_id = search_id or str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = f"{timestamp}_{file_id}.xlsx"

    try:
        storage = _get_storage()

        # Upload file
        storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=buffer_bytes,
            file_options={"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        )

        # Generate signed URL
        signed_url_response = storage.from_(BUCKET_NAME).create_signed_url(
            path=file_path,
            expires_in=SIGNED_URL_TTL,
        )

        # Handle both possible response formats from Supabase client
        signed_url = signed_url_response.get("signedURL") or signed_url_response.get("signedUrl", "")

        if not signed_url:
            logger.error(f"Supabase returned empty signed URL for {file_path}")
            return None

        logger.info(f"Excel uploaded to storage: {file_path} (TTL={SIGNED_URL_TTL}s)")
        return {
            "file_id": file_id,
            "file_path": file_path,
            "signed_url": signed_url,
            "expires_in": SIGNED_URL_TTL,
        }

    except Exception as e:
        logger.error(f"Failed to upload Excel to storage: {e}", exc_info=True)
        # Fallback: return None, let caller handle gracefully (e.g., use base64)
        return None


# Initialize bucket on module load (lazy, only if storage is used)
try:
    _ensure_bucket_exists()
except Exception as init_error:
    logger.warning(f"Storage initialization failed (will retry on first upload): {init_error}")
