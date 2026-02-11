---
task: Validate Text Quality
responsavel: "@copy-editor"
responsavel_type: agent
atomic_layer: task
elicit: false
Entrada: |
  - text: Text to validate
  - context: Optional context (welcome, loading, error, etc.)
  - target_audience: Optional target persona
Saida: |
  - validation_result: pass/fail status
  - suggestions: List of improvement suggestions
  - quality_score: Score from 0-100
Checklist:
  - "[ ] Check grammar and spelling"
  - "[ ] Validate tone consistency"
  - "[ ] Check clarity and brevity"
  - "[ ] Verify brand voice alignment"
  - "[ ] Provide actionable suggestions"
---

# *validate-text

Validates text quality including grammar, style, tone, and brand voice consistency.

## Usage

```bash
@copy-editor

*validate-text "text to validate"
*validate-text "text" --context "error message"
*validate-text "text" --audience "small business owners"
```

## Validation Checks

### 1. Grammar & Spelling
- Correct Portuguese grammar (pt-BR)
- No spelling errors
- Proper punctuation

### 2. Tone & Style
- Professional but friendly
- User-centric language
- Action-oriented phrasing

### 3. Clarity
- Clear and unambiguous
- No jargon unless necessary
- Concise without losing meaning

### 4. Brand Voice (BidiQ)
- Helpful and supportive
- Business-focused
- Confidence-inspiring

## Output Example

```
✅ Text Validation Complete

📊 Quality Score: 85/100 (Good)

📝 Analysis:

Grammar & Spelling (20/20) ★★★★★
  ✅ No grammar errors
  ✅ Correct punctuation
  ✅ Proper Portuguese (pt-BR)

Tone & Style (18/20) ★★★★☆
  ✅ Professional and friendly
  ⚠️  Could be more action-oriented

Clarity (15/20) ★★★☆☆
  ⚠️  "Isso" lacks specific context
  ✅ Generally understandable

Brand Voice (17/20) ★★★★☆
  ✅ Matches BidiQ tone
  ⚠️  Could emphasize value more

Brevity (15/20) ★★★☆☆
  ⚠️  Could be more concise

🎯 Suggestions:
  1. Replace "isso" with specific action for clarity
  2. Add value-oriented phrase
  3. Consider shorter alternative

✅ Result: PASS (with minor improvements suggested)
```
