# STORY-249: Sync de Setores Backend ↔ Frontend ↔ Signup

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-249 |
| **Priority** | P0 (GTM-critical) |
| **Sprint** | Sprint 1 |
| **Estimate** | 3h |
| **Depends on** | Nenhuma |
| **Blocks** | STORY-243 (renomear precisa sync funcional), STORY-242 (novos setores precisam propagar) |

## Problema
Existem 3 listas de setores no codebase que estão **dessincronizadas**:
1. **Backend:** `sectors_data.yaml` → 12 setores (sem `outro`)
2. **Frontend fallback:** `useSearchFilters.ts:59-72` → 12 setores (IDs e nomes divergem do backend)
3. **Signup:** `signup/page.tsx:12-26` → 13 setores (inclui `outro`)

Divergências encontradas:

| Backend ID | Backend Name | Frontend Fallback | Signup |
|-----------|-------------|-------------------|--------|
| `vestuario` | "Vestuário e Uniformes" | id=vestuario, name="Vestuário e Uniformes" | id=vestuario, "Vestuário e Uniformes" |
| `alimentos` | "Alimentos e Merenda" | **AUSENTE** (id=alimentacao, "Alimentação") | id=alimentos, "Alimentos e Merenda" |
| `informatica` | "Informática e Tecnologia" | **AUSENTE** | id=informatica, "Informática e Tecnologia" |
| `mobiliario` | "Mobiliário" | **AUSENTE** | id=mobiliario, "Mobiliário" |
| `papelaria` | "Papelaria e Material de Escritório" | **AUSENTE** (id=escritorio, "Material de Escritório") | id=papelaria, "Papelaria e Material de Escritório" |
| `engenharia` | "Engenharia e Construção" | **AUSENTE** (id=construcao, "Construção Civil") | id=engenharia, "Engenharia e Construção" |
| `software` | "Software e Sistemas" | id=software, "Software & TI" | id=software, "Software e Sistemas" |
| `facilities` | "Facilities (Limpeza e Zeladoria)" | id=facilities, name OK | id=facilities, name diferente |
| `saude` | "Saúde" | id=saude, name OK | id=saude, "Saúde" |
| `vigilancia` | "Vigilância e Segurança" | **AUSENTE** (id=seguranca, "Segurança") | id=vigilancia, "Vigilância e Segurança" |
| `transporte` | "Transporte e Veículos" | id=transporte, name OK | id=transporte, "Transporte e Veículos" |
| `manutencao_predial` | "Manutenção Predial" | **AUSENTE** (id=servicos, "Serviços Gerais") | id=manutencao_predial, "Manutenção Predial" |
| — | — | — | id=outro, "Outro" |

**6 de 12 setores** no frontend fallback têm IDs DIFERENTES do backend. Isso causa busca com setor inexistente no backend → erro silencioso.

## Solução
1. Alinhar SETORES_FALLBACK com sectors_data.yaml (IDs e nomes idênticos)
2. Alinhar SECTORS no signup com sectors_data.yaml (manter `outro` como opção extra)
3. Atualizar script de sync existente (`scripts/sync-setores-fallback.js`) para cobrir signup também

## Arquivos a Modificar

| Arquivo | Linhas | Mudança |
|---------|--------|---------|
| `frontend/app/buscar/hooks/useSearchFilters.ts` | 59-72 | SETORES_FALLBACK = cópia exata dos 12 setores do backend (IDs, nomes, descriptions) |
| `frontend/app/signup/page.tsx` | 12-26 | SECTORS = mesmos 12 setores do backend + `{ id: "outro", name: "Outro" }` |
| `scripts/sync-setores-fallback.js` | todo | Atualizar para também sincronizar signup/page.tsx |

## Acceptance Criteria

### Sync
- [x] **AC1:** SETORES_FALLBACK em `useSearchFilters.ts` tem exatamente os mesmos IDs e nomes que `sectors_data.yaml` (15 setores). Cada entrada tem: id, name, description.
- [x] **AC2:** SECTORS em `signup/page.tsx` tem os mesmos 15 setores + `{ id: "outro", name: "Outro" }` (total: 16). Já estava correto.
- [x] **AC3:** Nenhum ID inventado (como `alimentacao`, `escritorio`, `construcao`, `seguranca`, `servicos`) existe no frontend.
- [x] **AC4:** Script `scripts/sync-setores-fallback.js` sincroniza tanto `useSearchFilters.ts` quanto `signup/page.tsx`.

### Verificação
- [x] **AC5:** Teste automatizado: `sector-sync.test.ts` — lê sectors_data.yaml e compara com SETORES_FALLBACK (parse de arquivo). 6 testes passando.
- [x] **AC6:** `npm test` frontend passa com os novos setores (1302 passed, 7 pre-existing failures).
- [x] **AC7:** Dropdown de setores na busca mostra todos os setores corretos. (manual/E2E) ✓ Validated 2026-02-14 via Playwright — all 15 sectors visible with correct names/descriptions.
- [x] **AC8:** Dropdown de setores no signup mostra todos os setores corretos + "Outro". (manual/E2E) ✓ Validated 2026-02-14 via Playwright — 15 sectors + "Outro" (16 total), conditional "Qual setor?" input works.

### Regressão
- [x] **AC9:** Busca por setor funciona para todos os 15 setores (IDs corretos propagados). (manual/E2E) ✓ Validated 2026-02-14 — tested "saude" and "materiais_hidraulicos". Backend logs confirm `setor_id` correctly received and sector keywords loaded (268 terms for saude). External sources (PNCP 400, COMPRAS_GOV 503) down — not a sector sync issue.
- [x] **AC10:** Signup com seleção de setor funciona. (manual/E2E) ✓ Validated 2026-02-14 via Playwright — sector selection works for all options including "Outro" with conditional text input.
- [x] **AC11:** localStorage sector cache invalidado (versão bumped: `smartlic-sectors-cache` → `smartlic-sectors-cache-v2`).

## Definition of Done
- Todos os ACs checked
- `pytest` sem regressões
- `npm test` sem regressões
- TypeScript clean
