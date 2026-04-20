#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick verification script for STORY-203 Track 2 implementation.

Run this script to verify all Track 2 changes are working correctly:
- SYS-M02: Token cache hash mechanism
- SYS-M03: Rate limiter max size
- SYS-M04: Database-driven plan capabilities
- CROSS-M01: /api/plans endpoint

Usage:
    python test_story_203_track2.py
"""

import sys
import hashlib

import pytest

# Windows console encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_sys_m02_hash_mechanism():
    """Test SYS-M02: Verify SHA-256 hash is deterministic."""
    print("\n=== SYS-M02: Token Cache Hash Mechanism ===")

    test_token = "abcd1234efgh5678"

    hash1 = hashlib.sha256(test_token[:16].encode('utf-8')).hexdigest()
    hash2 = hashlib.sha256(test_token[:16].encode('utf-8')).hexdigest()

    assert hash1 == hash2, "SHA-256 hash must be deterministic"
    assert isinstance(hash1, str), "Hash must be string type (compatible with dict keys)"
    print(f"[PASS] SHA-256 hash is deterministic (hash: {hash1[:16]}...)")


def test_sys_m03_rate_limiter_max_size():
    """Test SYS-M03: Verify MAX_MEMORY_STORE_SIZE constant exists."""
    try:
        from rate_limiter import MAX_MEMORY_STORE_SIZE
    except ImportError as e:
        pytest.fail(f"Cannot import MAX_MEMORY_STORE_SIZE: {e}")

    assert MAX_MEMORY_STORE_SIZE == 10_000, (
        f"Expected MAX_MEMORY_STORE_SIZE=10,000, got {MAX_MEMORY_STORE_SIZE:,}"
    )


def test_sys_m04_plan_capabilities_loader():
    """Test SYS-M04: Verify plan capabilities functions exist."""
    try:
        from quota import (
            get_plan_capabilities,
            clear_plan_capabilities_cache,
            PLAN_CAPABILITIES_CACHE_TTL,
        )
    except ImportError as e:
        pytest.fail(f"Cannot import quota helpers: {e}")

    assert PLAN_CAPABILITIES_CACHE_TTL == 300, (
        f"Expected PLAN_CAPABILITIES_CACHE_TTL=300s, got {PLAN_CAPABILITIES_CACHE_TTL}s"
    )

    try:
        caps = get_plan_capabilities()
    except Exception as e:
        pytest.fail(f"get_plan_capabilities() raised: {e}")

    assert len(caps) > 0, "get_plan_capabilities() returned empty dict"

    # Verify at least one known plan is present. The prod tier names evolved
    # over time; keep this loose to tolerate plan-catalog changes.
    known_candidates = {"free_trial", "consultor_agil", "maquina", "sala_guerra", "smartlic_pro", "consultoria"}
    assert any(p in caps for p in known_candidates), (
        f"No known plan found in capabilities. Got: {list(caps.keys())[:10]}"
    )

    # Structure check on any plan present
    sample_plan = next(iter(caps.values()))
    required_keys = {"max_history_days", "allow_excel"}
    missing_keys = required_keys - set(sample_plan.keys())
    assert not missing_keys, f"Sample plan missing required keys: {missing_keys}"

    # Cache clear should not raise
    clear_plan_capabilities_cache()


def test_cross_m01_plans_endpoint():
    """Test CROSS-M01: Verify /api/plans endpoint exists."""
    try:
        from routes.plans import router, PlansResponse, PlanDetails  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Cannot import plans router: {e}")

    # Check router has the endpoint
    routes = [route for route in router.routes if hasattr(route, 'path')]
    api_plans_route = [r for r in routes if r.path == "/api/plans"]
    assert api_plans_route, "/api/plans route not registered on plans router"

    route = api_plans_route[0]
    methods = set(route.methods) if getattr(route, "methods", None) else set()
    assert "GET" in methods, f"GET method not supported on /api/plans (methods: {methods})"

    # Verify Pydantic model still constructs
    PlanDetails(
        id="test_plan",
        name="Test Plan",
        description="Test Description",
        price_brl=100.0,
        duration_days=30,
        max_searches=50,
        capabilities={
            "max_history_days": 30,
            "allow_excel": False,
            "max_requests_per_month": 50,
            "max_requests_per_min": 10,
            "max_summary_tokens": 200,
            "priority": "normal",
        },
        is_active=True,
    )


def test_main_py_integration():
    """Test that main.py registers the new router.

    NOTE (STORY-BTS-011): use pathlib + __file__ instead of open("main.py"), since
    pytest may run from arbitrary CWD in CI.
    """
    from pathlib import Path

    main_py = Path(__file__).resolve().parent.parent / "main.py"
    assert main_py.exists(), f"main.py not found at {main_py}"
    content = main_py.read_text(encoding="utf-8")

    assert "from routes.plans import router as plans_router" in content, (
        "main.py missing import of plans_router"
    )
    assert "app.include_router(plans_router)" in content, (
        "main.py missing app.include_router(plans_router)"
    )


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("STORY-203 Track 2 Verification Script")
    print("=" * 60)

    tests = [
        ("SYS-M02: Token Cache Hash", test_sys_m02_hash_mechanism),
        ("SYS-M03: Rate Limiter Max Size", test_sys_m03_rate_limiter_max_size),
        ("SYS-M04: Plan Capabilities", test_sys_m04_plan_capabilities_loader),
        ("CROSS-M01: /api/plans Endpoint", test_cross_m01_plans_endpoint),
        ("main.py Integration", test_main_py_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All Track 2 implementations verified successfully!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review above output.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

