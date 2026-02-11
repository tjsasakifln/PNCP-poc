# 🚨 Search & Export Bugfix Squad

**Status:** ACTIVE (P0)
**Version:** 1.0.0
**Created:** 2026-02-10
**Author:** Tiago Sasaki <tiago.sasaki@synkra.dev>

## 📋 Missão

Squad especializado em diagnóstico e correção de bugs críticos no sistema de busca e exportação do SmartLic.

## 🐛 Bugs Sob Investigação

### Bug #1: Busca Retornando Apenas 2 Resultados (P0)

**Descrição:**
- Usuário selecionou todos os estados (27), todas esferas, todas modalidades (Lei 14.133)
- Período: 01/jan/2026 - 10/fev/2026 (41 dias)
- Setor: Engenharia e Construção
- **Resultado:** Apenas 2 licitações retornadas (esperado: centenas/milhares)

**Status:** 🔍 Em diagnóstico
**Assignee:** search-specialist
**Root Cause Hypothesis:** `max_pages=50` em `pncp_client.py` limitando paginação

---

### Bug #2: Exportação Google Sheets - HTTP 404 (P0)

**Descrição:**
- Usuário tenta exportar resultados para Google Sheets
- **Erro:** "Falha ao exportar para Google Sheets - Erro HTTP 404"
- Impede uso de feature premium

**Status:** 🔍 Em diagnóstico
**Assignee:** export-specialist
**Root Cause Hypothesis:** Rota não acessível ou CORS bloqueando

---

## 👥 Equipe

| Agent | Role | Status |
|-------|------|--------|
| **Lead Investigator** | Coordenação e análise de logs | 🟢 Ready |
| **Search Specialist** | Expert em busca PNCP | 🔵 Active |
| **Export Specialist** | Expert em FastAPI/Google Sheets | 🔵 Active |
| **QA Validator** | Validação e testes | 🟡 Standby |

## 📝 Tasks

### Fase 1: Diagnóstico (30 min)

- [ ] `diagnose-search-bug.md` - Diagnosticar bug de busca (search-specialist) - **20 min**
- [ ] `diagnose-export-bug.md` - Diagnosticar bug de exportação (export-specialist) - **15 min**

### Fase 2: Correção (45 min)

- [ ] `fix-search-bug.md` - Implementar correção de busca - **30 min**
- [ ] `fix-export-bug.md` - Implementar correção de exportação - **20 min**

### Fase 3: Validação (30 min)

- [ ] `test-search-fix.md` - Validar correção de busca - **20 min**
- [ ] `test-export-fix.md` - Validar correção de exportação - **15 min**

**Total Estimado:** 1h45min

---

## 🚀 Quick Start

### Para Administrador (Você)

```bash
# Ativar squad
cd squads/search-export-bugfix-squad

# Executar workflow completo
aios-master --run workflows/emergency-bugfix-workflow.md

# OU executar tasks individuais
search-specialist --task tasks/diagnose-search-bug.md
export-specialist --task tasks/diagnose-export-bug.md
```

### Para Desenvolvedores Individualmente

```bash
# Diagnóstico de busca
cd backend
tail -f logs/app.log | grep "DIAGNÓSTICO"

# Diagnóstico de exportação
curl -i http://localhost:8000/api/export/google-sheets
open http://localhost:8000/docs
```

---

## 📁 Estrutura do Squad

```
search-export-bugfix-squad/
├── squad.yaml                  # Manifest principal
├── README.md                   # Este arquivo
├── agents/
│   ├── lead-investigator.md
│   ├── search-specialist.md    # ✅ Criado
│   ├── export-specialist.md    # ✅ Criado
│   └── qa-validator.md
├── tasks/
│   ├── diagnose-search-bug.md  # ✅ Criado
│   ├── diagnose-export-bug.md  # ✅ Criado
│   ├── fix-search-bug.md
│   ├── fix-export-bug.md
│   ├── test-search-fix.md
│   └── test-export-fix.md
├── workflows/
│   └── emergency-bugfix-workflow.md
├── templates/
│   ├── bug-diagnosis-report.md
│   └── hotfix-pr-template.md
├── checklists/
│   └── pre-deploy-checklist.md
├── tools/
│   ├── logs-analyzer.py
│   └── pncp-api-tester.py
├── data/
│   └── wide-search-params.json
└── config/
    ├── coding-standards.md
    ├── tech-stack.md
    └── source-tree.md
```

---

## 🔍 Root Cause Analysis (Atualizado em Tempo Real)

### Bug #1: Busca - 2 Resultados

**Causa Raiz Identificada:**
```python
# backend/pncp_client.py:461
def _fetch_by_uf(..., max_pages: int = 50):
    # ⚠️ Limita a 1000 registros por UF+modalidade (50 pages × 20 items)
    # Com 27 UFs e 8 modalidades = 216 combinações possíveis
    # Se algumas combinações atingem o limite, resultados são perdidos
```

**Correção Proposta:**
```python
max_pages: int = 500,  # 10.000 registros por UF+modalidade

# Adicionar warning
if pagina >= max_pages and tem_proxima_pagina:
    logger.warning(
        f"⚠️ MAX_PAGES ({max_pages}) atingido para UF={uf}, "
        f"modalidade={modalidade}. Resultados podem estar incompletos!"
    )
```

**Status:** 🔍 Aguardando confirmação via diagnóstico

---

### Bug #2: Exportação - HTTP 404

**Hipóteses em Investigação:**
1. Backend não iniciado completamente antes de frontend fazer request
2. Prefixo de rota duplicado (`/api/api/export`)
3. CORS bloqueando OPTIONS preflight
4. Proxy/nginx configurado incorretamente

**Status:** 🔍 Aguardando diagnóstico

---

## 📊 Métricas de Sucesso

### Search Fix
- ✅ Success Rate > 99%
- ✅ Coverage: 100% de UFs+modalidades processadas
- ✅ Performance: < 4 min para 27 UFs

### Export Fix
- ✅ Success Rate > 99%
- ✅ Latency < 10s para 1000 linhas
- ✅ HTTP 200 com `spreadsheet_url` válida

---

## 🛠️ Ferramentas Disponíveis

### Logs Analyzer
```bash
python tools/logs-analyzer.py --search-id <id>
```

### PNCP API Tester
```bash
python tools/pncp-api-tester.py --uf SP --modalidade 1 --pages 100
```

### Export Endpoint Tester
```bash
bash tools/test-export-endpoint.sh
```

---

## 📞 Contato

**Squad Lead:** Tiago Sasaki
**Email:** tiago.sasaki@synkra.dev
**Urgência:** P0 (Critical)

---

## 📝 Changelog

### 2026-02-10 21:30 UTC
- ✅ Squad criado
- ✅ Blueprint de design criada (`.designs/search-bugfix-squad-design.yaml`)
- ✅ Agentes principais criados (search-specialist, export-specialist)
- ✅ Tasks de diagnóstico criadas
- 🔄 Aguardando execução de diagnóstico

---

## 🚀 Próximos Passos

1. **AGORA:** Executar diagnóstico de ambos bugs (30 min)
2. **Depois:** Implementar correções (45 min)
3. **Final:** Validar e criar PRs de hotfix (30 min)
4. **Deploy:** Produção após validação em staging

**Timeline:** 1h45min até correção completa ✅
