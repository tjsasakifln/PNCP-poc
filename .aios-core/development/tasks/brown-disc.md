# *brown-disc - Brownfield Discovery Workflow Orchestrator

**Comando:** `*brown-disc`
**Categoria:** Workflow Orchestration
**Tempo estimado:** 4-6 horas
**Agentes envolvidos:** architect, data-engineer, ux-design-expert, qa, analyst, pm

---

## Objetivo

Executar workflow completo de descoberta técnica (`brownfield-discovery.yaml`) para analisar projeto existente, identificar débitos técnicos e gerar assessment com relatório executivo e stories.

---

## 🚀 Como Iniciar

```bash
# Via agente (qualquer um)
@architect *brown-disc

# Via CLI
node .aios-core/development/scripts/brown-disc-orchestrator.js

# Via AIOS Master
@aios-master *brown-disc
```

---

## 📋 Checklist de Execução

Siga cada fase em ordem. Marque conforme completa:

### PRÉ-REQUISITOS
- [ ] Clonar/acessar projeto brownfield
- [ ] Verificar tech stack (Next.js? FastAPI? Database?)
- [ ] Criar diretórios de output

### FASE 1-3: COLETA (Paralelo possível)

#### FASE 1: Documentação de Sistema
**Agente:** @architect
**Task:** `document-project.md`
**Checklist:** `architect-checklist.md`
**Output:** `docs/architecture/system-architecture.md`
**Tempo:** 30-60 min

```
[ ] @architect execute: *document-project
[ ] Validar output existe
[ ] Validar tamanho > 5KB
[ ] Passar checklist architect
```

**Prompt customizado:**
```
Analize o projeto e crie documentação completa:
1. Arquitetura geral (componentes, camadas)
2. Fluxos de dados principais
3. Tecnologias e frameworks
4. Padrões de código usados
5. Débitos técnicos identificados

Template: brownfield-architecture-tmpl.yaml
Output: docs/architecture/system-architecture.md
```

---

#### FASE 2: Auditoria de Database
**Agente:** @data-engineer
**Task:** `db-schema-audit.md`
**Checklist:** `database-design-checklist.md`
**Output:** `supabase/docs/SCHEMA.md`, `supabase/docs/DB-AUDIT.md`
**Tempo:** 20-40 min
**Condicional:** Só se `project_has_database === true`

```
[ ] Verificar se projeto tem database
[ ] Se não tem → SKIP esta fase
[ ] Se tem → @data-engineer execute: *db-schema-audit
[ ] Incluir db-rls-audit.md também
[ ] Validar outputs existem
[ ] Passar checklist database
```

**Prompt customizado:**
```
Analize o schema e segurança do banco:
1. Estrutura de tabelas e relacionamentos
2. Índices e performance
3. Políticas RLS (se Supabase)
4. Integridade referencial
5. Débitos de segurança/performance

Outputs:
- supabase/docs/SCHEMA.md (estrutura)
- supabase/docs/DB-AUDIT.md (problemas)
```

---

#### FASE 3: Especificação Frontend/UX
**Agente:** @ux-design-expert
**Task:** `audit-codebase.md`
**Checklist:** `component-quality-checklist.md`
**Output:** `docs/frontend/frontend-spec.md`
**Tempo:** 30-45 min

```
[ ] @ux-design-expert execute: *audit-codebase
[ ] Foco em Next.js/React estrutura
[ ] Validar output > 3KB
[ ] Passar checklist component
```

**Prompt customizado:**
```
Analize frontend e componentes:
1. Estrutura de componentes (atomic design?)
2. Padrões de estado (Redux/Context/Hooks?)
3. Estilo e design system (Tailwind/CSS-in-JS?)
4. Acessibilidade (WCAG compliance?)
5. Performance (bundle size, rendering?)
6. Débitos de UX/design

Template: front-end-spec-tmpl.yaml
Output: docs/frontend/frontend-spec.md
```

---

### FASE 4: Consolidação Inicial (DRAFT)

**Agente:** @architect
**Tipo:** Manual consolidation
**Output:** `docs/prd/technical-debt-DRAFT.md`
**Tempo:** 30-45 min

```
[ ] Ler docs/architecture/system-architecture.md
[ ] Ler supabase/docs/SCHEMA.md (se existe)
[ ] Ler supabase/docs/DB-AUDIT.md (se existe)
[ ] Ler docs/frontend/frontend-spec.md
[ ] @architect consolida em DRAFT
```

**Prompt para @architect:**
```
Consolide todos os débitos em um DRAFT:

LEIA:
1. docs/architecture/system-architecture.md
2. supabase/docs/SCHEMA.md (se existe)
3. supabase/docs/DB-AUDIT.md (se existe)
4. docs/frontend/frontend-spec.md

CRIE: docs/prd/technical-debt-DRAFT.md

ESTRUTURA:
# Technical Debt Assessment - DRAFT

## 1. Débitos de Sistema
[extrair de system-architecture.md]

## 2. Débitos de Database
[extrair de DB-AUDIT.md]
⚠️ PENDENTE: Revisão @data-engineer

## 3. Débitos de Frontend/UX
[extrair de frontend-spec.md]
⚠️ PENDENTE: Revisão @ux-expert

## 4. Matriz Preliminar
| ID | Débito | Área | Impacto | Esforço | Prioridade |
|----|--------|------|---------|---------|------------|

## 5. Perguntas para Especialistas
- @data-engineer: [perguntas sobre DB]
- @ux-expert: [perguntas sobre Frontend]

Marque claramente seções pendentes de revisão.
Adicione estimativas iniciais de esforço (horas).
```

---

### FASE 5: Validação Database Specialist

**Agente:** @data-engineer
**Tipo:** Manual review
**Output:** `docs/reviews/db-specialist-review.md`
**Tempo:** 20-30 min
**Condicional:** Só se database existe

```
[ ] Ler docs/prd/technical-debt-DRAFT.md
[ ] @data-engineer revisa seção Database
[ ] Cria docs/reviews/db-specialist-review.md
```

**Prompt para @data-engineer:**
```
Revise a seção de Database do DRAFT:

LEIA: docs/prd/technical-debt-DRAFT.md

FAÇA:
1. VALIDAR débitos (confirma/ajusta/remove)
2. ADICIONAR débitos não identificados
3. ESTIMAR horas para resolver cada um
4. PRIORIZAR (risco de segurança, performance)
5. RESPONDER perguntas do architect

CRIE: docs/reviews/db-specialist-review.md

FORMATO:
## Database Specialist Review

### Débitos Validados
| ID | Débito | Severidade | Horas | Prioridade | Notas |

### Débitos Adicionados
[novos]

### Respostas ao Architect
[respostas]

### Recomendações
[ordem de resolução]
```

---

### FASE 6: Validação UX/Frontend Specialist

**Agente:** @ux-design-expert
**Tipo:** Manual review
**Output:** `docs/reviews/ux-specialist-review.md`
**Tempo:** 20-30 min

```
[ ] Ler docs/prd/technical-debt-DRAFT.md
[ ] @ux-expert revisa seção Frontend/UX
[ ] Cria docs/reviews/ux-specialist-review.md
```

**Prompt para @ux-design-expert:**
```
Revise a seção de Frontend/UX do DRAFT:

LEIA: docs/prd/technical-debt-DRAFT.md

FAÇA:
1. VALIDAR débitos (confirma/ajusta/remove)
2. ADICIONAR débitos não identificados
3. ESTIMAR horas para resolver cada um
4. PRIORIZAR (impacto na UX, acessibilidade)
5. RESPONDER perguntas do architect

CRIE: docs/reviews/ux-specialist-review.md

FORMATO:
## UX Specialist Review

### Débitos Validados
| ID | Débito | Severidade | Horas | Prioridade | Impacto UX |

### Débitos Adicionados
[novos]

### Respostas ao Architect
[respostas]

### Recomendações de Design
[soluções sugeridas]
```

---

### FASE 7: QA Review Geral

**Agente:** @qa
**Tipo:** Manual review
**Output:** `docs/reviews/qa-review.md`
**Tempo:** 30-45 min

```
[ ] Ler docs/prd/technical-debt-DRAFT.md
[ ] Ler docs/reviews/db-specialist-review.md (se existe)
[ ] Ler docs/reviews/ux-specialist-review.md
[ ] @qa faz review geral
[ ] Cria docs/reviews/qa-review.md
```

**Prompt para @qa:**
```
Faça review geral da qualidade do assessment:

LEIA:
1. docs/prd/technical-debt-DRAFT.md
2. docs/reviews/db-specialist-review.md (se existe)
3. docs/reviews/ux-specialist-review.md

FAÇA:
1. IDENTIFICAR gaps (débitos não cobertos, áreas não analisadas)
2. AVALIAR riscos (segurança, regressão, integração)
3. VALIDAR dependências (ordem faz sentido?)
4. SUGERIR testes (testes pós-resolução, critérios de aceite)
5. DAR PARECER (APPROVED / NEEDS WORK)

CRIE: docs/reviews/qa-review.md

FORMATO:
## QA Review - Technical Debt Assessment

### Gate Status: [APPROVED / NEEDS WORK]

### Gaps Identificados
[áreas não cobertas]

### Riscos Cruzados
| Risco | Áreas Afetadas | Mitigação |

### Dependências Validadas
[ordem correta? bloqueios?]

### Testes Requeridos
[testes pós-resolução]

### Parecer Final
[comentários gerais]

**IMPORTANTE:** Marque APPROVED ou NEEDS WORK.
Se NEEDS WORK, retorne à FASE 4 para ajustes.
```

---

### FASE 8: Assessment Final

**Agente:** @architect
**Tipo:** Manual consolidation
**Output:** `docs/prd/technical-debt-assessment.md`
**Tempo:** 30-45 min
**Condicional:** Só se QA Review foi APPROVED

```
[ ] Verificar docs/reviews/qa-review.md status
[ ] Se NEEDS WORK → voltar à FASE 4
[ ] Se APPROVED → prosseguir
[ ] @architect finaliza assessment
```

**Prompt para @architect:**
```
Finalize o assessment incorporando TODOS os inputs:

LEIA:
1. docs/prd/technical-debt-DRAFT.md
2. docs/reviews/db-specialist-review.md
3. docs/reviews/ux-specialist-review.md
4. docs/reviews/qa-review.md

FAÇA:
1. Incorporar ajustes do @data-engineer
2. Incorporar ajustes do @ux-expert
3. Endereçar gaps do @qa
4. Recalcular prioridades com inputs
5. Definir ordem final de resolução

CRIE: docs/prd/technical-debt-assessment.md

ESTRUTURA:
# Technical Debt Assessment - FINAL

## Executive Summary
- Total de débitos: X
- Críticos: Y | Altos: Z
- Esforço total: XXX horas

## Inventário Completo de Débitos

### Sistema (validado @architect)
| ID | Débito | Severidade | Horas | Prioridade |

### Database (validado @data-engineer)
| ID | Débito | Severidade | Horas | Prioridade |

### Frontend/UX (validado @ux-expert)
| ID | Débito | Severidade | Horas | Prioridade |

## Matriz de Priorização Final
[consolidada]

## Plano de Resolução
[ordem, dependências, timeline]

## Riscos e Mitigações
[do QA review]

## Critérios de Sucesso
[métricas, testes]
```

---

### FASE 9: Relatório Executivo

**Agente:** @analyst
**Tipo:** Manual report
**Output:** `docs/reports/TECHNICAL-DEBT-REPORT.md` ⭐
**Tempo:** 30-45 min

```
[ ] Ler docs/prd/technical-debt-assessment.md
[ ] @analyst cria relatório para stakeholders
```

**Prompt para @analyst:**
```
Crie relatório executivo de awareness para stakeholders:

LEIA: docs/prd/technical-debt-assessment.md

FOCO EM:
- Custos claros (resolver vs NÃO resolver)
- Impacto no negócio (não técnico!)
- Timeline realista
- ROI da resolução

USE LINGUAGEM DE NEGÓCIO (não técnica).
VALORES EM R$ (considere R$150/h como base).

CRIE: docs/reports/TECHNICAL-DEBT-REPORT.md

ESTRUTURA:
# 📊 Relatório de Débito Técnico

## 🎯 Executive Summary (1 página)
- Situação atual (3 parágrafos)
- Números chave (total débitos, críticos, esforço, custo)
- Recomendação

## 💰 Análise de Custos
- Custo de RESOLVER (tabela por categoria)
- Custo de NÃO RESOLVER (riscos, probabilidade, impacto)

## 📈 Impacto no Negócio
- Performance (tempo carregamento, conversão)
- Segurança (vulnerabilidades, compliance)
- UX (problemas, abandono)
- Manutenibilidade (velocidade entrega)

## ⏱️ Timeline Recomendado
- Fase 1: Quick Wins (1-2 sem)
- Fase 2: Fundação (2-4 sem)
- Fase 3: Otimização (4-6 sem)

## 📊 ROI da Resolução
- Investimento vs Retorno esperado

## ✅ Próximos Passos
- [ ] Aprovar orçamento
- [ ] Definir sprint
- [ ] Alocar time
- [ ] Iniciar Fase 1

---

ESTE É O DOCUMENTO PARA APRESENTAR A STAKEHOLDERS!
```

---

### FASE 10: Planning (Epic + Stories)

**Agente:** @pm
**Tipo:** Command execution
**Output:** `docs/stories/epic-technical-debt.md` + `story-*.md`
**Tempo:** 30-60 min

#### FASE 10a: Create Epic

```
[ ] Ler docs/prd/technical-debt-assessment.md
[ ] @pm execute: *create-epic
```

**Prompt para @pm:**
```
Crie epic de resolução de débitos técnicos:

LEIA: docs/prd/technical-debt-assessment.md

EPIC DETAILS:
- Título: "Resolução de Débitos Técnicos - [Nome Projeto]"
- Descrição: Resumo do assessment
- Objetivo: Resolver débitos identificados
- Escopo: Quais débitos estão inclusos
- Timeline: Do relatório (Fase 9)
- Budget: Valor total estimado
- Critérios de sucesso

CRIE: docs/stories/epic-technical-debt.md

Comando: *create-epic
```

---

#### FASE 10b: Create Stories

```
[ ] Para cada débito priorizado:
    [ ] @pm execute: *create-story
```

**Prompt para @pm:**
```
Crie stories individuais para cada débito/grupo:

PARA CADA ITEM PRIORIZADO:
- Story com tasks claras
- Critérios de aceite específicos
- Testes requeridos (do QA review)
- Estimativa (do assessment)
- Definition of Done

PATTERN:
- Story 1.1: [Débito crítico 1]
- Story 1.2: [Débito crítico 2]
- Story 1.3: [Débito alto 1]
- Story 2.1: [Débito médio 1]
- ...

OUTPUT: docs/stories/story-X.X-*.md

Comando: *create-story (repetir para cada)
```

---

## ✅ WORKFLOW COMPLETO

```
[ ] PRÉ-REQUISITOS
    [ ] FASE 1: System Documentation
    [ ] FASE 2: Database Audit (se aplicável)
    [ ] FASE 3: Frontend Spec
    [ ] FASE 4: Initial Consolidation (DRAFT)
    [ ] FASE 5: DB Specialist Review
    [ ] FASE 6: UX Specialist Review
    [ ] FASE 7: QA General Review
         [ ] Se NEEDS WORK → voltar à FASE 4
         [ ] Se APPROVED → prosseguir
    [ ] FASE 8: Final Assessment
    [ ] FASE 9: Executive Report ⭐
    [ ] FASE 10: Planning (Epic + Stories)

[ ] ARTEFATOS FINAIS
    ✅ docs/architecture/system-architecture.md
    ✅ supabase/docs/SCHEMA.md (se DB)
    ✅ supabase/docs/DB-AUDIT.md (se DB)
    ✅ docs/frontend/frontend-spec.md
    ✅ docs/prd/technical-debt-DRAFT.md
    ✅ docs/reviews/db-specialist-review.md
    ✅ docs/reviews/ux-specialist-review.md
    ✅ docs/reviews/qa-review.md
    ✅ docs/prd/technical-debt-assessment.md
    ✅ docs/reports/TECHNICAL-DEBT-REPORT.md ⭐⭐⭐
    ✅ docs/stories/epic-technical-debt.md
    ✅ docs/stories/story-*.md (múltiplas)
```

---

## 📊 Saídas por Tipo de Usuário

| Usuário | Documento | Ação |
|---------|-----------|------|
| **CTO/VP Tech** | `TECHNICAL-DEBT-REPORT.md` | Review + apresentar |
| **CFO/Finance** | `TECHNICAL-DEBT-REPORT.md` (seção custos) | Aprovar budget |
| **Scrum Master** | `epic-technical-debt.md` | Planejar sprints |
| **Dev Team** | `story-*.md` | Implementar |
| **Architect** | `technical-debt-assessment.md` | Review arquitetura |

---

## 🔄 Looping de Revisão

Se QA Review indicar **NEEDS WORK**:

```
FASE 7: QA Review → NEEDS WORK
↓
@architect revisa DRAFT (FASE 4)
↓
Ajusta baseado em feedback
↓
Re-envia para validação (FASES 5-6)
↓
QA Review novamente (FASE 7)
↓
Se APPROVED → FASE 8
Se ainda NEEDS WORK → loop novamente
```

---

## 💡 Dicas de Execução

1. **Paralelização:** Fases 1-3 podem rodar em paralelo (agentes diferentes)
2. **Tempo:** Planejar 4-6 horas com agentes disponíveis
3. **Iteração:** Fases 4-8 são sequenciais por dependência
4. **Qualidade:** QA Review é critical gate (pode rejeitar)
5. **Apresentação:** FASE 9 é o deliverable principal para stakeholders

---

## 📞 Suporte

**Se travar em:**
- FASE 1-3: Verificar se agentes entendem projeto
- FASE 4: Consolidar dados com cuidado
- FASE 5-7: Reviewers precisam de clarity
- FASE 8: Re-enviar material incompleto
- FASE 9: Revisar números e ROI
- FASE 10: Usar template de story para consistência

---

**Próximo Passo:** Execute `@architect *brown-disc` para iniciar!
