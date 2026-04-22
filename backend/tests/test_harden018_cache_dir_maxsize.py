"""HARDEN-018: Local Cache Dir Max Size (200MB) tests.

AC1: _check_cache_dir_size() helper verifies total directory size
AC2: If > 200MB, deletes oldest files until < 100MB
AC3: Called before each write + in cleanup
AC4: Unit tests (this file)
"""

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from search_cache import (
    _check_cache_dir_size,
    _save_to_local,
    cleanup_local_cache,
    LOCAL_CACHE_MAX_SIZE_MB,
    LOCAL_CACHE_TARGET_SIZE_MB,
)


@pytest.fixture
def cache_dir(tmp_path):
    """Create a temporary cache directory and patch LOCAL_CACHE_DIR."""
    cache_path = tmp_path / "smartlic_cache"
    cache_path.mkdir()
    with patch("cache.local_file.LOCAL_CACHE_DIR", cache_path):
        yield cache_path


def _create_file(cache_dir: Path, name: str, size_mb: float, age_offset: float = 0.0):
    """Create a cache file with given size (MB) and relative mtime offset (seconds older)."""
    fpath = cache_dir / name
    # Write enough data to reach target size
    size_bytes = int(size_mb * 1024 * 1024)
    fpath.write_bytes(b"x" * size_bytes)
    if age_offset > 0:
        mtime = time.time() - age_offset
        os.utime(fpath, (mtime, mtime))
    return fpath


class TestCheckCacheDirSize:
    """AC1/AC2: _check_cache_dir_size() enforces 200MB limit."""

    def test_returns_zero_when_dir_empty(self, cache_dir):
        assert _check_cache_dir_size() == 0

    def test_returns_zero_when_below_limit(self, cache_dir):
        _create_file(cache_dir, "a.json", 50)
        assert _check_cache_dir_size() == 0

    def test_returns_zero_when_dir_not_exists(self, tmp_path):
        nonexistent = tmp_path / "nope"
        with patch("cache.local_file.LOCAL_CACHE_DIR", nonexistent):
            assert _check_cache_dir_size() == 0

    def test_evicts_oldest_files_when_over_200mb(self, cache_dir):
        """AC2: Creates 250MB across 5 files, oldest should be evicted first."""
        # 5 files x 50MB = 250MB total (> 200MB limit)
        for i in range(5):
            _create_file(cache_dir, f"file{i}.json", 50, age_offset=(5 - i) * 10)
            # file0 = oldest (50s ago), file4 = newest (10s ago)

        deleted = _check_cache_dir_size()
        assert deleted >= 3  # Need to get from 250MB down to <100MB = delete 3x50MB
        remaining = list(cache_dir.glob("*.json"))
        assert len(remaining) == 2  # 2 files x 50MB = 100MB

    def test_evicts_until_below_target(self, cache_dir):
        """AC2: Stops evicting once below 100MB target."""
        # 4 files of different sizes, totaling 220MB
        _create_file(cache_dir, "old1.json", 60, age_offset=40)
        _create_file(cache_dir, "old2.json", 60, age_offset=30)
        _create_file(cache_dir, "mid.json", 50, age_offset=20)
        _create_file(cache_dir, "new.json", 50, age_offset=10)

        deleted = _check_cache_dir_size()
        # 220MB total. Delete old1 (60) → 160MB > 100MB. Delete old2 (60) → 100MB ≤ 100MB. Stop.
        assert deleted == 2

        remaining_names = sorted(f.name for f in cache_dir.glob("*.json"))
        assert remaining_names == ["mid.json", "new.json"]

    def test_preserves_newest_files(self, cache_dir):
        """Oldest files are deleted, newest are preserved."""
        _create_file(cache_dir, "oldest.json", 80, age_offset=100)
        _create_file(cache_dir, "middle.json", 80, age_offset=50)
        _create_file(cache_dir, "newest.json", 80, age_offset=1)
        # 240MB total, need to get to <100MB

        _check_cache_dir_size()

        remaining = [f.name for f in cache_dir.glob("*.json")]
        assert "newest.json" in remaining
        assert "oldest.json" not in remaining


class TestSaveToLocalIntegration:
    """AC3: _save_to_local calls _check_cache_dir_size before writing."""

    def test_save_to_local_triggers_size_check(self, cache_dir):
        """Verify _check_cache_dir_size is called during _save_to_local."""
        with patch("cache.local_file._check_cache_dir_size") as mock_check:
            _save_to_local("test_key_abc", [{"id": 1}], ["pncp"])
            mock_check.assert_called_once()

        # Verify the file was written
        files = list(cache_dir.glob("*.json"))
        assert len(files) == 1


class TestCleanupLocalCacheIntegration:
    """AC3: cleanup_local_cache also calls _check_cache_dir_size."""

    def test_cleanup_triggers_size_check(self, cache_dir):
        """Verify _check_cache_dir_size is called during cleanup."""
        with patch("cache.local_file._check_cache_dir_size") as mock_check:
            cleanup_local_cache()
            mock_check.assert_called_once()


class TestConstants:
    """Verify HARDEN-018 constants are correctly set."""

    def test_max_size_is_200mb(self):
        assert LOCAL_CACHE_MAX_SIZE_MB == 200

    def test_target_size_is_100mb(self):
        assert LOCAL_CACHE_TARGET_SIZE_MB == 100
