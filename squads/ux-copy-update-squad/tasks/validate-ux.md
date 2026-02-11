---
task: Validate UX Quality of Copy Changes
responsavel: "@ux-validator"
responsavel_type: agent
atomic_layer: task
elicit: false
Entrada: |
  - old_copy: Original text
  - new_copy: New text
  - user_context: Context about where the text appears
  - target_audience: Optional target user persona
Saida: |
  - ux_score: Score from 0-100
  - improvement_areas: List of areas that could be improved
  - recommendations: Specific recommendations
  - approval: Boolean indicating if change is approved
Checklist:
  - "[ ] Analyze clarity and comprehension"
  - "[ ] Evaluate user-centricity"
  - "[ ] Check tone consistency"
  - "[ ] Assess brevity and conciseness"
  - "[ ] Review accessibility considerations"
  - "[ ] Calculate UX score"
  - "[ ] Provide recommendations"
  - "[ ] Give approval decision"
---

# *validate-ux

Validates the UX quality of copy changes to ensure they maintain high user experience standards.

## Usage

```bash
@ux-validator

*validate-ux <old_copy> <new_copy>
*validate-ux <old_copy> <new_copy> --context "loading message"
*validate-ux <old_copy> <new_copy> --audience "small business owners"
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `old_copy` | string | Yes | Original text |
| `new_copy` | string | Yes | New text |
| `--context` | string | No | Where the text appears |
| `--audience` | string | No | Target audience |
| `--verbose` | flag | No | Detailed analysis output |

## Validation Criteria

### 1. Clarity (25 points)
- Is the message clear and unambiguous?
- Can users understand it immediately?
- Does it avoid confusing language?

### 2. User-Centricity (25 points)
- Does it focus on user benefits?
- Is it written from user perspective?
- Does it address user needs?

### 3. Tone Consistency (20 points)
- Matches brand voice guidelines?
- Appropriate for context?
- Professional yet friendly?

### 4. Brevity (15 points)
- Concise without losing meaning?
- No unnecessary words?
- Scannable and digestible?

### 5. Accessibility (15 points)
- Appropriate reading level?
- Jargon-free plain language?
- Screen reader compatible?

## Examples

### Example 1: Loading Message

```bash
*validate-ux "O PNCP está mais lento que o normal. Aguarde..." "Estamos trabalhando nisso, só mais um instante!"
```

**Output:**
```
✅ UX Validation Complete

📊 UX Score: 92/100 (Excellent)

📝 Analysis:

Clarity (24/25) ★★★★★
  ✅ Clear and unambiguous
  ✅ Immediately understandable
  ⚠️  Could specify what "isso" refers to

User-Centricity (24/25) ★★★★★
  ✅ Focuses on action being taken
  ✅ Reassuring tone
  ✅ Acknowledges user's wait

Tone Consistency (20/20) ★★★★★
  ✅ Matches brand voice perfectly
  ✅ Friendly and professional
  ✅ Appropriate for loading context

Brevity (14/15) ★★★★☆
  ✅ Concise and scannable
  ⚠️  Slightly longer than original

Accessibility (10/15) ★★★☆☆
  ✅ Plain language
  ✅ Screen reader compatible
  ⚠️  Could be more specific
  ⚠️  "Isso" may lack context for screen readers

🎯 Recommendations:
  1. Consider making "isso" more explicit: "Estamos processando sua busca"
  2. Alternative: "Só mais um instante, estamos buscando os melhores resultados!"

✅ Approval: APPROVED
   Change improves UX quality significantly.
```

### Example 2: Welcome Message

```bash
*validate-ux "Encontre oportunidades de contratação pública no Portal Nacional (PNCP)" "Encontre oportunidades de contratação pública mais adequadas para o momento de seu negócio." --context "logged area welcome"
```

**Output:**
```
✅ UX Validation Complete

📊 UX Score: 95/100 (Excellent)

📝 Analysis:

Clarity (25/25) ★★★★★
  ✅ Crystal clear message
  ✅ Immediately understandable
  ✅ No ambiguity

User-Centricity (25/25) ★★★★★
  ✅ Focuses on user's business needs
  ✅ Emphasizes relevance and fit
  ✅ "Seu negócio" creates personal connection

Tone Consistency (20/20) ★★★★★
  ✅ Professional and helpful
  ✅ Business-focused
  ✅ Value-oriented

Brevity (13/15) ★★★★☆
  ✅ Clear and concise
  ⚠️  Slightly longer (but justified)

Accessibility (12/15) ★★★★☆
  ✅ Plain language
  ✅ Jargon removed (PNCP)
  ✅ Screen reader friendly
  ⚠️  Could test with real users

🎯 Improvements over old copy:
  ✅ Removes technical acronym (PNCP)
  ✅ Shifts focus from system to user benefit
  ✅ More value-oriented messaging
  ✅ Emphasizes personalization and relevance

✅ Approval: APPROVED
   Significant improvement in user-centricity.
```

## Scoring Thresholds

| Score | Rating | Action |
|-------|--------|--------|
| 90-100 | Excellent | Approved, ready to ship |
| 70-89 | Good | Minor improvements suggested |
| 50-69 | Fair | Needs revision |
| 0-49 | Poor | Significant changes required |

## Output Format

```
✅ / ⚠️ / ❌ UX Validation [Status]

📊 UX Score: [score]/100 ([rating])

📝 Analysis:
  [Detailed breakdown by criteria]

🎯 Recommendations:
  [Numbered list of suggestions]

✅ / ❌ Approval: [APPROVED / NEEDS_REVISION]
   [Justification]
```

## Related Tasks

- `update-copy.md` - Apply changes after validation
- `check-accessibility.md` - Deep accessibility audit
- `validate-text.md` - Grammar and style check

## Notes

- Always validate BEFORE implementing changes
- Consider target audience context
- Balance brevity with clarity
- User testing trumps subjective judgment
