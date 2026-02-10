# 📑 STORY-183: Índice de Documentação - Hotfix Crítico

**Status:** 🚨 P0 - CRÍTICO
**Criada:** 2026-02-10 21:45 UTC
**Squad:** search-export-bugfix-squad

---

## 📖 Documentos Principais (Leia Nesta Ordem)

### 1. 🚨 **Executive Summary** (COMECE AQUI)
**Arquivo:** `docs/stories/STORY-183-EXECUTIVE-SUMMARY.md`

**O que é:** Resumo de 1 página com ações imediatas

**Quando ler:** Agora, antes de qualquer coisa

**Tempo de leitura:** 2 minutos

---

### 2. 📋 **Story Completa** (Implementação Detalhada)
**Arquivo:** `docs/stories/STORY-183-hotfix-search-export-critical-bugs.md`

**O que é:** Documentação completa com:
- Root Cause Analysis detalhada
- Plano técnico de implementação passo-a-passo
- Acceptance Criteria completos
- Código das correções
- Plano de testes
- Procedimento de deploy
- Rollback plan

**Quando ler:** Antes de implementar as correções

**Tempo de leitura:** 15 minutos

---

### 3. 🛠️ **Hotfix Execution Report** (Guia Prático)
**Arquivo:** `HOTFIX-EXECUTION-REPORT-2026-02-10.md`

**O que é:** Guia prático de execução com comandos prontos

**Quando ler:** Durante a execução das correções

**Tempo de leitura:** 10 minutos

---

### 4. 🏗️ **Squad README** (Visão Geral do Squad)
**Arquivo:** `squads/search-export-bugfix-squad/README.md`

**O que é:** Documentação do squad especializado criado para resolver esses bugs

**Quando ler:** Para entender a estrutura do squad

**Tempo de leitura:** 5 minutos

---

## 🚀 Quick Start (Começar Agora)

### Passo 1: Executar Diagnóstico (5 min)

```bash
cd "T:\GERAL\SASAKI\Licitações"
bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh
```

**O que faz:**
- Verifica backend está rodando
- Testa rota de exportação (404?)
- Confirma valor de `max_pages` em `pncp_client.py`
- Analisa logs recentes
- Gera relatório de diagnóstico

---

### Passo 2: Aplicar Correções (45 min)

#### Correção 2.1: Bug de Busca
```python
# Editar: backend/pncp_client.py linha 461

# DE:
max_pages: int = 50,

# PARA:
max_pages: int = 500,
```

#### Correção 2.2: Bug de Exportação
Baseado no resultado do diagnóstico (Passo 1)

**Veja:** `docs/stories/STORY-183-hotfix-search-export-critical-bugs.md` seção "Fase 2"

---

### Passo 3: Testar (30 min)

```bash
# Iniciar backend
cd backend
uvicorn main:app --reload

# Testar busca ampla (em outro terminal)
curl -X POST http://localhost:8000/api/buscar \
  -H "Authorization: Bearer <token>" \
  -d '{"ufs":["SP","RJ","MG"],"data_inicial":"2026-01-01","data_final":"2026-02-10"}'

# Esperado: > 100 resultados
```

---

### Passo 4: Deploy (15 min)

```bash
git checkout -b hotfix/STORY-183-search-export-bugs
git add backend/pncp_client.py backend/main.py
git commit -m "fix(P0): resolve search pagination and export bugs [STORY-183]"
git push origin hotfix/STORY-183-search-export-bugs
# Criar PR e merge
```

---

## 📁 Estrutura de Arquivos

```
T:\GERAL\SASAKI\Licitações\
│
├── STORY-183-INDEX.md                          # ← VOCÊ ESTÁ AQUI
├── HOTFIX-EXECUTION-REPORT-2026-02-10.md      # Guia prático
│
├── docs/stories/
│   ├── STORY-183-hotfix-search-export-critical-bugs.md  # Story completa
│   └── STORY-183-EXECUTIVE-SUMMARY.md                   # Resumo executivo
│
├── squads/search-export-bugfix-squad/
│   ├── README.md                               # Visão geral do squad
│   ├── squad.yaml                              # Manifest
│   │
│   ├── agents/
│   │   ├── search-specialist.md                # Expert em busca PNCP
│   │   └── export-specialist.md                # Expert em FastAPI/Sheets
│   │
│   ├── tasks/
│   │   ├── diagnose-search-bug.md              # Diagnóstico de busca (20 min)
│   │   ├── diagnose-export-bug.md              # Diagnóstico de export (15 min)
│   │   ├── fix-search-bug.md                   # Implementação busca
│   │   ├── fix-export-bug.md                   # Implementação export
│   │   ├── test-search-fix.md                  # Validação busca
│   │   └── test-export-fix.md                  # Validação export
│   │
│   └── tools/
│       └── quick-diagnostic.sh                 # Script automático (5 min)
│
└── squads/.designs/
    └── search-bugfix-squad-design.yaml         # Blueprint arquitetural
```

---

## 🎯 Navegação Rápida por Objetivo

### "Preciso Entender o Problema Rápido"
→ **Leia:** `STORY-183-EXECUTIVE-SUMMARY.md` (2 min)

### "Vou Implementar as Correções"
→ **Leia:** `STORY-183-hotfix-search-export-critical-bugs.md` (15 min)
→ **Siga:** Seção "Technical Implementation Plan"

### "Quero Executar o Diagnóstico"
→ **Execute:** `bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh`
→ **Leia:** `squads/search-export-bugfix-squad/tasks/diagnose-*.md`

### "Preciso de Comandos Prontos"
→ **Leia:** `HOTFIX-EXECUTION-REPORT-2026-02-10.md`

### "Quero Entender a Arquitetura do Squad"
→ **Leia:** `squads/search-export-bugfix-squad/README.md`
→ **Veja:** `squads/.designs/search-bugfix-squad-design.yaml`

---

## 📊 Status das Tarefas

| Task | Status | Arquivo de Referência |
|------|--------|----------------------|
| Diagnóstico de Busca | ⏳ Pendente | `tasks/diagnose-search-bug.md` |
| Diagnóstico de Export | ⏳ Pendente | `tasks/diagnose-export-bug.md` |
| Correção de Busca | ⏳ Pendente | `tasks/fix-search-bug.md` |
| Correção de Export | ⏳ Pendente | `tasks/fix-export-bug.md` |
| Testes de Busca | ⏳ Pendente | `tasks/test-search-fix.md` |
| Testes de Export | ⏳ Pendente | `tasks/test-export-fix.md` |

---

## 🔗 Links Úteis

### Documentação Relacionada
- [STORY-180: Google Sheets Export](docs/stories/STORY-180-google-sheets-export.md)
- [Epic: Estabilidade](docs/stories/epic-technical-debt.md)

### APIs Externas
- [PNCP API Docs](https://pncp.gov.br/api/docs)
- [Google Sheets API](https://developers.google.com/sheets/api)

---

## 📞 Contatos

**PM:** @pm (Morgan - Product Manager)
**Admin:** Tiago Sasaki
**Squad:** search-export-bugfix-squad

---

## ⏱️ Timeline Estimada

```
Diagnóstico      ████░░░░░░░░░░░░░░  15 min
Implementação    ░░░░█████████░░░░░  45 min
Testes           ░░░░░░░░░████░░░░░  30 min
Deploy           ░░░░░░░░░░░░░███░░  15 min
Validação        ░░░░░░░░░░░░░░░░█░  10 min
────────────────────────────────────────
TOTAL                              1h55min
```

---

## 🚀 Ação Imediata

**Execute agora:**
```bash
bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh
```

**Resultado esperado:**
- ✅ Confirmação de `max_pages=50` (bug de busca)
- ✅ Confirmação de 404 em `/api/export/google-sheets` (bug de export)
- ✅ Relatório detalhado com recomendações

---

**Última atualização:** 2026-02-10 21:50 UTC
**Mantido por:** @pm (Morgan)
