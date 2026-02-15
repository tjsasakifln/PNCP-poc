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
| **Status** | Pending |
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

- [ ] **AC1:** ZERO ocorrências de "PNCP" em qualquer texto visível ao usuário final
  - Landing page (`app/components/landing/*`)
  - Buscar page (`app/buscar/page.tsx`)
  - Planos page (`app/planos/page.tsx`)
  - Features page (`app/features/page.tsx`)
  - Footer (`app/components/Footer.tsx`)
  - Error messages do backend (`routes/search.py`, `routes/billing.py`, etc.)

- [ ] **AC2:** Footer usa linguagem genérica apropriada
  - **Atual:** "PNCP e outras fontes públicas"
  - **Novo:** "fontes oficiais de contratações públicas"

- [ ] **AC3:** Error messages do backend usam "nossas fontes" ou "fontes de dados"
  - **Exemplo 1:** "Nossas fontes de dados estão temporariamente indisponíveis. Tente novamente em alguns minutos."
  - **Exemplo 2:** "As fontes de dados estão temporariamente limitando consultas. Aguarde um momento e tente novamente."
  - **Nota:** Já parcialmente implementado em STORY-257A/B — verificar consistência

- [ ] **AC4:** `pncp_id` e links para `pncp.gov.br` nos resultados **permanecem**
  - Campo `pncp_id` é técnico e necessário para tracking interno
  - Links diretos para editais em pncp.gov.br são úteis ao usuário (não comunicam "vá usar o PNCP em vez do SmartLic")

### Banned Phrases e Preferred Phrases

- [ ] **AC5:** Atualizar `valueProps.ts` com banned phrases:
  ```typescript
  const BANNED_PHRASES = [
    'PNCP',
    'Portal Nacional de Contratações Públicas',
    'Portal Nacional',
    'pncp.gov.br', // Exceto em links diretos
    // ... outros termos banidos existentes (160x, 95%, 3 minutos, etc.)
  ];
  ```

- [ ] **AC6:** Atualizar `valueProps.ts` com preferred phrases:
  ```typescript
  const PREFERRED_PHRASES = [
    'fontes oficiais',
    'fontes governamentais',
    'cobertura nacional completa',
    'consolidação de fontes federais e estaduais',
    'dezenas de fontes em tempo real',
    // ... outros termos preferidos
  ];
  ```

### Validação por Grep

- [ ] **AC7:** Grep de `"PNCP"` no frontend retorna **ZERO matches** em arquivos user-facing
  ```bash
  # Deve retornar ZERO resultados (exceto imports técnicos e types):
  grep -r "PNCP" frontend/app/components/landing/
  grep -r "PNCP" frontend/app/buscar/
  grep -r "PNCP" frontend/app/planos/
  grep -r "PNCP" frontend/app/features/
  grep -r "PNCP" frontend/lib/copy/
  ```

- [ ] **AC8:** Grep de `"PNCP"` no backend (error messages) retorna ZERO matches em strings user-facing
  ```bash
  # Deve retornar ZERO resultados em strings de erro:
  grep -r "PNCP" backend/routes/search.py | grep "HTTPException"
  grep -r "Portal Nacional" backend/routes/
  ```

- [ ] **AC9:** Grep de `pncp_client` e `pncp_id` retorna matches **apenas em código técnico** (OK manter)

### Copy Estratégica

- [ ] **AC10:** Buscar page header usa "Inteligência de decisão" (não "Busca inteligente")
  - **Atual:** "Busca inteligente de licitações"
  - **Novo:** "Inteligência de decisão em licitações"

- [ ] **AC11:** Features page narrativa atualizada
  - **Atual:** "PNCP federal + portais estaduais"
  - **Novo:** "Consulta em tempo real todas as fontes federais e estaduais. Você nunca perde uma oportunidade por não saber que ela existe."

---

## Definition of Done

- [ ] Todos os Acceptance Criteria marcados como concluídos
- [ ] Grep validation passa (zero matches em user-facing code)
- [ ] Error messages auditados e atualizados
- [ ] Footer atualizado com linguagem genérica
- [ ] `valueProps.ts` e `comparisons.ts` atualizados com nova copy
- [ ] Banned/Preferred phrases atualizados
- [ ] Build passa (TypeScript clean, lint clean)
- [ ] PR aberto, revisado e merged
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
- [ ] Mensagens de timeout/rate limit já usam "fontes de dados" (não "PNCP")?
- [ ] Frontend error states exibem mensagens genéricas (não "erro do PNCP")?

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
