"""GTM-FIX-027 Track 1: PNCP page size tests."""
import inspect
import pytest
from pncp_client import PNCPClient, AsyncPNCPClient


def test_fetch_page_default_tamanho_50():
    """AC1: fetch_page() signature defaults to tamanho=50 (PNCP max as of Feb 2026)."""
    sig = inspect.signature(PNCPClient.fetch_page)
    assert sig.parameters["tamanho"].default == 50


def test_fetch_page_async_default_tamanho_50():
    """AC2: _fetch_page_async() signature defaults to tamanho=50 (PNCP max as of Feb 2026)."""
    sig = inspect.signature(AsyncPNCPClient._fetch_page_async)
    assert sig.parameters["tamanho"].default == 50


def test_no_test_assumes_tamanho_20():
    """AC7: No test file references the old tamanho=20 default as expected behavior."""
    import glob
    import re
    test_files = glob.glob("tests/test_*.py")
    for tf in test_files:
        if "test_gtm_fix_027" in tf:
            continue
        try:
            with open(tf, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Skip files with encoding issues (unrelated to our changes)
            continue
        # Check no assertion expects tamanho=20 as default
        matches = re.findall(r'tamanho["\']?\s*[:=]\s*20\b', content)
        assert len(matches) == 0, f"{tf} still references tamanho=20: {matches}"
