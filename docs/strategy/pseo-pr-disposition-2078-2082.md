# Disposição dos PRs pSEO antigos — #2118

Arquitetura vigente: ADR-STRAT-001. Estes PRs nasceram sob o SaaS + DataLake SmartLic.

| PR | Título | Destino | O que aproveitar |
|---|---|---|---|
| #2078 | split `lib/programmatic.ts` | SUPERSEDED / CLOSE_RECOMMENDED | Refactor sem contrato de eligibility. Não mergear. |
| #2079 | SEOSemaphore | SALVAGED | Ideia de pool protection → `backend/public_read/isolation.py` |
| #2080 | fetchWithBudget unificado | SUPERSEDED | Já existe `frontend/lib/safe-fetch.ts` no HEAD |
| #2081 | loading skeletons pSEO | STILL_VALID (ideia) / CLOSE_RECOMMENDED | Skeleton é UX; reabrir só depois do eligibility gate |
| #2082 | error boundaries por grupo | SALVAGED | Complementa ADR-SEO-001; reimplementar no template novo se faltar |

Não fazer merge mecânico. Nenhum destes PRs introduz `public_read_v1`, marca CONFENGE ou eligibility.
