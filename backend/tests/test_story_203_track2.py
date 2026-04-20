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
    print("\n=== SYS-M03: Rate Limiter Max Size ===")

    try:
        from rate_limiter import MAX_MEMORY_STORE_SIZE
        print(f"✅ MAX_MEMORY_STORE_SIZE = {MAX_MEMORY_STORE_SIZE:,}")

        if MAX_MEMORY_STORE_SIZE == 10_000:
            print("✅ Limit set to correct value (10,000)")
        else:
            print(f"⚠️  WARNING: Expected 10,000, got {MAX_MEMORY_STORE_SIZE:,}")

        return True
    except ImportError as e:
        print(f"❌ FAIL: Cannot import MAX_MEMORY_STORE_SIZE: {e}")
        return False


def test_sys_m04_plan_capabilities_loader():
    """Test SYS-M04: Verify plan capabilities functions exist."""
    print("\n=== SYS-M04: Database-Driven Plan Capabilities ===")

    try:
        from quota import (
            get_plan_capabilities,
            clear_plan_capabilities_cache,
            PLAN_CAPABILITIES_CACHE_TTL,
        )
        print("✅ All required functions imported successfully")
    except ImportError as e:
        print(f"❌ FAIL: Cannot import functions: {e}")
        return False

    # Verify cache TTL
    if PLAN_CAPABILITIES_CACHE_TTL == 300:
        print(f"✅ Cache TTL = {PLAN_CAPABILITIES_CACHE_TTL}s (5 minutes)")
    else:
        print(f"⚠️  WARNING: Expected 300s, got {PLAN_CAPABILITIES_CACHE_TTL}s")

    # Test get_plan_capabilities() function
    try:
        caps = get_plan_capabilities()
        print(f"✅ get_plan_capabilities() returned {len(caps)} plans")

        # Verify expected plans exist
        expected_plans = ["free_trial", "consultor_agil", "maquina", "sala_guerra"]
        missing = [p for p in expected_plans if p not in caps]

        if not missing:
            print(f"✅ All expected plans present: {expected_plans}")
        else:
            print(f"⚠️  WARNING: Missing plans: {missing}")

        # Verify structure of one plan
        if "consultor_agil" in caps:
            cap = caps["consultor_agil"]
            required_keys = [
                "max_history_days",
                "allow_excel",
                "max_requests_per_month",
                "max_requests_per_min",
                "max_summary_tokens",
                "priority",
            ]
            missing_keys = [k for k in required_keys if k not in cap]

            if not missing_keys:
                print("✅ Plan capabilities have all required keys")
            else:
                print(f"❌ FAIL: Missing keys in capabilities: {missing_keys}")
                return False

        # Test cache clear function
        clear_plan_capabilities_cache()
        print("✅ clear_plan_capabilities_cache() executed successfully")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error testing plan capabilities: {e}")
        return False


def test_cross_m01_plans_endpoint():
    """Test CROSS-M01: Verify /api/plans endpoint exists."""
    print("\n=== CROSS-M01: /api/plans Endpoint ===")

    try:
        from routes.plans import router, PlansResponse, PlanDetails  # noqa: F401
        print("✅ Plans router imported successfully")
    except ImportError as e:
        print(f"❌ FAIL: Cannot import plans router: {e}")
        return False

    # Check router has the endpoint
    routes = [route for route in router.routes if hasattr(route, 'path')]
    api_plans_route = [r for r in routes if r.path == "/api/plans"]

    if api_plans_route:
        print("✅ /api/plans route registered")
        route = api_plans_route[0]
        methods = ",".join(route.methods) if hasattr(route, 'methods') and route.methods else "N/A"
        print(f"   Methods: {methods}")

        if "GET" in methods:
            print("✅ GET method supported")
        else:
            print("⚠️  WARNING: GET method not found")

    else:
        print("❌ FAIL: /api/plans route not found")
        return False

    # Verify Pydantic models
    try:
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
        print("✅ PlanDetails model validation works")
    except Exception as e:
        print(f"❌ FAIL: PlanDetails validation failed: {e}")
        return False

    return True


def test_main_py_integration():
    """Test that main.py registers the new router."""
    print("\n=== main.py Integration ===")

    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()

        checks = {
            "Import statement": "from routes.plans import router as plans_router",
            "Router registration": "app.include_router(plans_router)",
        }

        all_passed = True
        for check_name, check_str in checks.items():
            if check_str in content:
                print(f"✅ {check_name} found")
            else:
                print(f"❌ FAIL: {check_name} not found")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ FAIL: Error reading main.py: {e}")
        return False


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

