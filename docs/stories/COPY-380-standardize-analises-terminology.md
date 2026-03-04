# STORY-COPY-380: Padronizar terminologia "análises" em vez de "buscas" em todo user-facing copy

**Prioridade:** P3 (consistência terminológica)
**Escopo:** Frontend e backend — múltiplos arquivos
**Estimativa:** L
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

O codebase alterna entre "buscas" e "análises" para descrever a mesma ação. CLAUDE.md proíbe "busca" em texto user-facing.

- **Cluster 4 (Godin):** Terminologia inconsistente fragmenta identidade de marca.
- **Cluster 3 (Geisler):** "Uma palavra = uma coisa. Sempre."
- **Cluster 3 (Handley):** Style guide é contrato com o usuário.

A palavra correta é "análise" porque:
1. É o que o usuário realmente recebe (filtrado + classificado + avaliado por IA), não apenas uma "busca"
2. "Análise" implica trabalho intelectual e justifica o preço

## Critérios de Aceitação

- [x] AC1: Audit completo de strings user-facing que usam "busca(s)" → substituir por "análise(s)" onde aplicável
- [x] AC2: Exceções permitidas: "Buscar oportunidades" como label de botão/CTA principal (verbo é ok); "buscar" como verbo de ação em tour steps
- [x] AC3: "Buscando licitações" em loading → "Analisando oportunidades" (coberto por STORY-COPY-376)
- [x] AC4: Dashboard stats: "buscas realizadas" → "análises realizadas"
- [x] AC5: Navigation: menu item "Buscar" pode permanecer (é verbo, não substantivo)
- [x] AC6: Testes atualizados para novas strings

## Copy Recomendada

Regra geral:
- **Substantivo:** "análise(s)" (nunca "busca(s)")
- **Verbo:** "analisar" preferido, "buscar" tolerado em CTAs de ação
- **Loading:** "Analisando..." (nunca "Buscando...")

## Princípios Aplicados

- **Godin (Brand):** Consistência terminológica = identidade de marca
- **Geisler (SaaS Conversion):** Uma palavra, um significado, sempre
- **Handley (Brand):** Style guide é contrato com o usuário

## File List

**Backend source (11 files):** routes/search.py, routes/reports.py, routes/bid_analysis.py, search_pipeline.py, llm.py, pncp_client.py, templates/emails/quota.py, templates/emails/trial.py, templates/emails/welcome.py, templates/emails/digest.py, templates/emails/alert_digest.py

**Backend tests (8 files):** test_gtm_fix_041_042.py, test_pncp_date_formats.py, test_resilience_a01.py, test_search_error_codes.py, test_stab004_never_lose_data.py, test_stab009_async_search.py, test_email_templates.py, test_alert_digest_template.py, test_digest_template.py

**Frontend source (~30 files):** buscar/page.tsx, buscar/hooks/useSearch.ts, buscar/components/SearchForm.tsx, buscar/components/SearchResults.tsx, buscar/components/SearchStateManager.tsx, buscar/components/SourceStatusGrid.tsx, buscar/types/searchPhase.ts, dashboard/page.tsx, historico/page.tsx, components/SavedSearchesDropdown.tsx, components/Breadcrumbs.tsx, lib/error-messages.ts, lib/savedSearches.ts, api/buscar/route.ts, api/download/route.ts, api/search-history/route.ts, components/billing/PaymentRecoveryModal.tsx, + pages (ajuda, planos, privacidade, sobre, termos, features, pricing, blog)

**Frontend tests (~40 files):** All test files referencing "busca(s)" updated to "análise(s)"

## Evidência

- Atual: "buscas" e "análises" usados intercambiavelmente em dashboard, quota messages, loading states
- Regra CLAUDE.md: "busca" listed as banned term in user-visible text
