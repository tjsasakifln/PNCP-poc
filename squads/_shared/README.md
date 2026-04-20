# `squads/_shared/` — Contexto B2G compartilhado

Arquivos neste diretório formam o **contexto comum de domínio** que qualquer squad do projeto SmartLic (B2G — licitações públicas brasileiras) pode referenciar. O objetivo é evitar duplicação e garantir que todos os agentes "falem a mesma língua" sobre PNCP, modalidades, tabelas Supabase, feature flags, etc.

## Ordem de carga (agentes devem seguir)

Quando um agente de um squad é ativado, a ordem canônica de leitura é:

1. **`squads/_shared/<arquivos relevantes>.md`** — contexto de domínio comum
2. **`squads/<squad-name>/squad.yaml` (ou `config.yaml`)** — definição upstream do squad
3. **`squads/<squad-name>/config/smartlic-overlay.yaml`** — overrides B2G deste squad (se existir)
4. **`squads/<squad-name>/<agent>.md`** — agente do squad conforme workflow
5. **`squads/<squad-name>/<agent>.smartlic.md`** — overlay B2G do agente (se existir)

O overlay **nunca** edita os arquivos upstream — apenas acrescenta. Isso garante que re-sync do registry `aiox-squads` é zero-conflict (`rsync` ou `cp -r`).

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `domain-glossary.md` | PNCP, PCP v2, ComprasGov, SICAF, modalidade, viability, setor — definições canônicas |
| `supabase-schema.md` | Tabelas principais (`pncp_raw_bids`, `supplier_contracts`, `ingestion_*`, `profiles`, `search_results_cache`) + RPCs + invariantes |
| `api-contracts.md` | Rotas backend (`/buscar` SSE, `/setores`, `/v1/admin/cron-status`) + `response_model=` policy + timeout waterfall |
| `sectors-15.yaml` | Referência (não duplica) a `backend/sectors_data.yaml` — 15 setores B2G com keywords + exclusions |
| `tech-stack.md` | Versões exatas: FastAPI 0.129, Next 16, Python 3.12, Redis, ARQ, PostgreSQL 17, Supabase Auth |
| `feature-flags.md` | `DATALAKE_*`, `LLM_*`, `VIABILITY_*`, `SYNONYM_*`, `LLM_FALLBACK_PENDING_ENABLED` — flags + defaults |
| `invariants.md` | Timeout waterfall, zero-failure test policy, RLS em todas tabelas, Anti-hang rules |

## Coexistência com os 12 squads B2G internos

O diretório `squads/` raiz já contém 12 squads internos do SmartLic (`auth-debugger-squad`, `bug-investigation-squad`, `lei-14133-modalidades-squad`, etc.). Os squads `aiox-*` (vendored do registry `SynkraAI/aiox-squads`) coexistem:

- **Internos** (`<nome>-squad/`): tactical — hotfix, debug, UX microcopy, bugfix de feature específica
- **aiox (`aiox-<nome>/`)**: strategic — arquitetura frontend, pesquisa multi-fonte, SEO, memória longo prazo, jurisprudência

Ambos grupos podem ler `_shared/`. Conflito de skills é resolvido pelo `.claude/hooks/smart-router.cjs` via first-match-wins com padrões específicos.

## Quando modificar

- Nova tabela Supabase relevante → atualizar `supabase-schema.md`
- Nova rota com `response_model=` → atualizar `api-contracts.md`
- Novo feature flag → atualizar `feature-flags.md`
- Novo invariant cross-cutting → atualizar `invariants.md`

Estes arquivos são **fonte canônica dentro do contexto de squads** — `CLAUDE.md` raiz continua sendo a fonte principal do projeto, mas `_shared/` é o que agentes de squads consultam primeiro.

## Licensing (squads aiox-*)

Os squads sob `squads/aiox-*/` são **vendored** (cópias congeladas) do registry público `https://github.com/SynkraAI/aiox-squads` no commit `66118db856ef655b8cf5ba44eda963ad4d0b1d78` (fetch em 2026-04-20).

**Atribuição por squad:**

| Squad | LICENSE upstream | Observação |
|---|---|---|
| `aiox-apex` | MIT (© 2026 Synkra AIOS / Gabriel Gama) — presente em `squads/aiox-apex/LICENSE` | Licença preservada |
| `aiox-deep-research`, `aiox-dispatch`, `aiox-kaizen-v2`, `aiox-seo`, `aiox-legal-analyst` | Sem LICENSE explícito no upstream | Uso derivativo respeitando convenções do registry. Cada `UPSTREAM.md` registra SHA + fetch date para auditoria. |

**Overlays locais** (`config/smartlic-overlay.yaml` + `*.smartlic.md`) são obra derivativa do SmartLic sob os termos do registry. Modificações ao conteúdo upstream devem respeitar o LICENSE original do squad quando existente.

Para re-sync com upstream:
```bash
git clone https://github.com/SynkraAI/aiox-squads.git /tmp/aiox-sync
rsync -a /tmp/aiox-sync/squads/<name>/ /mnt/d/pncp-poc/squads/aiox-<name>/ \
  --exclude='config/smartlic-overlay.yaml' \
  --exclude='*.smartlic.*' \
  --exclude='UPSTREAM.md'
# Depois atualizar SHA em squads/aiox-<name>/UPSTREAM.md
```
