"""Contract tests for entity endpoint parity (CRIT-DATA-PARITY-001).

Validates that pairs of endpoints aggregating the same underlying dataset
return values within a 5% drift tolerance for the same entity.

These tests run against a live target (staging or production) — skipped
when PARITY_TARGET_URL env var is absent. Intended for CI nightly
advisory, not PR gate.

Run locally:
    export PARITY_TARGET_URL=https://smartlic.tech
    pytest backend/tests/contract/ -v -m contract
"""
