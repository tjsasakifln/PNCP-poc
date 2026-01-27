# *brown-disc - Brownfield Discovery Command

**Status:** ✅ Pronto para usar
**Tipo:** Workflow Orchestrator Task
**Arquivo principal:** `.aios-core/development/tasks/brown-disc.md`

---

## 🚀 Como Usar

### Opção 1: Via Agente (Recomendado)

```bash
# Qualquer agente pode iniciar
@architect *brown-disc
@dev *brown-disc
@pm *brown-disc
```

### Opção 2: Via Script CLI

```bash
cd D:\pncp-poc
node .aios-core/development/scripts/brown-disc-orchestrator.js
```

### Opção 3: Via Workflow YAML

```bash
@aios-master *workflow brownfield-discovery
```

---

## 📋 O Que o Comando Faz

Orquestra **10 fases** de descoberta técnica:

| Fase | Agente | Tipo | Saída |
|------|--------|------|-------|
| 1 | @architect | Auto | System Architecture |
| 2 | @data-engineer | Auto (opcional) | Database Audit |
| 3 | @ux-design-expert | Auto | Frontend Spec |
| 4 | @architect | Manual | Technical Debt DRAFT |
| 5 | @data-engineer | Manual | DB Review |
| 6 | @ux-design-expert | Manual | UX Review |
| 7 | @qa | Manual | QA Gate Review |
| 8 | @architect | Manual | Final Assessment |
| 9 | @analyst | Manual | Executive Report ⭐ |
| 10 | @pm | Manual | Epic + Stories |

---

## 📊 Saídas Geradas

```
docs/
├── architecture/
│   └── system-architecture.md          [FASE 1]
├── frontend/
│   └── frontend-spec.md                [FASE 3]
├── reviews/
│   ├── db-specialist-review.md         [FASE 5]
│   ├── ux-specialist-review.md         [FASE 6]
│   └── qa-review.md                    [FASE 7]
├── prd/
│   ├── technical-debt-DRAFT.md         [FASE 4]
│   └── technical-debt-assessment.md    [FASE 8]
├── reports/
│   └── TECHNICAL-DEBT-REPORT.md        [FASE 9] ⭐⭐⭐
└── stories/
    ├── epic-technical-debt.md          [FASE 10]
    ├── story-1.1-*.md
    └── story-1.2-*.md

supabase/
└── docs/
    ├── SCHEMA.md                       [FASE 2]
    └── DB-AUDIT.md                     [FASE 2]
```

**Documento Principal para Stakeholders:**
- `docs/reports/TECHNICAL-DEBT-REPORT.md` ⭐

---

## ⏱️ Tempo Estimado

- **Mínimo:** 4 horas
- **Típico:** 5-6 horas
- **Projeto Complexo:** 8 horas

---

## 🎯 Fluxo de Execução

```
START
  ↓
[Criar diretórios]
  ↓
FASE 1-3 (podem ser paralelas):
  → @architect: System Documentation
  → @data-engineer: Database Audit
  → @ux-expert: Frontend Spec
  ↓
FASE 4:
  → @architect: Consolidar em DRAFT
  ↓
FASE 5-7 (sequenciais):
  → @data-engineer: Revisar DB
  → @ux-expert: Revisar UX
  → @qa: QA Gate ← ⚠️ QUALITY GATE
  ↓
[Se QA rejeitou → volta à FASE 4]
  ↓
FASE 8:
  → @architect: Finalizar Assessment
  ↓
FASE 9:
  → @analyst: Relatório Executivo
  ↓
FASE 10:
  → @pm: Epic + Stories
  ↓
END ✅
```

---

## 💡 Exemplos de Uso

### Para Seu Projeto BidIQ Uniformes

```bash
# 1. Iniciar discovery
@architect *brown-disc

# Isso vai gerar:
# - docs/architecture/system-architecture.md
#   → Documenta FastAPI + Next.js + PNCP integration
#
# - docs/frontend/frontend-spec.md
#   → Analisa Next.js 14 + Tailwind CSS
#
# - docs/reports/TECHNICAL-DEBT-REPORT.md
#   → Relatório com custos, ROI, timeline
#
# - docs/stories/epic-technical-debt.md + stories
#   → Pronto para dev implementar
```

### Para um Projeto Legado

```bash
# Quer auditar projeto antigo?
@architect *brown-disc

# Resultado: Assessment completo com:
# - Débitos identificados e priorizados
# - Estimativas de esforço validadas
# - Timeline de resolução
# - ROI demonstrado
```

---

## 📖 Referência das Fases

### FASES 1-3: COLETA (Automáticas, podem ser paralelas)

**FASE 1 - Sistema**
```
Agente: @architect
Task: document-project.md
Output: docs/architecture/system-architecture.md
Tempo: 30-60 min

Documenta:
✓ Arquitetura geral
✓ Componentes e camadas
✓ Fluxos de dados
✓ Tecnologias
✓ Padrões de código
✓ Débitos técnicos iniciais
```

**FASE 2 - Database**
```
Agente: @data-engineer
Task: db-schema-audit.md
Output: supabase/docs/SCHEMA.md + DB-AUDIT.md
Tempo: 20-40 min
Condicional: project_has_database

Analisa:
✓ Schema e relacionamentos
✓ Índices e performance
✓ RLS policies (Supabase)
✓ Integridade referencial
✓ Débitos de segurança/perf
```

**FASE 3 - Frontend**
```
Agente: @ux-design-expert
Task: audit-codebase.md
Output: docs/frontend/frontend-spec.md
Tempo: 30-45 min

Revisa:
✓ Estrutura de componentes
✓ Estado management
✓ Styling (Tailwind/etc)
✓ Acessibilidade (WCAG)
✓ Performance (bundle size)
✓ Débitos de UX
```

### FASES 4-8: CONSOLIDAÇÃO (Manuais, sequenciais)

**FASE 4 - DRAFT**
```
Agente: @architect
Tipo: Manual consolidation
Output: docs/prd/technical-debt-DRAFT.md
Tempo: 30-45 min

Consolida:
✓ Todos os débitos em tabela
✓ Estimativas preliminares
✓ Perguntas para especialistas
✓ Matriz de priorização inicial
```

**FASES 5-6 - REVISÕES DOS ESPECIALISTAS**
```
FASE 5 - @data-engineer revisa Database
FASE 6 - @ux-expert revisa UX/Frontend

Cada um:
✓ Valida débitos
✓ Adiciona débitos não identificados
✓ Estima horas de resolução
✓ Prioriza (visão do especialista)
✓ Responde perguntas do architect
```

**FASE 7 - QA GATE** ⚠️ CRÍTICA
```
Agente: @qa
Output: docs/reviews/qa-review.md
Tempo: 30-45 min
GATEKEEPER: true

QA faz:
✓ Identifica gaps
✓ Avalia riscos cruzados
✓ Valida dependências
✓ Sugere testes
✓ Aprova ou REJEITA

Se REJEITA → Volta à FASE 4
Se APROVA → Segue para FASE 8
```

**FASE 8 - ASSESSMENT FINAL**
```
Agente: @architect
Output: docs/prd/technical-debt-assessment.md
Tempo: 30-45 min

Incorpora:
✓ Inputs de @data-engineer
✓ Inputs de @ux-expert
✓ Feedback do @qa
✓ Recalcula prioridades
✓ Define ordem final de resolução
```

### FASES 9-10: ENTREGA (Manuais, finais)

**FASE 9 - RELATÓRIO EXECUTIVO** ⭐⭐⭐
```
Agente: @analyst
Output: docs/reports/TECHNICAL-DEBT-REPORT.md
Tempo: 30-45 min

Para stakeholders:
✓ Executive Summary (1 página)
✓ Números chave (custo, esforço)
✓ Análise de custos (resolver vs NÃO resolver)
✓ Impacto no negócio
✓ Timeline realista
✓ ROI demonstrado
✓ Recomendações

ESTE É O DOCUMENTO PARA APRESENTAR!
```

**FASE 10 - PLANNING**
```
Agente: @pm
Output: docs/stories/epic-*.md + story-*.md
Tempo: 30-60 min

Cria:
✓ Epic de resolução
✓ Stories individuais
✓ Critérios de aceite
✓ Testes requeridos
✓ Definition of Done

PRONTO PARA: @dev implementar
```

---

## ⚠️ Pontos de Atenção

### Quality Gate (FASE 7)
Se @qa não aprova:
1. Voltar à FASE 4
2. @architect revisa DRAFT
3. Ajusta baseado em feedback
4. Re-envia para validação (FASES 5-6)
5. @qa revisa novamente

### Condicionalidades
- **FASE 2 (Database):** Só roda se projeto tem database
- **FASE 5 (DB Review):** Só roda se FASE 2 completou
- **FASE 8 (Assessment):** Só roda se FASE 7 foi APPROVED

### Ordem Importância
1. **FASE 9 (Relatório):** Deliverable principal
2. **FASE 8 (Assessment):** Base técnica
3. **FASE 7 (QA Gate):** Validação qualidade
4. **FASES 1-3:** Coleta de dados

---

## 🔧 Personalização

Para seu projeto BidIQ:

```bash
# O workflow vai detectar:
# ✓ FastAPI + Next.js (tech stack)
# ✓ Supabase (database) - ou não, se não tiver
# ✓ Tailwind CSS (styling)
# ✓ Python + TypeScript (linguagens)

# E gerar assessment específico para:
# → API resilience (PNCP integration)
# → Frontend performance (Next.js optimization)
# → Database design (se houver)
# → Segurança (API keys, data validation)
```

---

## 📞 Suporte

**Dúvidas em qual fase?**
- Leia a seção correspondente em `brown-disc.md`
- Procure prompt customizado para seu agente

**Workflow travado?**
- FASE 1-3: Agente pode não entender projeto
- FASE 4: Consolide manualmente
- FASE 7: QA pode rejeitar (volte à FASE 4)
- FASE 9: Revise números e ROI

**Quer pular uma fase?**
- Não recomendado, pois cada uma valida anteriors
- Se necessário, @architect pode consolidar

---

## 📚 Arquivos Relacionados

- **Task:** `.aios-core/development/tasks/brown-disc.md`
- **Script:** `.aios-core/development/scripts/brown-disc-orchestrator.js`
- **Workflow YAML:** `.aios-core/development/workflows/brownfield-discovery.yaml`
- **Checklists:** `.aios-core/development/product/checklists/`
- **Templates:** `.aios-core/development/product/templates/`

---

## 🎯 Próximos Passos

1. **Iniciar:** `@architect *brown-disc`
2. **Monitorar:** Acompanhe cada fase
3. **Revisar:** Quality gate na FASE 7
4. **Apresentar:** TECHNICAL-DEBT-REPORT.md para stakeholders
5. **Planejar:** Use stories geradas na FASE 10
6. **Implementar:** @dev executa stories

---

**Pronto para começar? Execute:**

```bash
@architect *brown-disc
```

**Boa sorte! 🚀**
