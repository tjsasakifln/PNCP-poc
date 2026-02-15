# Term Validation UI Implementation - Summary

## Overview
Implemented comprehensive client-side term validation with clear user feedback about ignored terms, mirroring backend validation logic from `filter.py:validate_terms()`.

## Changes Made

### 1. Type Definitions (`frontend/app/types.ts`)
Added new interface for term validation metadata:
```typescript
interface TermValidationMetadata {
  termos_utilizados: string[];
  termos_ignorados: string[];
  motivos_ignorados: Record<string, string>;
}
```

Updated `BuscaResult` interface to include optional `metadata` field for new format while maintaining backward compatibility with old `termos_utilizados` and `stopwords_removidas` fields.

### 2. Client-Side Validation Logic (`frontend/app/buscar/page.tsx`)

#### New Function: `validateTermsClientSide(terms: string[]): TermValidation`
Mirrors backend validation from `backend/filter.py:validate_terms()`:
- **Validation 1**: Empty terms after trim
- **Validation 2**: Stopwords (single-word terms only)
- **Validation 3**: Minimum length (4 chars, single-word terms only)
- **Validation 4**: Special characters (allows letters, numbers, hyphens, accents)

Multi-word phrases are exempt from min-length and stopword checks.

#### Helper Functions
- `updateTermValidation(terms: string[])` - Validates and updates state
- `addTerms(newTerms: string[])` - Adds terms with automatic validation
- `removeTerm(termToRemove: string)` - Removes term with validation update

#### State Management
- New state: `termValidation: TermValidation | null`
- useEffect hook to auto-validate when `searchMode === "termos"` or `termosArray` changes

### 3. UI Components

#### Pre-Search Warning Alert
Displays BEFORE search execution when terms are added:
```tsx
{termValidation && termValidation.ignored.length > 0 && (
  <Alert variant="warning">
    ⚠️ Atenção: N termo(s) não será(ão) utilizado(s) na busca
    • "term": Reason (e.g., "Muito curto (mínimo 4 caracteres)")
    • "de": Palavra comum não indexada (stopword)
  </Alert>
)}
```

**Features:**
- Warning icon with amber/yellow styling
- Lists each ignored term with specific reason
- Helpful tip about minimum length and stopwords
- Automatically shown/hidden based on validation state

#### Button State
- **Disabled** when `termValidation.valid.length === 0` (no valid terms)
- Button text adapts:
  - Normal: "Buscar {sectorName}" or "Buscar N termos"
  - No valid terms: "Adicione termos válidos para buscar"

#### Post-Search Metadata Display
Enhanced results banner showing:
- **Terms used**: Green badges for utilized terms
- **Terms ignored**: Collapsible `<details>` section with reasons
- Backward compatible with old `termos_utilizados` / `stopwords_removidas` format

```tsx
<div className="bg-surface-1 border border-border rounded-card p-4">
  Termos utilizados na busca: [badge] [badge] [badge]

  <details>
    <summary>N termo(s) não utilizado(s)</summary>
    • "term": Reason
    • "term2": Reason
  </details>
</div>
```

### 4. Event Handler Updates
All input handlers now use centralized `addTerms()` / `removeTerm()`:
- `onChange` (comma-separated input)
- `onKeyDown` (Enter key, Backspace)
- `onPaste` (comma-separated paste)
- Tag remove button (`onClick`)

### 5. Tests (`frontend/__tests__/termValidation.test.tsx`)
Comprehensive test suite with **17 test cases**:

#### Unit Tests
- Valid single-word terms
- Valid multi-word phrases
- Empty terms rejection
- Stopword rejection (single-word only)
- Multi-word phrases with stopwords (allowed)
- Short terms rejection (< 4 chars, single-word only)
- Multi-word phrases with short words (allowed)
- Special characters rejection
- Hyphens and accents acceptance
- Mixed valid/invalid terms
- Case insensitivity
- Accent stripping for stopword detection

#### Real-World Scenarios
- Construction terms (terraplenagem, pavimentação)
- Facilities management terms (limpeza, conservação)
- IT procurement terms (servidor, notebook, licença de software)
- All stopwords input (valid.length === 0)
- Trailing/leading spaces handling

**All tests passing (17/17).**

## Validation Rules Summary

| Rule | Applies To | Reason Message | Example |
|------|-----------|----------------|---------|
| Empty | All | "Termo vazio ou apenas espaços" | `""`, `"  "` |
| Stopword | Single-word only | "Palavra comum não indexada (stopword)" | `"de"`, `"para"` |
| Min Length | Single-word only | "Muito curto (mínimo 4 caracteres)" | `"abc"` |
| Special Chars | All | "Contém caracteres especiais não permitidos" | `"termo@inválido"` |

**Multi-word phrases** like "serviço de limpeza" are **exempt** from stopword and min-length checks.

## UX Flow

### Before Search (Proactive Validation)
1. User adds term via comma, Enter, or paste
2. Term is immediately validated client-side
3. If invalid, warning alert appears above input
4. If ALL terms invalid, button is disabled with message "Adicione termos válidos"

### During Search
- Button disabled, loading spinner shown
- Validation state preserved (no re-validation during loading)

### After Search (Server Response)
- New metadata format (`result.metadata`) takes precedence
- Falls back to old format (`result.termos_utilizados`, `result.stopwords_removidas`)
- Collapsible section shows ignored terms with backend reasons
- Green badges for utilized terms

## Backward Compatibility
- Old API responses without `metadata` still work
- Falls back to `termos_utilizados` / `stopwords_removidas` display
- Client-side validation is independent of backend response format

## Files Modified
1. `frontend/app/types.ts` - Type definitions
2. `frontend/app/buscar/page.tsx` - Validation logic + UI
3. `frontend/__tests__/termValidation.test.tsx` - Test suite (new file)

## Testing
```bash
# Run term validation tests
npm test -- termValidation.test.tsx

# TypeScript check (no errors)
npx tsc --noEmit --pretty
```

## Next Steps (Optional Enhancements)
1. Add tooltip on input field explaining validation rules
2. Add link to glossary page (when created) from warning alert
3. Add analytics tracking for ignored terms patterns
4. Consider "did you mean?" suggestions for common misspellings
5. Add visual indicators (checkmark/X) next to each term tag

## Screenshots (To be captured)
1. Warning alert with multiple ignored terms
2. Button disabled state ("Adicione termos válidos")
3. Results metadata with collapsible ignored terms section
4. Multi-word phrase with stopwords (accepted)

---

**Implementation Date**: 2026-02-10
**Story**: Term Validation UI Feedback
**Developer**: @dev (Frontend)
