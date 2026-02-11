---
task: Test UI Changes
responsavel: "@frontend-tester"
responsavel_type: agent
atomic_layer: task
elicit: false
Entrada: |
  - changed_files: List of files with copy changes
  - test_scenarios: Optional specific scenarios to test
Saida: |
  - test_results: Pass/fail status for each test
  - visual_diff: Screenshots of before/after
  - issues_found: List of issues discovered
  - test_report: Complete test execution report
Checklist:
  - "[ ] Test desktop viewports"
  - "[ ] Test tablet viewports"
  - "[ ] Test mobile viewports"
  - "[ ] Run accessibility audits"
  - "[ ] Check cross-browser compatibility"
  - "[ ] Verify no layout breaks"
  - "[ ] Test keyboard navigation"
  - "[ ] Generate test report"
---

# *test-ui-changes

Runs comprehensive UI tests after copy changes to ensure visual consistency and functionality.

## Usage

```bash
@frontend-tester

*test-ui-changes frontend/app/buscar/page.tsx
*test-ui-changes frontend/app/buscar/page.tsx --scenarios "mobile,accessibility"
```

## Test Matrix

### Viewports Tested
- **Desktop:** 1920x1080, 1366x768
- **Tablet:** 768x1024 (portrait/landscape)
- **Mobile:** 375x667 (iPhone), 360x640 (Android)

### Browsers Tested
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Accessibility Tests
- NVDA screen reader
- JAWS screen reader (if available)
- Keyboard navigation
- Color contrast (WCAG AA)
- Focus indicators

## Output Format

```
🧪 UI Testing Complete

📁 Files Tested:
  - frontend/app/buscar/page.tsx

📊 Test Results: 28/30 PASSED (93%)

✅ Desktop Tests (10/10)
  ✅ Chrome 1920x1080 - Text renders correctly
  ✅ Firefox 1920x1080 - No layout shift
  ✅ Safari 1366x768 - Proper alignment
  ✅ Edge 1920x1080 - Spacing consistent
  ... (6 more passed)

✅ Tablet Tests (6/6)
  ✅ iPad Pro 768x1024 - Responsive layout
  ✅ iPad 768x1024 - Text wraps correctly
  ... (4 more passed)

⚠️  Mobile Tests (10/12)
  ✅ iPhone 13 375x667 - Readable text
  ✅ Galaxy S21 360x640 - No overflow
  ❌ iPhone SE 375x667 - Text truncation on small screen
  ❌ Small Android 320x568 - Horizontal scroll detected
  ... (8 more passed)

✅ Accessibility Tests (2/2)
  ✅ NVDA compatibility - Announces correctly
  ✅ Keyboard navigation - All elements reachable

🐛 Issues Found (2):
  1. Text truncates on iPhone SE (375x667) - LOW priority
  2. Horizontal scroll on very small screens (<360px) - LOW priority

🎯 Recommendations:
  1. Add ellipsis for text overflow on small screens
  2. Consider min-width media query for <360px

✅ Overall Status: PASS (minor issues acceptable)
   Safe to deploy with noted caveats.

📸 Visual Diff: .test-results/visual-diff-2026-02-10.html
📄 Full Report: .test-results/ui-test-report-2026-02-10.json
```

## Test Scenarios

### Standard (default)
- Basic rendering across viewports
- No layout breaks
- Text legibility

### Accessibility
- Screen reader compatibility
- Keyboard navigation
- Color contrast
- Focus indicators

### Visual Regression
- Screenshot comparison
- Pixel-perfect diff
- Layout shift detection

### Performance
- No CLS (Cumulative Layout Shift)
- Fast render times
- No jank

## Implementation

Uses:
- **Playwright** for automated testing
- **Lighthouse** for accessibility audits
- **Percy** (optional) for visual regression
- **axe-core** for a11y validation

## Related

- `update-copy.md` - Make text changes
- `validate-ux.md` - Validate UX quality
- `check-accessibility.md` - Accessibility review
