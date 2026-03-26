#!/usr/bin/env python3
"""Safe test runner for Windows — runs each test file in a subprocess with timeout.

Usage:
    python scripts/run_tests_safe.py                    # All tests
    python scripts/run_tests_safe.py tests/test_foo.py  # Specific file
    python scripts/run_tests_safe.py --timeout 60       # Custom per-file timeout (default: 120s)
    python scripts/run_tests_safe.py --parallel 4       # Run 4 files in parallel (default: 1)

Why this exists:
    On Windows, pytest-timeout's "thread" method cannot interrupt C-level blocking calls
    (asyncio IOCP, regex compilation, threading.Lock.acquire). When a test hangs in
    single-process mode, the ENTIRE suite hangs forever. This runner isolates each test
    file in its own subprocess and kills it on timeout, so the remaining files still run.

    On Linux/CI, use `pytest --timeout=30 --timeout-method=signal` instead (reliable).
"""

import argparse
import glob
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


@dataclass
class FileResult:
    path: str
    status: str = "pending"  # passed, failed, timeout, error
    duration: float = 0.0
    passed: int = 0
    failed: int = 0
    output: str = ""


def run_test_file(filepath: str, timeout: int) -> FileResult:
    """Run a single test file with subprocess timeout."""
    result = FileResult(path=filepath)
    start = time.monotonic()

    cmd = [
        sys.executable, "-m", "pytest",
        filepath,
        "--timeout=30",
        "-q", "--tb=line", "--no-header",
        "-p", "no:benchmark",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        result.duration = time.monotonic() - start
        result.output = proc.stdout + proc.stderr

        # Parse pytest summary
        for line in proc.stdout.splitlines():
            if "passed" in line:
                import re
                m = re.search(r"(\d+) passed", line)
                if m:
                    result.passed = int(m.group(1))
                m = re.search(r"(\d+) failed", line)
                if m:
                    result.failed = int(m.group(1))

        if proc.returncode == 0:
            result.status = "passed"
        else:
            result.status = "failed"

    except subprocess.TimeoutExpired:
        result.duration = time.monotonic() - start
        result.status = "timeout"
        result.output = f"TIMEOUT after {timeout}s"

    except Exception as e:
        result.duration = time.monotonic() - start
        result.status = "error"
        result.output = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="Safe per-file test runner")
    parser.add_argument("files", nargs="*", help="Test files to run (default: all)")
    parser.add_argument("--timeout", type=int, default=120, help="Per-file timeout in seconds")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel workers")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    args = parser.parse_args()

    # Discover test files
    if args.files:
        test_files = args.files
    else:
        test_files = sorted(
            glob.glob("tests/test_*.py") + glob.glob("tests/integration/test_*.py")
        )

    if not test_files:
        print("No test files found.")
        return 1

    print(f"Running {len(test_files)} test files (timeout={args.timeout}s, parallel={args.parallel})")
    print("=" * 70)

    results: list[FileResult] = []
    total_start = time.monotonic()

    if args.parallel <= 1:
        # Sequential mode
        for i, filepath in enumerate(test_files, 1):
            short = os.path.basename(filepath)
            print(f"[{i}/{len(test_files)}] {short} ... ", end="", flush=True)
            r = run_test_file(filepath, args.timeout)
            results.append(r)

            if r.status == "passed":
                print(f"OK ({r.passed} passed, {r.duration:.1f}s)")
            elif r.status == "timeout":
                print(f"TIMEOUT ({args.timeout}s)")
            elif r.status == "failed":
                print(f"FAIL ({r.failed} failed, {r.passed} passed, {r.duration:.1f}s)")
            else:
                print(f"ERROR ({r.duration:.1f}s)")

            if args.fail_fast and r.status in ("failed", "error"):
                print(f"\n--fail-fast: stopping after {short}")
                break
    else:
        # Parallel mode
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            future_map = {
                executor.submit(run_test_file, f, args.timeout): f
                for f in test_files
            }
            for future in as_completed(future_map):
                r = future.result()
                results.append(r)
                short = os.path.basename(r.path)
                status_icon = {"passed": "OK", "failed": "FAIL", "timeout": "TIMEOUT", "error": "ERR"}
                print(f"  {status_icon.get(r.status, '??')} {short} ({r.duration:.1f}s)")

    total_duration = time.monotonic() - total_start

    # Summary
    print("\n" + "=" * 70)
    passed_files = [r for r in results if r.status == "passed"]
    failed_files = [r for r in results if r.status == "failed"]
    timeout_files = [r for r in results if r.status == "timeout"]
    error_files = [r for r in results if r.status == "error"]

    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)

    print(f"\nFiles: {len(passed_files)} passed, {len(failed_files)} failed, "
          f"{len(timeout_files)} timeout, {len(error_files)} errors "
          f"(of {len(results)} total)")
    print(f"Tests: {total_passed} passed, {total_failed} failed")
    print(f"Duration: {total_duration:.1f}s")

    if timeout_files:
        print(f"\nTIMEOUT files ({len(timeout_files)}):")
        for r in timeout_files:
            print(f"  - {r.path}")

    if failed_files:
        print(f"\nFAILED files ({len(failed_files)}):")
        for r in failed_files:
            print(f"  - {r.path} ({r.failed} failures)")

    return 1 if (failed_files or timeout_files or error_files) else 0


if __name__ == "__main__":
    sys.exit(main())
