"""Contract tests — snapshot + schema validation for external APIs.

Detects breaking changes in response shape for:
- PNCP (primary data source)
- PCP v2 (secondary)
- ComprasGov v3 (tertiary)
- Stripe webhooks (billing)

Default run: offline contract-shape-validation against committed snapshots.
Opt-in: live API comparison via RUN_LIVE_CONTRACT_TESTS=1.
"""
