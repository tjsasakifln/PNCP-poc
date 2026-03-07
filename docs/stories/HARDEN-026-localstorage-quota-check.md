# HARDEN-026: localStorage Quota Check com Fallback

**Severidade:** BAIXA
**Esforço:** 10 min
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

Se usuário acumula 50+ searches (cada 100KB JSON), localStorage (5-10MB) pode exceder quota. Writes falham silenciosamente e searches salvas desaparecem ao recarregar.

## Critérios de Aceitação

- [x] AC1: Wrapper `safeSetItem()` com try/catch no setItem
- [x] AC2: Em caso de QuotaExceededError, evict items mais antigos
- [x] AC3: Usado em todos os localStorage writes do app
- [x] AC4: Teste unitário

## Arquivos Afetados

- `frontend/lib/storage.ts` — novo helper safeSetItem()
- `frontend/__tests__/lib/storage.test.ts` — 7 testes unitários
- 20 arquivos de produção atualizados para usar safeSetItem()

## Implementação

### `safeSetItem()` (`frontend/lib/storage.ts`)
- Try/catch em `localStorage.setItem()`
- Detecta `QuotaExceededError` (spec name + legacy codes 22/1014)
- Eviction cascade: `search_partial_*` → `smartlic_last_search`
- Retry uma vez após eviction; silently drop se ainda falhar

### Arquivos migrados (AC3)
- `app/(protected)/layout.tsx`
- `app/buscar/page.tsx`
- `app/buscar/hooks/useSearchFilters.ts`
- `app/buscar/components/SearchResults.tsx`
- `app/buscar/components/FeedbackButtons.tsx`
- `app/components/CookieConsentBanner.tsx`
- `app/components/ContextualTutorialTooltip.tsx`
- `app/components/ThemeProvider.tsx`
- `app/onboarding/page.tsx`
- `app/signup/page.tsx`
- `app/planos/page.tsx`
- `components/billing/TrialUpsellCTA.tsx`
- `components/Sidebar.tsx`
- `components/ui/Pagination.tsx`
- `components/ProfileCongratulations.tsx`
- `components/ProfileCompletionPrompt.tsx`
- `hooks/useUserProfile.ts`
- `hooks/useShepherdTour.ts`
- `hooks/useOnboarding.tsx`
- `lib/searchPartialCache.ts`
- `lib/savedSearches.ts`
- `lib/lastSearchCache.ts`

### Exceções (não migradas)
- `app/layout.tsx:138` — inline `<script>` pré-hydration (não importa módulos)
- `__tests__/` e `e2e-tests/` — test setup (localStorage direto é correto)
