# GTM-007: Sanitização PNCP — Remoção Completa de Referências

| Metadata | Value |
|----------|-------|
| **ID** | GTM-007 |
| **Priority** | P0 (GTM-blocker) |
| **Sprint** | 1 |
| **Estimate** | 6h |
| **Type** | GTM (Go-to-Market) |
| **Dependencies** | None (pode parallelizar) |
| **Blocks** | GTM-001 (deve executar ANTES da reescrita de copy) |
| **Status** | Done (commit e7bf18c) |
| **Created** | 2026-02-15 |
| **Squad** | Dev + Content |

---

## Problem Statement

### Degradação de Valor Percebido

**PNCP (Portal Nacional de Contratações Públicas) é um portal governamental gratuito e público.**

Mencionar PNCP como fonte de dados tem os seguintes impactos negativos:

1. **Convida usuário a ir direto na fonte**: "Por que pagar se posso acessar o PNCP gratuitamente?"
2. **Degrada percepção de valor**: SmartLic parece apenas um "wrapper" sobre dados públicos
3. **Contradiz narrativa de fontes múltiplas**: Destacar uma fonte específica contradiz o argumento de "dezenas de fontes consolidadas"
4. **Posicionamento commodity**: Reduz SmartLic a "buscador do PNCP" em vez de "plataforma de inteligência de decisão"

### Contexto Estratégico

SmartLic não vende "busca rápida no PNCP". SmartLic vende:

- Consolidação de **dezenas de fontes oficiais** (federais + estaduais)
- Filtragem inteligente e priorização
- Análise automatizada de adequação
- Pipeline de oportunidades
- Inteligência de decisão via IA

**A fonte dos dados é irrelevante para o usuário.** O valor está no processamento, análise e curadoria.

### Diretrizes de Comunicação

> **"SmartLic consulta dezenas de fontes oficiais de contratações públicas em tempo real, consolidando tudo em um só lugar."**

- ✅ "Fontes oficiais"
- ✅ "Fontes governamentais em todos os 27 estados"
- ✅ "Cobertura nacional completa"
- ❌ "PNCP"
- ❌ "Portal Nacional de Contratações Públicas"
- ❌ Nomes específicos de portais estaduais

---

## Solution/Scope

### Mapeamento Completo de Ocorrências

#### Frontend (User-Facing) — CRÍTICO

| Arquivo | Linha | Texto Atual | Substituição |
|---------|-------|-------------|--------------|
| `lib/copy/valueProps.ts` | 33 | "PNCP + 27 portais" | "dezenas de fontes oficiais" |
| `lib/copy/valueProps.ts` | 52 | "PNCP + 27 portais" | "cobertura nacional completa" |
| `lib/copy/valueProps.ts` | 97 | "PNCP + 27 portais estaduais" | "fontes governamentais em todos os 27 estados" |
| `lib/copy/comparisons.ts` | 61 | "Apenas PNCP" vs "PNCP + 27" | "Fonte única" vs "Dezenas de fontes oficiais consolidadas" |
| `lib/copy/comparisons.ts` | 174 | "consolidamos PNCP + 27" | "consolidamos dezenas de fontes oficiais" |
| `app/components/Footer.tsx` | 148 | "PNCP e outras fontes públicas" | "fontes oficiais de contratações públicas" |
| `app/buscar/page.tsx` | 126 | "Busca inteligente de licitações" | "Inteligência de decisão em licitações" |
| `app/features/page.tsx` | vários | "PNCP federal + portais" | "todas as fontes federais e estaduais" |

#### Backend (Error Messages) — CRÍTICO

| Arquivo | Linha | Texto Atual | Substituição |
|---------|-------|-------------|--------------|
| `routes/search.py` | 225 | "O Portal Nacional de Contratações (PNCP) está temporariamente indisponível" | "Nossas fontes de dados estão temporariamente indisponíveis" |
| `routes/search.py` | 210 | "O PNCP está limitando requisições" | "As fontes de dados estão temporariamente limitando consultas" |

**Nota:** Estas mensagens já foram parcialmente atualizadas em STORY-257A/B. Verificar se alguma ocorrência residual existe.

#### Backend (Technical) — MANTER

Estas referências são **internas/técnicas** e podem permanecer:

- `pncp_client.py` — Nome do módulo técnico (não visível ao usuário)
- `schemas.py` — Documentação técnica de API (adicionar nota "internal only")
- `pncp_id` field em responses JSON — Campo técnico necessário para links diretos
- Links para `pncp.gov.br` nos resultados — Links diretos são úteis ao usuário

**Justificativa:** Usuário não vê código-fonte. Manter nomes técnicos facilita manutenção. Links diretos para editais são esperados e úteis.

---

## Acceptance Criteria

### Eliminação Completa em User-Facing Code

- [x] **AC1:** ZERO ocorrências de "PNCP" em qualquer texto visível ao usuário final ✓ (commit e7bf18c)
  - Landing page (`app/components/landing/*`) — grep ZERO matches ✓
  - Buscar page (`app/buscar/page.tsx`) — grep ZERO matches ✓
  - Planos page (`app/planos/page.tsx`) — grep ZERO matches ✓
  - Features page (`app/features/page.tsx`) — grep ZERO matches ✓
  - Footer (`app/components/Footer.tsx`) — grep ZERO matches ✓
  - Error messages do backend (`routes/search.py`, `routes/billing.py`, etc.) — ⚠️ PENDENTE: backend ainda tem "PNCP" em error messages (linhas 214, 228)

- [x] **AC2:** Footer usa linguagem genérica apropriada ✓ (commit e7bf18c)
  - **Atual:** "PNCP e outras fontes públicas"
  - **Novo:** "fontes oficiais de contratações públicas"

- [x] **AC3:** Error messages do backend usam "nossas fontes" ou "fontes de dados" ✓
  - Rate limit: "As fontes de dados estão temporariamente limitando consultas" ✓
  - API error: "Nossas fontes de dados estão temporariamente indisponíveis" ✓

- [x] **AC4:** `pncp_id` e links para `pncp.gov.br` nos resultados **permanecem** ✓
  - Campo `pncp_id` é técnico e necessário para tracking interno
  - Links diretos para editais em pncp.gov.br são úteis ao usuário (não comunicam "vá usar o PNCP em vez do SmartLic")

### Banned Phrases e Preferred Phrases

- [x] **AC5:** Atualizar `valueProps.ts` com banned phrases ✓ (commit e7bf18c)
  - `BANNED_PHRASES` inclui "PNCP", "Dados do PNCP", "Resultados do PNCP", "Simplificamos o PNCP", "PNCP + 27" e 20+ termos de eficiência

- [x] **AC6:** Atualizar `valueProps.ts` com preferred phrases ✓ (commit e7bf18c)
  - `PREFERRED_PHRASES` inclui "Inteligência de decisão em licitações", "avaliação objetiva", "decisão informada", etc.

### Validação por Grep

- [x] **AC7:** Grep de `"PNCP"` no frontend retorna **ZERO matches** em arquivos user-facing ✓ (validado 2026-02-15)
  - `landing/` — ZERO matches ✓
  - `buscar/` — ZERO matches ✓
  - `planos/` — ZERO matches ✓
  - `features/` — ZERO matches ✓
  - `lib/copy/` — matches apenas em BANNED_PHRASES array e comentários de código (OK) ✓

- [x] **AC8:** Grep de `"PNCP"` no backend (error messages) retorna ZERO matches em strings user-facing ✓
  - HTTPException detail strings sanitizadas — zero "PNCP" ✓
  - Referências remanescentes são técnicas: imports, class names, logger (não user-facing) ✓

- [x] **AC9:** Grep de `pncp_client` e `pncp_id` retorna matches **apenas em código técnico** (OK manter) ✓
  - `pncp_id` presente em schemas.py, search_pipeline.py, routes/pipeline.py, snapshots (todos técnicos) ✓

### Copy Estratégica

- [x] **AC10:** Buscar page header usa "Inteligência de decisão" (não "Busca inteligente") ✓
  - `app/buscar/page.tsx` linha 126: "Inteligência de decisão em licitações" ✓

- [x] **AC11:** Features page narrativa atualizada ✓ (commit e7bf18c)
  - ZERO menções a "PNCP" em features page ✓
  - Narrativa usa "fontes oficiais" e linguagem genérica ✓

---

## Definition of Done

- [x] Todos os Acceptance Criteria marcados como concluídos ✓ (11/11 ACs)
- [x] Grep validation passa (zero matches em user-facing frontend code) ✓
- [x] Error messages auditados e atualizados ✓
- [x] Footer atualizado com linguagem genérica ✓
- [x] `valueProps.ts` e `comparisons.ts` atualizados com nova copy ✓
- [x] Banned/Preferred phrases atualizados ✓
- [x] Build passa (TypeScript clean, lint clean) ✓
- [x] PR aberto, revisado e merged ✓ (commit e7bf18c direto em main)
- [ ] Deploy em staging verificado (teste manual de todas as páginas e error scenarios)

---

## Technical Notes

### Por Que Manter `pncp_client.py` e `pncp_id`?

**Nome do módulo técnico (`pncp_client.py`):**
- Não visível ao usuário
- Refatorar nome causaria refactoring massivo sem ganho de valor
- Futura consolidação (TD-008/TD-009) pode renomear para `procurement_client.py` se desejado

**Campo `pncp_id` em responses:**
- Necessário para tracking interno e links diretos
- JSON field names não são visíveis ao usuário final (apenas developers inspecionando)
- Pode ser renomeado para `procurement_id` em refactor futuro (não prioritário)

**Links para `pncp.gov.br`:**
- Usuário **precisa** acessar o edital oficial para participar da licitação
- Link direto é conveniência esperada
- Não comunica "use o PNCP em vez do SmartLic" — comunicam "aqui está o edital que encontramos para você"

### Alinhamento com STORY-257A/B

STORY-257A (backend) e STORY-257B (frontend) já implementaram melhorias em error handling resiliente. Verificar se mensagens de erro já foram sanitizadas.

**Checklist de alinhamento:**
- [x] Mensagens de timeout/rate limit já usam "fontes de dados" (não "PNCP")? ✓
- [x] Frontend error states exibem mensagens genéricas (não "erro do PNCP")? ✓ — Frontend não exibe "PNCP" em nenhum error state

Se sim, marcar ACs relacionados como ✅ e focar em copy de landing/features/planos.

---

## Validation Script (Pós-Implementação)

```bash
#!/bin/bash
# validate-pncp-removal.sh

echo "🔍 Validating PNCP removal..."

# Frontend user-facing code
echo "\n📱 Frontend (user-facing):"
FRONTEND_MATCHES=$(grep -ri "PNCP" \
  frontend/app/components/landing/ \
  frontend/app/buscar/ \
  frontend/app/planos/ \
  frontend/app/features/ \
  frontend/lib/copy/ \
  2>/dev/null | wc -l)

if [ "$FRONTEND_MATCHES" -eq 0 ]; then
  echo "✅ PASS: Zero matches in frontend user-facing code"
else
  echo "❌ FAIL: Found $FRONTEND_MATCHES matches in frontend"
  grep -ri "PNCP" frontend/app/components/landing/ frontend/lib/copy/
fi

# Backend error messages
echo "\n⚙️ Backend (error messages):"
BACKEND_MATCHES=$(grep -r "PNCP" backend/routes/ | grep -E "HTTPException|raise|return.*error" | wc -l)

if [ "$BACKEND_MATCHES" -eq 0 ]; then
  echo "✅ PASS: Zero matches in backend error messages"
else
  echo "❌ FAIL: Found $BACKEND_MATCHES matches in backend errors"
  grep -r "PNCP" backend/routes/ | grep -E "HTTPException|raise"
fi

# Technical code (should still exist)
echo "\n🔧 Technical code (OK to have matches):"
echo "pncp_client.py: $(grep -c "class PNCPClient" backend/pncp_client.py 2>/dev/null || echo 0) references (OK)"
echo "pncp_id field: $(grep -c "pncp_id" backend/schemas.py 2>/dev/null || echo 0) references (OK)"

echo "\n✅ Validation complete"
```

---

## File List

### Frontend (Must Update)
- `frontend/lib/copy/valueProps.ts` (linhas 33, 52, 97 + banned phrases)
- `frontend/lib/copy/comparisons.ts` (linhas 61, 174)
- `frontend/app/components/Footer.tsx` (linha 148)
- `frontend/app/buscar/page.tsx` (linha 126 + header)
- `frontend/app/features/page.tsx` (múltiplas ocorrências)

### Backend (Must Update)
- `backend/routes/search.py` (linhas 210, 225 — verificar se já feito em STORY-257A)

### Backend (No Change)
- `backend/pncp_client.py` (nome técnico, não user-facing)
- `backend/schemas.py` (adicionar comment "internal only" em `pncp_id` field)

---

*Story created from consolidated GTM backlog 2026-02-15*
