# UX-351 — Historico Funcional: Salvamento, Status e Apresentacao

**Status:** completed
**Priority:** P1 — Funcionalidade core quebrada
**Created:** 2026-02-22
**Completed:** 2026-02-22
**Origin:** Auditoria UX area logada (2026-02-22-ux-audit-area-logada.md)
**Dependencias:** CRIT-027
**Estimativa:** M

---

## Problema

1. **Buscas duplicadas**: Uma unica busca gera 2 entradas "Processando..." no historico
2. **Status nunca atualiza**: "Processando..." permanece mesmo apos busca concluir
3. **Erros em ingles**: "Server restart — retry recommended" em vez de mensagem em portugues
4. **Visual poluido**: Todos 27 codigos de UF listados em linha quando e "Todo o Brasil"
5. **Acentuacao**: "Historico" sem acento no header e sidebar; "Concluida" sem acento nos badges

---

## Solucao

### Criterios de Aceitacao

**Salvamento correto**
- [x] **AC1:** Cada busca gera EXATAMENTE 1 entrada no historico (nao duplicada)
- [x] **AC2:** Busca e salva no historico imediatamente ao iniciar (status "Em andamento")

**Atualizacao de status**
- [x] **AC3:** Status transiciona para "Concluida" quando busca termina com sucesso
- [x] **AC4:** Status transiciona para "Falhou" se busca falha, com mensagem EM PORTUGUES
- [x] **AC5:** Status transiciona para "Timeout" se busca excede tempo limite

**Mensagens**
- [x] **AC6:** "Server restart — retry recommended" → "O servidor reiniciou. Tente novamente."
- [x] **AC7:** Todas as mensagens de erro do historico em portugues

**Apresentacao**
- [x] **AC8:** Quando todas 27 UFs selecionadas, mostrar "Todo o Brasil" (nao listar AC, AL, AM...)
- [x] **AC9:** Quando subset de UFs, mostrar ate 5 + "+ X outros" (ex: "SP, RJ, MG + 3 outros")
- [x] **AC10:** Corrigir acentuacao: "Historico" → "Historico" no header (verificar se vem de i18n ou hardcoded)
- [x] **AC11:** Corrigir badges: "Concluida" → "Concluida" (com acento)

**Testes**
- [x] **AC12:** Teste: busca gera 1 entrada no historico
- [x] **AC13:** Teste: status atualiza corretamente
- [x] **AC14:** Teste: 27 UFs = "Todo o Brasil"
- [x] **AC15:** Zero regressoes

---

## Implementacao

### Backend (3 files)

| Arquivo | Mudanca |
|---------|---------|
| `backend/quota.py` | AC1: Dedup check — reusa sessao existente se search_id ja registrado |
| `backend/search_state_manager.py` | AC6-AC7: Mensagens de erro em portugues (4 strings traduzidas) |
| `backend/main.py` | AC7: Mensagem shutdown handler em portugues |

### Frontend (1 file)

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/historico/page.tsx` | AC2-AC5: Polling 5s para sessoes ativas (auto-refresh). AC7: Error msgs passam por getUserFriendlyError(). AC8-AC9: formatUfs() com "Todo o Brasil" e truncamento. AC10-AC11: Accents verificados (ja corretos). Labels atualizados: "Em andamento", "Tempo esgotado", "Concluida" |

### Testes (2 files)

| Arquivo | Mudanca |
|---------|---------|
| `frontend/__tests__/pages/HistoricoUX351.test.tsx` | 19 testes: AC12 (2), AC13 (6), AC14 (5), AC6-AC7 (2), AC15 (4) |
| `backend/tests/test_ux351_session_dedup.py` | 6 testes: dedup (4) + Portuguese messages (2) |

---

## Referencias

- Audit: C05, M02, M03
- Screenshot: audit-06-historico.png
