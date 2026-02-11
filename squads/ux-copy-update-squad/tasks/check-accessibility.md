---
task: Check Accessibility Compliance
responsavel: "@ux-validator"
responsavel_type: agent
atomic_layer: task
elicit: false
Entrada: |
  - text_content: Text to check
  - ui_context: Where text appears (button, label, error, etc.)
Saida: |
  - accessibility_score: Score from 0-100
  - wcag_compliance: Level (A, AA, AAA or fails)
  - issues: List of accessibility issues found
  - recommendations: Suggested fixes
Checklist:
  - "[ ] Check reading level appropriateness"
  - "[ ] Verify screen reader compatibility"
  - "[ ] Check plain language usage"
  - "[ ] Validate context sufficiency"
  - "[ ] Check abbreviations/jargon"
  - "[ ] Provide WCAG compliance rating"
---

# *check-accessibility

Verifies text meets WCAG 2.1 Level AA accessibility standards.

## Usage

```bash
@ux-validator

*check-accessibility "text to check"
*check-accessibility "text" --context "error message"
*check-accessibility "text" --context "button label"
```

## WCAG 2.1 Criteria Checked

### 3.1 Readable
- **3.1.3** Unusual Words - Jargon explained
- **3.1.4** Abbreviations - Expanded on first use
- **3.1.5** Reading Level - Appropriate complexity

### 3.3 Input Assistance
- **3.3.1** Error Identification - Clear description
- **3.3.2** Labels/Instructions - Sufficient guidance
- **3.3.3** Error Suggestion - Actionable fixes
- **3.3.4** Error Prevention - Confirmations provided

## Output Example

```
✅ Accessibility Check Complete

📊 Accessibility Score: 90/100
🎯 WCAG Compliance: Level AA

✅ Passed Criteria:
  - 3.1.3 Unusual Words: No unexplained jargon
  - 3.1.5 Reading Level: Appropriate (Grade 8)
  - 3.3.1 Error Identification: Clear description
  - 3.3.3 Error Suggestion: Actionable guidance

⚠️  Potential Issues:
  - 3.1.4 Abbreviations: "PNCP" not expanded
  - Context: "Aguarde..." lacks specific action

🎯 Recommendations:
  1. Expand "PNCP" on first mention
  2. Provide context: "Aguardando resposta do servidor..."
  3. Ensure screen reader announces properly

✅ Result: COMPLIANT (Level AA)
```

## Screen Reader Testing

Text is validated for:
- Semantic meaning preserved
- No context lost when read linearly
- Proper announcement timing
- Pause points for comprehension

## Related

- `validate-ux.md` - UX quality review
- `validate-text.md` - Text quality check
