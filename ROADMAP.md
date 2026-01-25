# 🗺️ ROADMAP — BidIQ Uniformes POC

**Versão:** 1.6 (100% PRD Coverage)
**Última Atualização:** 2026-01-25 01:53
**Status:** 🚧 Em Desenvolvimento (14.7% completo - 5/34 issues)

---

## 📋 Visão Geral

O **BidIQ Uniformes POC** é uma aplicação web que automatiza a busca, filtragem e análise de licitações de uniformes/fardamentos no Portal Nacional de Contratações Públicas (PNCP).

**Objetivo:** Demonstrar viabilidade técnica da solução com funcionalidades core implementadas.

**Prazo Estimado:** 3-4 semanas (ajustado após audit 2026-01-24)

---

## 🎯 Objetivos do POC

### ✅ Funcionalidades Core
- [ ] Consumo resiliente da API PNCP (retry, rate limiting)
- [ ] Filtragem inteligente de licitações de uniformes
- [ ] Geração de planilha Excel formatada
- [ ] Resumo executivo via GPT-4.1-nano
- [ ] Interface web interativa (Next.js)

### 🎁 Nice-to-Have (Opcional)
- [ ] Circuit breaker para resiliência avançada
- [ ] Dashboard de métricas/observabilidade
- [ ] Histórico de buscas
- [ ] Export em múltiplos formatos (PDF, CSV)

---

## 📊 Status Atual

### Current Milestone: **M1 - Fundação e Backend**

**Meta:** Backend funcional com integração PNCP completa
**Prazo:** Semana 1 (24/01 - 31/01)
**Status:** 🟡 Em Progresso (5/31 issues concluídas - 16.1%)

**Progresso Geral:**
```
[████░░░░░░░░░░░░░░░] 14.7% (5/34 issues) - 100% PRD Coverage ✅

📦 EPIC 1: Setup             [███████░░░] 3/5 🟡 60% (issues #2, #32 abertas)
🔌 EPIC 2: Cliente PNCP      [███████░░░] 2/3 🟡 67% EM PROGRESSO (#8 ✅)
🎯 EPIC 3: Filtragem         [░░░░░░░░░░] 0/4 🔴 Não iniciado
📊 EPIC 4: Saídas            [░░░░░░░░░░] 0/3 🔴 Não iniciado
🌐 EPIC 5: API Backend       [░░░░░░░░░░] 0/5 🔴 Não iniciado
🎨 EPIC 6: Frontend          [░░░░░░░░░░] 0/6 🔴 Não iniciado (issues #33, #34 adicionadas)
🚀 EPIC 7: Deploy            [░░░░░░░░░░] 0/5 🔴 Não iniciado
```

---

## 🏔️ Milestones

### M1: Fundação e Backend Core *(Semana 1)*
**Objetivo:** Backend funcional consumindo PNCP e gerando saídas

**Prioridade P0 (Crítico):**
- [ ] #2 - EPIC 1: Setup e Infraestrutura Base 🟡 60% COMPLETO
  - [x] #3 - Estrutura de pastas ✅
  - [x] #4 - Variáveis de ambiente ✅
  - [x] #5 - Docker Compose ✅ (PR #37 merged)
  - [ ] #32 - Setup Test Frameworks (pytest + jest) ⭐ NOVO
- [ ] #6 - EPIC 2: Cliente PNCP e Resiliência 🟡 67% EM PROGRESSO
  - [x] #7 - Cliente HTTP resiliente ✅ (PR #38 merged 2026-01-24)
  - [x] #8 - Paginação automática ✅ (PR #39 merged 2026-01-25)
  - [ ] #28 - Rate limiting
- [ ] #9 - EPIC 3: Motor de Filtragem 🔴 NÃO INICIADO
  - [ ] #10 - Normalização e keywords
  - [ ] #11 - Filtros sequenciais
  - [ ] #30 - Estatísticas
- [ ] #12 - EPIC 4: Geração de Saídas 🔴 NÃO INICIADO
  - [ ] #13 - Excel formatado
  - [ ] #14 - GPT-4.1-nano
  - [ ] #15 - Fallback sem LLM

**Deliverables:**
- 🟡 Backend executando via Docker (estrutura criada, módulos core pendentes)
- 🟡 Integração PNCP funcional (cliente base implementado, paginação pendente)
- 🔴 Excel sendo gerado (módulo não implementado)
- 🔴 Resumo LLM funcionando (módulo não implementado)

---

### M2: Full-Stack Funcional *(Semana 2)*
**Objetivo:** Interface web + API completa
**Status:** 🔴 NÃO INICIADO (0/9 issues - 0%)

**Prioridade P0 (Crítico):**
- [ ] #16 - EPIC 5: API Backend (FastAPI)
  - [ ] #17 - Estrutura base
  - [ ] #18 - POST /buscar
  - [ ] #19 - Logging
  - [ ] #29 - Health check
- [ ] #20 - EPIC 6: Frontend (Next.js)
  - [ ] #21 - Setup Next.js
  - [ ] #22 - Seleção UFs (validações enriquecidas)
  - [ ] #33 - Error Boundaries ⭐ NOVO
  - [ ] #34 - Form Validations ⭐ NOVO
  - [ ] #23 - Resultados
  - [ ] #24 - API Routes

**Deliverables:**
- 🔴 API REST completa (não iniciado)
- 🔴 Interface web responsiva (não iniciado)
- 🔴 Fluxo end-to-end funcional (não iniciado)
- 🔴 Docker Compose full-stack (não iniciado)

---

### M3: POC em Produção *(Semana 3-4)*
**Objetivo:** POC deployado e documentado
**Status:** 🔴 NÃO INICIADO (0/5 issues - 0%)

**Prioridade P0 (Crítico):**
- [ ] #25 - EPIC 7: Integração e Deploy
  - [ ] #26 - Integração frontend ↔ backend
  - [ ] #27 - Testes end-to-end
  - [ ] #1 - Documentação (README.md)
  - [ ] #31 - Deploy inicial

**Deliverables:**
- 🔴 POC em produção (Vercel + Railway) - não iniciado
- 🔴 README completo - não iniciado
- 🔴 Testes E2E passando - não iniciado
- 🔴 Monitoramento básico - não iniciado

---

## 🚧 Blockers & Riscos

### 🔴 Crítico
- **VELOCIDADE DE DESENVOLVIMENTO:** 0.57 issues/dia (média 7 dias)
  - **Impacto:** Com 27 issues restantes, ETA realista é 2026-02-18 (não 2026-02-14)
  - **Mitigação:** Aumentar cadência para 1.5-2 issues/dia ou reduzir escopo do POC
  - **Decisão Necessária:** Priorizar EPICs 1-4 (backend core) e adiar EPICs 5-7 para v0.3?

### 🟡 Atenção
- **API PNCP:** Estabilidade desconhecida, pode ter rate limits agressivos
  - **Mitigação:** Cliente resiliente com retry e circuit breaker
- **OpenAI API:** Custo e disponibilidade do GPT-4.1-nano
  - **Mitigação:** Fallback sem LLM implementado
- **ESCOPO vs PRAZO:** Roadmap original estimava 2-3 semanas, mas velocidade sugere 3-4 semanas
  - **Mitigação:** Considerar MVP reduzido focado apenas em backend funcional

### 🟢 Monitorando
- **Performance:** Excel grande pode ser lento
  - **Mitigação:** Limitar busca a 30 dias (PRD)
- **Deploy:** Configuração de variáveis de ambiente em produção
  - **Mitigação:** Documentação detalhada no README

---

## 📈 Métricas de Sucesso

### KPIs do POC
| Métrica | Meta | Status |
|---------|------|--------|
| **Issues Concluídas** | 34/34 | 🔴 4/34 (11.8%) |
| **PRD Coverage** | 100% | ✅ 100% (era 93%) |
| **Cobertura de Testes** | >70% | 🔴 N/A (Issue #32 pendente) |
| **Tempo de Resposta API** | <10s | 🔴 N/A |
| **Uptime em Produção** | >95% | 🔴 N/A |
| **Documentação** | README completo | 🔴 Pendente |

### Critérios de Aceitação POC
- [ ] Interface web acessível e funcional
- [ ] Busca retorna resultados em <15s (cenário médio)
- [ ] Excel gerado com formatação correta
- [ ] Resumo LLM relevante e preciso
- [ ] Fallback funciona sem OpenAI
- [ ] Docker Compose permite execução local
- [ ] README permite que terceiros executem o POC

---

## 🗓️ Cronograma

```
┌─────────────────────────────────────────────────────────┐
│  Semana 1 (24/01 - 31/01)                               │
│  ▓▓▓▓▓▓▓░░░░░░░░░░░░░░ M1: Backend Core                │
│  └─ EPIC 1, 2, 3, 4                                     │
│                                                          │
│  Semana 2 (31/01 - 07/02)                               │
│  ░░░░░░▓▓▓▓▓▓▓▓░░░░░░ M2: Full-Stack                   │
│  └─ EPIC 5, 6                                           │
│                                                          │
│  Semana 3 (07/02 - 14/02)                               │
│  ░░░░░░░░░░░░▓▓▓▓▓▓▓ M3: Deploy                        │
│  └─ EPIC 7, Testes, Docs                                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Processo de Desenvolvimento

### Workflow Padrão
1. **Pick Issue:** Usar `/pick-next-issue` para selecionar issue
2. **Implementar:** Criar branch `feature/issue-{number}`
3. **Commit:** Seguir Conventional Commits
4. **PR:** Criar PR com descrição completa
5. **Review:** Usar `/review-pr` para análise automatizada
6. **Merge:** Após aprovação, merge para `main`

### Convenções
- **Branches:** `feature/issue-{n}`, `fix/issue-{n}`
- **Commits:** `feat(escopo): descrição` ou `fix(escopo): descrição`
- **PRs:** Título = título da issue, corpo com contexto

### Comandos Disponíveis
```bash
/pick-next-issue     # Seleciona próxima issue para implementar
/review-pr {number}  # Analisa PR e verifica conformidade
/audit-roadmap       # Verifica sincronização Roadmap ↔ Issues
```

---

## 📚 Referências

### Documentos do Projeto
- **PRD Técnico:** [PRD.md](PRD.md)
- **Issues:** [GitHub Issues](https://github.com/tjsasakifln/PNCP-poc/issues)
- **Roadmap de Issues:** [ISSUES-ROADMAP.md](ISSUES-ROADMAP.md)

### APIs e Documentação Externa
- **API PNCP:** https://pncp.gov.br/api/consulta/swagger-ui/index.html
- **OpenAI API:** https://platform.openai.com/docs
- **Next.js 14:** https://nextjs.org/docs
- **FastAPI:** https://fastapi.tiangolo.com

---

## 🎯 Próximas Ações (Immediate)

### Esta Semana (Prioridade P0 - M1 Backend Core)
1. **#32 - Setup Test Frameworks** ← NOVA - FUNDAMENTAL (2h)
2. **#8 - Paginação automática PNCP** ← PRÓXIMA TAREFA (enriquecida com PRD)
3. **#28 - Rate limiting (429)**
4. **#10 - Normalização e matching de keywords**
5. **#11 - Filtros sequenciais fail-fast**
6. **#30 - Estatísticas de filtragem**

### Próxima Semana (M1 → M2 Transition)
6. **#13 - Gerador de Excel formatado**
7. **#14 - Integração GPT-4.1-nano**
8. **#15 - Fallback sem LLM**
9. **#17 - Estrutura base FastAPI**

### Comandos Úteis
```bash
# Selecionar próxima issue automaticamente
/pick-next-issue

# Verificar sincronização do roadmap
/audit-roadmap

# Após criar PR
/review-pr {pr-number}
```

---

## 📝 Histórico de Atualizações

| Data | Versão | Mudanças |
|------|--------|----------|
| 2026-01-24 | 1.0 | Roadmap inicial criado com 31 issues mapeadas |
| 2026-01-24 | 1.1 | Issue #4 concluída (Environment Variables) - PR #36 merged |
| 2026-01-24 | 1.2 | Issue #5 concluída (Docker Compose) - PR #37 merged |
| 2026-01-24 | 1.3 | **AUDIT CRÍTICO:** Correção de 26 estados incorretos - Drift de 83.9% eliminado |
| 2026-01-24 | 1.4 | Progresso real: 4/31 (12.9%). M2 e M3 corrigidos para 0%. ETA ajustado para 3-4 semanas |
| 2026-01-24 | 1.5 | **100% PRD COVERAGE:** +3 issues (#32, #33, #34). Total: 34 issues. Progresso: 11.8% (4/34) |
| 2026-01-25 | 1.6 | Issue #8 concluída (Paginação PNCP) - PR #39 merged. EPIC 2: 67% completo (2/3). Progresso: 14.7% (5/34) |

---

## ⚠️ Nota de Sincronização

**ÚLTIMA AUDITORIA:** 2026-01-24 23:30
**DRIFT DETECTADO:** 83.9% (26 issues marcadas incorretamente como concluídas)
**AÇÃO TOMADA:** Sincronização completa realizada via `/audit-roadmap`

**Status Validado:**
- ✅ Issues fechadas: #3, #4, #5, #7, #8 (5 issues)
- ⚠️ Issues abertas: Todas as demais (29 issues)
- 📊 Progresso real: 14.7% (5/34)

---

## 🤝 Contribuição

Este é um POC interno. Para contribuir:
1. Leia o [PRD.md](PRD.md) completo
2. Use `/pick-next-issue` para selecionar uma tarefa
3. Siga o workflow de desenvolvimento acima
4. Abra PR com descrição detalhada

---

---

## 🎯 NOVAS ISSUES - 100% PRD Coverage

### ⭐ Issue #32: Setup Test Frameworks (pytest + jest)
**EPIC:** #2 | **Prioridade:** P1 | **Estimativa:** 2h

Configurar pytest (backend) e jest (frontend) conforme CLAUDE.md e PRD Seção 9.

**Por que é necessário:**
- Gap identificado na auditoria PRD
- CLAUDE.md especifica pytest/jest mas não há issue para configuração inicial
- Coverage threshold (70% backend, 60% frontend) precisa ser configurado

**Acceptance Criteria:**
- pytest.ini ou pyproject.toml com configurações
- Coverage threshold 70% para backend
- jest.config.js para frontend
- Scripts npm test e pytest funcionando

---

### ⭐ Issue #33: Frontend Error Boundaries
**EPIC:** #20 | **Prioridade:** P1 | **Estimativa:** 2h

Implementar `error.tsx` conforme PRD Seção 7.2 linha 1187.

**Por que é necessário:**
- PRD estrutura de arquivos inclui `error.tsx`
- Error boundaries são best practice React
- Melhora UX em casos de falha

**Acceptance Criteria:**
- Arquivo app/error.tsx criado
- Fallback UI amigável
- Botão "Tentar novamente"
- Erros logados apropriadamente

---

### ⭐ Issue #34: Frontend Form Validations
**EPIC:** #20 | **Prioridade:** P1 | **Estimativa:** 1h

Validações client-side para formulário (PRD 7.3 linhas 1259-1262).

**Por que é necessário:**
- PRD implementação mostra validação de UFs vazia (linha 1259)
- Prevenir requests inválidos ao backend
- Melhorar feedback ao usuário

**Acceptance Criteria:**
- Min 1 UF selecionada
- Validação data_final >= data_inicial
- Range máximo 30 dias (PRD Seção 1.2)
- Mensagens de erro inline

---

**Última sincronização com issues:** 2026-01-25 01:53 (Issue #8 merged via PR #39)
**Próxima revisão agendada:** 2026-01-27 (após progresso em M1)

*Este roadmap é sincronizado automaticamente. Versão 1.6: 34 issues, 100% PRD coverage*
