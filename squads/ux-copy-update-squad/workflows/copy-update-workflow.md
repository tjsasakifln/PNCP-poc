---
workflow: Complete Copy Update Workflow
responsavel: "@copy-editor"
responsavel_type: agent
atomic_layer: workflow
steps:
  - step: 1
    task: find-copy.md
    description: Locate all instances of the text
  - step: 2
    task: validate-text.md
    description: Validate new text quality
  - step: 3
    task: validate-ux.md
    description: Review UX impact (by @ux-validator)
  - step: 4
    task: update-copy.md
    description: Apply text changes
  - step: 5
    task: check-accessibility.md
    description: Verify accessibility (by @ux-validator)
  - step: 6
    task: test-ui-changes.md
    description: Test visual changes (by @frontend-tester)
---

# Copy Update Workflow

End-to-end workflow for safely updating copy across the application.

## Workflow Steps

```
┌─────────────────────────────────────────────────────────────┐
│                  COPY UPDATE WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. FIND COPY (@copy-editor)                                │
│     *find-copy "text to find"                               │
│     → Locate all instances across codebase                  │
│                                                              │
│  2. VALIDATE TEXT (@copy-editor)                            │
│     *validate-text "new text"                               │
│     → Check grammar, style, tone                            │
│                                                              │
│  3. VALIDATE UX (@ux-validator)                             │
│     *validate-ux "old" "new"                                │
│     → Review UX quality and user impact                     │
│                                                              │
│  4. UPDATE COPY (@copy-editor)                              │
│     *update-copy file "old" "new"                           │
│     → Apply changes with backups                            │
│                                                              │
│  5. CHECK ACCESSIBILITY (@ux-validator)                     │
│     *check-accessibility "new text"                         │
│     → Verify WCAG compliance                                │
│                                                              │
│  6. TEST UI CHANGES (@frontend-tester)                      │
│     *test-ui-changes <files>                                │
│     → Run comprehensive UI tests                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Example: Update Welcome Message

```bash
# Step 1: Find all instances
@copy-editor
*find-copy "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)"

# Step 2: Validate new text
*validate-text "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio."

# Step 3: UX validation
@ux-validator
*validate-ux "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)" "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio."

# Step 4: Update copy
@copy-editor
*update-copy frontend/app/buscar/page.tsx "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)" "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio."

# Step 5: Accessibility check
@ux-validator
*check-accessibility "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio." --context "welcome message"

# Step 6: Test UI
@frontend-tester
*test-ui-changes frontend/app/buscar/page.tsx
```

## Success Criteria

- ✅ All instances found and updated
- ✅ Text quality validated (score ≥70)
- ✅ UX quality approved (score ≥70)
- ✅ Accessibility compliant (WCAG AA)
- ✅ UI tests passing (≥90% pass rate)
- ✅ No visual regressions

## Rollback Procedure

If issues are found:
1. Restore from backup: `.backup/`
2. Review issues with team
3. Revise text or approach
4. Re-run workflow

## Notes

- Always run complete workflow
- Don't skip validation steps
- Test on multiple viewports
- Document all changes
