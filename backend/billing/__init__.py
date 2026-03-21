"""billing package — SYS-004 backend package grouping.

Provides a new import path for billing-related modules:
  - billing.quota (from quota)
  - billing.service (from services.billing)

All original import paths continue to work via the unchanged top-level modules.
"""
