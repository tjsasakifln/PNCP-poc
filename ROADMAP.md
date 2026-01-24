# 🗺️ ROADMAP — BidIQ Uniformes POC

**Versão:** 1.0
**Última Atualização:** 2026-01-24
**Status:** 🚧 Em Desenvolvimento

---

## 📋 Visão Geral

O **BidIQ Uniformes POC** é uma aplicação web que automatiza a busca, filtragem e análise de licitações de uniformes/fardamentos no Portal Nacional de Contratações Públicas (PNCP).

**Objetivo:** Demonstrar viabilidade técnica da solução com funcionalidades core implementadas.

**Prazo Estimado:** 2-3 semanas

---

## 🎯 Objetivos do POC

### ✅ Funcionalidades Core
- [x] Consumo resiliente da API PNCP (retry, rate limiting)
- [x] Filtragem inteligente de licitações de uniformes
- [x] Geração de planilha Excel formatada
- [x] Resumo executivo via GPT-4.1-nano
- [x] Interface web interativa (Next.js)

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
**Status:** 🟢 Iniciado (1/10 issues concluídas)

**Progresso Geral:**
```
[██░░░░░░░░░░░░░░░░░░] 3% (1/31 issues)

📦 EPIC 1: Setup             [███░░░░░] 1/3
🔌 EPIC 2: Cliente PNCP      [░░░░░░░░] 0/3
🎯 EPIC 3: Filtragem         [░░░░░░░░] 0/3
📊 EPIC 4: Saídas            [░░░░░░░░] 0/3
🌐 EPIC 5: API Backend       [░░░░░░░░] 0/4
🎨 EPIC 6: Frontend          [░░░░░░░░] 0/4
🚀 EPIC 7: Deploy            [░░░░░░░░] 0/4
```

---

## 🏔️ Milestones

### M1: Fundação e Backend Core *(Semana 1)*
**Objetivo:** Backend funcional consumindo PNCP e gerando saídas

**Prioridade P0 (Crítico):**
- [x] #2 - EPIC 1: Setup e Infraestrutura Base
  - [x] #3 - Estrutura de pastas
  - [x] #4 - Variáveis de ambiente
  - [x] #5 - Docker Compose
- [x] #6 - EPIC 2: Cliente PNCP e Resiliência
  - [x] #7 - Cliente HTTP resiliente
  - [x] #8 - Paginação automática
  - [x] #28 - Rate limiting
- [x] #9 - EPIC 3: Motor de Filtragem
  - [x] #10 - Normalização e keywords
  - [x] #11 - Filtros sequenciais
  - [x] #30 - Estatísticas
- [x] #12 - EPIC 4: Geração de Saídas
  - [x] #13 - Excel formatado
  - [x] #14 - GPT-4.1-nano
  - [x] #15 - Fallback sem LLM

**Deliverables:**
- ✅ Backend executando via Docker
- ✅ Integração PNCP funcional
- ✅ Excel sendo gerado
- ✅ Resumo LLM funcionando

---

### M2: Full-Stack Funcional *(Semana 2)*
**Objetivo:** Interface web + API completa

**Prioridade P0 (Crítico):**
- [x] #16 - EPIC 5: API Backend (FastAPI)
  - [x] #17 - Estrutura base
  - [x] #18 - POST /buscar
  - [x] #19 - Logging
  - [x] #29 - Health check
- [x] #20 - EPIC 6: Frontend (Next.js)
  - [x] #21 - Setup Next.js
  - [x] #22 - Seleção UFs
  - [x] #23 - Resultados
  - [x] #24 - API Routes

**Deliverables:**
- ✅ API REST completa
- ✅ Interface web responsiva
- ✅ Fluxo end-to-end funcional
- ✅ Docker Compose full-stack

---

### M3: POC em Produção *(Semana 2-3)*
**Objetivo:** POC deployado e documentado

**Prioridade P0 (Crítico):**
- [x] #25 - EPIC 7: Integração e Deploy
  - [x] #26 - Integração frontend ↔ backend
  - [x] #27 - Testes end-to-end
  - [x] #1 - Documentação (README.md)
  - [x] #31 - Deploy inicial

**Deliverables:**
- ✅ POC em produção (Vercel + Railway)
- ✅ README completo
- ✅ Testes E2E passando
- ✅ Monitoramento básico

---

## 🚧 Blockers & Riscos

### 🔴 Crítico
*(Nenhum bloqueador crítico no momento)*

### 🟡 Atenção
- **API PNCP:** Estabilidade desconhecida, pode ter rate limits agressivos
  - **Mitigação:** Cliente resiliente com retry e circuit breaker
- **OpenAI API:** Custo e disponibilidade do GPT-4.1-nano
  - **Mitigação:** Fallback sem LLM implementado

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
| **Issues Concluídas** | 31/31 | 🔴 0/31 (0%) |
| **Cobertura de Testes** | >70% | 🔴 N/A |
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

### Esta Semana (Prioridade P0)
1. **#3 - Estrutura de pastas** ← COMEÇAR AQUI
2. **#4 - Variáveis de ambiente**
3. **#5 - Docker Compose**
4. **#7 - Cliente HTTP resiliente**

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

---

## 🤝 Contribuição

Este é um POC interno. Para contribuir:
1. Leia o [PRD.md](PRD.md) completo
2. Use `/pick-next-issue` para selecionar uma tarefa
3. Siga o workflow de desenvolvimento acima
4. Abra PR com descrição detalhada

---

**Última sincronização com issues:** 2026-01-24 17:45
**Próxima revisão agendada:** 2026-01-27 (após Milestone 1)

*Este roadmap é sincronizado automaticamente via `/audit-roadmap`*
