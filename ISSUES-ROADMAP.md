# 🗺️ Roadmap de Issues - PNCP POC

**Total de Issues:** 31 (7 Épicos + 24 Issues de Implementação)

**Repositório:** https://github.com/tjsasakifln/PNCP-poc/issues

---

## 🏗️ EPIC 1: Setup e Infraestrutura Base (#2)

**Objetivo:** Estabelecer estrutura base do projeto

| # | Issue | Labels |
|---|-------|--------|
| #3 | Inicializar repositório e estrutura de pastas | infrastructure, setup |
| #4 | Configurar ambientes e variáveis | infrastructure, configuration |
| #5 | Setup Docker Compose | infrastructure, docker |

**Referência PRD:** Seções 10, 11

---

## 🔌 EPIC 2: Cliente PNCP e Resiliência (#6)

**Objetivo:** Cliente HTTP resiliente para API do PNCP

| # | Issue | Labels |
|---|-------|--------|
| #7 | Implementar cliente HTTP resiliente | backend, feature |
| #8 | Implementar paginação automática PNCP | backend, feature |
| #28 | Tratamento de rate limiting (429) | backend, feature |

**Referência PRD:** Seções 2, 3

---

## 🎯 EPIC 3: Motor de Filtragem (#9)

**Objetivo:** Sistema de filtragem sequencial fail-fast

| # | Issue | Labels |
|---|-------|--------|
| #10 | Normalização e matching de keywords | backend, feature |
| #11 | Filtros sequenciais fail-fast | backend, feature |
| #30 | Estatísticas de filtragem | backend, feature |

**Referência PRD:** Seção 4

---

## 📊 EPIC 4: Geração de Saídas (#12)

**Objetivo:** Excel formatado + resumo via LLM

| # | Issue | Labels |
|---|-------|--------|
| #13 | Gerador de Excel formatado | backend, feature |
| #14 | Integração GPT-4.1-nano | backend, feature, ai |
| #15 | Fallback sem LLM | backend, feature |

**Referência PRD:** Seções 5, 6

---

## 🌐 EPIC 5: API Backend (FastAPI) (#16)

**Objetivo:** API REST para orquestração

| # | Issue | Labels |
|---|-------|--------|
| #17 | Estrutura base FastAPI | backend, setup |
| #18 | Endpoint POST /buscar | backend, feature, integration |
| #19 | Logging estruturado | backend, feature |
| #29 | Health check endpoint | backend, feature |

**Referência PRD:** Seções 8, 12

---

## 🎨 EPIC 6: Frontend (Next.js) (#20)

**Objetivo:** Interface web interativa

| # | Issue | Labels |
|---|-------|--------|
| #21 | Setup Next.js 14 + Tailwind | frontend, setup |
| #22 | Interface seleção UFs e período | frontend, feature |
| #23 | Tela de resultados com resumo | frontend, feature |
| #24 | API Routes Next.js | frontend, feature |

**Referência PRD:** Seção 7

---

## 🚀 EPIC 7: Integração e Deploy (#25)

**Objetivo:** Integração completa e produção

| # | Issue | Labels |
|---|-------|--------|
| #26 | Integrar frontend e backend | integration, feature |
| #27 | Testes end-to-end | testing, feature |
| #1 | Documentação de uso (README.md) | documentation |
| #31 | Deploy inicial (produção) | deployment, infrastructure |

**Referência PRD:** Todas as seções

---

## 📋 Ordem de Execução Recomendada

### Sprint 1: Fundação (Semana 1)
1. ✅ EPIC 1 completo (#2-#5)
2. ✅ EPIC 2: Cliente PNCP (#6-#8, #28)

### Sprint 2: Lógica Core (Semana 1-2)
3. ✅ EPIC 3: Filtragem (#9-#11, #30)
4. ✅ EPIC 4: Saídas (#12-#15)

### Sprint 3: APIs e UI (Semana 2)
5. ✅ EPIC 5: Backend API (#16-#19, #29)
6. ✅ EPIC 6: Frontend (#20-#24)

### Sprint 4: Finalização (Semana 2-3)
7. ✅ EPIC 7: Integração e Deploy (#25-#27, #1, #31)

---

## 🎯 Marcos (Milestones)

- **Milestone 1 (Semana 1):** Backend funcional (EPICs 1-4)
- **Milestone 2 (Semana 2):** Full-stack funcional (EPICs 5-6)
- **Milestone 3 (Semana 3):** POC em produção (EPIC 7)

---

## 📊 Estatísticas

- **Total de Issues:** 31
- **Épicos:** 7
- **Issues de Implementação:** 24
- **Backend:** 17 issues
- **Frontend:** 4 issues
- **Infraestrutura:** 5 issues
- **Integração/Deploy:** 5 issues

---

## 🔗 Links Úteis

- **Issues:** https://github.com/tjsasakifln/PNCP-poc/issues
- **PRD:** [PRD.md](PRD.md)
- **Documentação PNCP:** https://pncp.gov.br/api/consulta/swagger-ui/index.html

---

*Gerado automaticamente pelo AIOS Master em 2026-01-24*
