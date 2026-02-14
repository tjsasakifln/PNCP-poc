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
- [ ] **AC1:** SETORES_FALLBACK em `useSearchFilters.ts` tem exatamente os mesmos IDs e nomes que `sectors_data.yaml` (12 setores). Cada entrada tem: id, name, description.
- [ ] **AC2:** SECTORS em `signup/page.tsx` tem os mesmos 12 setores + `{ id: "outro", name: "Outro" }` (total: 13).
- [ ] **AC3:** Nenhum ID inventado (como `alimentacao`, `escritorio`, `construcao`, `seguranca`, `servicos`) existe no frontend.
- [ ] **AC4:** Script `scripts/sync-setores-fallback.js` sincroniza tanto `useSearchFilters.ts` quanto `signup/page.tsx`.

### Verificação
- [ ] **AC5:** Teste automatizado: `test_frontend_fallback_matches_backend()` — lê sectors_data.yaml e compara com SETORES_FALLBACK (importação direta ou parse de arquivo).
- [ ] **AC6:** `npm test` frontend passa com os novos setores.
- [ ] **AC7:** Dropdown de setores na busca mostra todos os setores corretos.
- [ ] **AC8:** Dropdown de setores no signup mostra todos os setores corretos + "Outro".

### Regressão
- [ ] **AC9:** Busca por setor funciona para todos os 12 setores (IDs corretos propagados).
- [ ] **AC10:** Signup com seleção de setor funciona.
- [ ] **AC11:** localStorage sector cache invalidado (TTL ou versão) para forçar recarga.

## Definition of Done
- Todos os ACs checked
- `pytest` sem regressões
- `npm test` sem regressões
- TypeScript clean
