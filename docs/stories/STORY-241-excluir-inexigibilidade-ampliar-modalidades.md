# STORY-241: Excluir Inexigibilidade e Ampliar Modalidades Competitivas

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-241 |
| **Priority** | P0 (GTM-critical) |
| **Sprint** | Sprint 1 |
| **Estimate** | 6h |
| **Depends on** | Nenhuma |
| **Blocks** | STORY-240 (busca abertas usa modalidades corretas) |

## Problema
O SmartLic busca apenas modalidade 6 (Pregão Eletrônico). Isso perde oportunidades reais em Concorrência (4), Concorrência Presencial (5) e Pregão Presencial (7). Além disso, Inexigibilidade (código 9 no PNCP / enum 7 no schemas.py) e Inaplicabilidade (14) são modalidades com vencedor pré-definido — puro ruído para o usuário.

## Investigação Técnica

### Mapeamento de Códigos

**ATENÇÃO: Existem DUAS numerações diferentes no codebase:**

| PNCP API (config.py) | Nome | Lei | Ação |
|----|------|-----|------|
| 1 | Leilão Eletrônico | 14.133/21 | Manter (não default) |
| 2 | Diálogo Competitivo | 14.133/21 | Manter (não default) |
| 3 | Concurso | 14.133/21 | Manter (não default) |
| 4 | Concorrência Eletrônica | 14.133/21 | **ADICIONAR ao default** |
| 5 | Concorrência Presencial | 14.133/21 | **ADICIONAR ao default** |
| 6 | Pregão Eletrônico | 14.133/21 | Manter (já é default) |
| 7 | Pregão Presencial | 14.133/21 | **ADICIONAR ao default** |
| 8 | Dispensa | 14.133/21 | Manter (não default, volume excessivo) |
| 9 | Inexigibilidade | 14.133/21 | **EXCLUIR** |
| 10 | Manifestação de Interesse | 14.133/21 | Manter (não default) |
| 11 | Pré-qualificação | 14.133/21 | Manter (não default) |
| 12 | Credenciamento | 14.133/21 | Manter (não default) |
| 13 | Leilão Presencial | 14.133/21 | Manter (não default) |
| 14 | Inaplicabilidade | 14.133/21 | **EXCLUIR** |
| 15 | Chamada Pública | 14.133/21 | Manter (não default) |

**schemas.py ModalidadeContratacao enum (DIFERENTE do config.py!):**
- Enum usa: 1=Pregão Eletrônico, 2=Pregão Presencial, 3=Concorrência, 6=Dispensa, 7=Inexigibilidade, 9=Leilão, 10=Diálogo, 11=Concurso
- config.py MODALIDADES_PNCP usa os códigos REAIS da API

### Arquivos a Modificar

| Arquivo | Linhas | Mudança |
|---------|--------|---------|
| `backend/config.py` | 33-35 | `DEFAULT_MODALIDADES = [4, 5, 6, 7]` + nova constante `MODALIDADES_EXCLUIDAS = [9, 14]` |
| `backend/config.py` | 12-28 | Adicionar comentário sobre exclusões |
| `backend/pncp_client.py` | 381, 941 | Aplicar filtro de exclusão quando `modalidades=None` |
| `backend/schemas.py` | 30-52 | Atualizar `ModalidadeContratacao` enum — reconciliar com códigos PNCP reais (4=Concorrência Eletrônica, 5=Concorrência Presencial) |
| `backend/schemas.py` | 339-349 | Atualizar description do campo `modalidades` e remover menção a Lei 8.666 (4 e 5 agora são Nova Lei) |
| `frontend/components/ModalidadeFilter.tsx` | 30-74 | Adicionar Concorrência Eletrônica (4), Concorrência Presencial (5), marcar como popular. Remover Inexigibilidade (7/9). |
| `frontend/components/ModalidadeFilter.tsx` | 30 | Reconciliar códigos com PNCP API real |
| `backend/tests/test_pncp_client.py` | 651-665 | Atualizar teste de DEFAULT_MODALIDADES |
| `backend/tests/snapshots/openapi_schema.json` | 315 | Atualizar snapshot após mudança no schema |

### Decisão Arquitetural
- `MODALIDADES_EXCLUIDAS` é uma constante em `config.py`, não um feature flag. Inexigibilidade e Inaplicabilidade NUNCA são úteis para o usuário.
- O `ModalidadeContratacao` enum precisa ser reconciliado com os códigos reais da API PNCP para evitar confusão futura.

## Acceptance Criteria

### Backend
- [ ] **AC1:** `DEFAULT_MODALIDADES = [4, 5, 6, 7]` em `config.py`. Comentário explica a escolha (modalidades competitivas).
- [ ] **AC2:** `MODALIDADES_EXCLUIDAS = [9, 14]` em `config.py`. Comentário explica: "vencedor pré-definido = ruído".
- [ ] **AC3:** `pncp_client.py:fetch_all()` e `buscar_todas_ufs_paralelo()` — quando `modalidades=None`, usa `DEFAULT_MODALIDADES`. Quando lista explícita fornecida, filtra removendo qualquer modalidade em `MODALIDADES_EXCLUIDAS`.
- [ ] **AC4:** `ModalidadeContratacao` enum atualizado para mapear códigos PNCP reais (4=Concorrência Eletrônica, 5=Concorrência Presencial, 6=Pregão Eletrônico, 7=Pregão Presencial, 8=Dispensa, 12=Credenciamento).
- [ ] **AC5:** Schema field description de `modalidades` atualizado com códigos corretos e nota sobre exclusão de 9 e 14.
- [ ] **AC6:** Testes unitários: `test_default_modalidades_includes_competitive()` verifica [4,5,6,7]. `test_excluded_modalidades_never_fetched()` verifica que 9 e 14 são filtrados.

### Frontend
- [ ] **AC7:** `ModalidadeFilter.tsx` — Concorrência Eletrônica (4) e Concorrência Presencial (5) adicionados. Pregão Presencial (7) adicionado. Popular=[4, 5, 6, 7]. Inexigibilidade removida.
- [ ] **AC8:** Frontend não permite selecionar modalidades 9 ou 14 (não aparecem na lista).
- [ ] **AC9:** Testes de componente `ModalidadeFilter` atualizados.

### Regressão
- [ ] **AC10:** OpenAPI schema snapshot atualizado após mudanças em schemas.py.
- [ ] **AC11:** Todos os testes existentes de modalidade passam ou são atualizados.

## Definition of Done
- Todos os ACs checked
- `pytest` sem regressões
- `npm test` sem regressões
- TypeScript clean
