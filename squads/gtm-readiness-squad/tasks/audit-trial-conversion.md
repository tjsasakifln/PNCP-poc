---
task: "Audit Trial Conversion Flow"
responsavel: "@billing-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - Trial configuration (14 days, STORY-277/319)
  - backend/quota.py
  - frontend trial status components
Saida: |
  - Trial flow validation
  - Conversion funnel analysis
  - Grace period check
Checklist:
  - "[ ] Trial creates on signup (14 days)"
  - "[ ] Trial days remaining shown correctly"
  - "[ ] Trial-to-paid conversion works"
  - "[ ] Trial expiry downgrades to free"
  - "[ ] Grace period (3 days) functional"
  - "[ ] Quota enforced during trial"
---

# *audit-trial

Validate the complete trial lifecycle: creation → usage → conversion/expiry.

## Steps

1. Read quota.py — check trial quota enforcement
2. Read trial status frontend components
3. Verify STORY-277/319 trial configuration (14 days)
4. Check grace period implementation (SUBSCRIPTION_GRACE_DAYS)
5. Verify trial expiry handling

## Output

Score (0-10) + trial flow gaps + recommendations
