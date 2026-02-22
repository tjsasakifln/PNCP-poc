# UX-351 — Historico Funcional: Salvamento, Status e Apresentacao

**Status:** pending
**Priority:** P1 — Funcionalidade core quebrada
**Created:** 2026-02-22
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
- [ ] **AC1:** Cada busca gera EXATAMENTE 1 entrada no historico (nao duplicada)
- [ ] **AC2:** Busca e salva no historico imediatamente ao iniciar (status "Em andamento")

**Atualizacao de status**
- [ ] **AC3:** Status transiciona para "Concluida" quando busca termina com sucesso
- [ ] **AC4:** Status transiciona para "Falhou" se busca falha, com mensagem EM PORTUGUES
- [ ] **AC5:** Status transiciona para "Timeout" se busca excede tempo limite

**Mensagens**
- [ ] **AC6:** "Server restart — retry recommended" → "O servidor reiniciou. Tente novamente."
- [ ] **AC7:** Todas as mensagens de erro do historico em portugues

**Apresentacao**
- [ ] **AC8:** Quando todas 27 UFs selecionadas, mostrar "Todo o Brasil" (nao listar AC, AL, AM...)
- [ ] **AC9:** Quando subset de UFs, mostrar ate 5 + "+ X outros" (ex: "SP, RJ, MG + 3 outros")
- [ ] **AC10:** Corrigir acentuacao: "Historico" → "Historico" no header (verificar se vem de i18n ou hardcoded)
- [ ] **AC11:** Corrigir badges: "Concluida" → "Concluida" (com acento)

**Testes**
- [ ] **AC12:** Teste: busca gera 1 entrada no historico
- [ ] **AC13:** Teste: status atualiza corretamente
- [ ] **AC14:** Teste: 27 UFs = "Todo o Brasil"
- [ ] **AC15:** Zero regressoes

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/historico/page.tsx` | AC8-AC11 apresentacao + acentuacao |
| `frontend/hooks/useSearch.ts` | AC1-AC2 salvamento correto (verificar se salva 2x) |
| `backend/routes/sessions.py` | Verificar se cria sessao duplicada |
| `frontend/__tests__/historico*.test.tsx` | Testes AC12-AC15 |

---

## Referencias

- Audit: C05, M02, M03
- Screenshot: audit-06-historico.png
