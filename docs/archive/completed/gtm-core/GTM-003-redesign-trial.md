# GTM-003: Redesign do Trial — 7 Dias, Produto Integral

## Metadata
| Field | Value |
|-------|-------|
| **ID** | GTM-003 |
| **Priority** | P0 (GTM-blocker) |
| **Sprint** | Sprint 1 |
| **Estimate** | 8h |
| **Depends on** | GTM-002 (plano único deve existir primeiro) |
| **Blocks** | GTM-004 (onboarding), GTM-010 (conversão trial→paid) |

## Filosofia

> **"Trial não é uma versão limitada. É o produto completo por tempo limitado."**

> **"Você precisa EXPERIMENTAR a vantagem competitiva, não uma versão capada que não mostra o valor real."**

O trial atual oferece 3 buscas com funcionalidades restritas (sem Excel, sem Pipeline, IA básica de 200 tokens, histórico de 7 dias). Isso entrega uma versão "capada" que não demonstra o valor real do SmartLic. O usuário não experimenta análise estratégica completa, não vê o pipeline em ação, não entende a diferença da IA prioritária.

**Resultado:** Usuário completa trial sem entender o que está comprando.

## Problema

### Trial Atual (free_trial plan)

| Aspecto | Valor Atual | Problema |
|---------|------------|----------|
| Duração | 7 dias (via `expires_at`) | ✅ OK |
| Limite de buscas | 3 buscas/mês | ⚠️ Suficiente mas restritivo |
| Excel | ❌ Desabilitado | ❌ Não experimenta export real |
| Pipeline | ❌ Desabilitado | ❌ Não entende acompanhamento |
| IA | Básica (200 tokens) | ❌ Não vê análise estratégica |
| Histórico | 7 dias | ❌ Não vê abrangência temporal |
| Priority | Low | ⚠️ Busca pode ser mais lenta |

**Evidência de problema:**

```python
# backend/quota.py L62-75 (current)
"free_trial": {
    "max_requests_per_month": 3,
    "allow_excel": False,        # ← BLOQUEADO
    "allow_pipeline": False,      # ← BLOQUEADO
    "max_summary_tokens": 200,    # ← IA CAPADA
    "max_history_days": 7,        # ← HISTÓRICO MÍNIMO
    "priority": "low",            # ← BUSCA LENTA
}
```

**Impacto:**
- Usuário completa trial sem clicar em "Baixar Excel" (botão desabilitado)
- Usuário não adiciona licitações ao pipeline (feature invisível)
- Resumos IA são genéricos de 1 linha (não demonstra análise estratégica)
- Só vê licitações publicadas na última semana (não entende cobertura histórica)

## Solução: Trial = Produto Completo por 7 Dias

### Nova Estrutura do Trial (free_trial plan — updated)

| Aspecto | Atual | Novo | Justificativa |
|---------|-------|------|---------------|
| Duração | 7 dias | **7 dias** (manter) | Tempo suficiente para 3 análises bem pensadas |
| Limite | 3 buscas/mês | **3 análises completas** (manter) | Força qualidade, não quantidade |
| Excel | ❌ | ✅ **Habilitado** | Usuário baixa e vê qualidade do output |
| Pipeline | ❌ | ✅ **Habilitado** | Usuário adiciona licitações e vê acompanhamento |
| IA | 200 tokens | **10.000 tokens** (análise completa) | Vê resumos estratégicos de verdade |
| Histórico | 7 dias | **365 dias** | Entende cobertura temporal real |
| Priority | Low | **Normal** | Velocidade de busca igual ao pago |

**Mensagem:** "Experimente o SmartLic completo por 7 dias. Sem versão limitada. Você vai usar o mesmo produto que clientes pagos."

### Impacto Esperado

**Antes (trial capado):**
- Usuário completa trial → "OK, busca funciona, mas não entendi a diferença do manual"
- Conversão: baixa (produto não demonstra valor)

**Depois (trial integral):**
- Usuário completa trial → "Baixei 3 Excels priorizados, adicionei 12 licitações ao pipeline, vi análises de 200 palavras. Isso muda meu processo."
- Conversão: alta (produto demonstra valor tangível)

## Escopo — Backend

### Arquivo: `backend/quota.py`

**Mudança:** Atualizar `PLAN_CAPABILITIES["free_trial"]`

**Antes:**
```python
"free_trial": {
    "max_requests_per_month": 3,
    "allow_excel": False,
    "allow_pipeline": False,
    "max_summary_tokens": 200,
    "max_history_days": 7,
    "priority": "low",
}
```

**Depois:**
```python
"free_trial": {
    "max_requests_per_month": 3,         # Manter
    "allow_excel": True,                 # HABILITAR
    "allow_pipeline": True,              # HABILITAR
    "max_summary_tokens": 10000,         # IA COMPLETA (igual smartlic_pro)
    "max_history_days": 365,             # 1 ANO (igual smartlic_pro)
    "priority": "normal",                # VELOCIDADE NORMAL (igual smartlic_pro)
}
```

**Linhas afetadas:** L62-75 aproximadamente

**Sem migration SQL:** Capabilities são código Python, não database. Change é apenas código.

### Função: `check_and_increment_quota_atomic`

**Verificação:** Garantir que lógica de quota respeita novas capabilities.

- `allow_excel=True` → Botão "Baixar Excel" nos resultados deve estar habilitado
- `allow_pipeline=True` → Botão "Adicionar ao Pipeline" deve estar habilitado
- `max_summary_tokens=10000` → Passar para LLM service ao gerar resumo

**Nenhuma mudança de código necessária** — lógica já respeita `PLAN_CAPABILITIES`.

## Escopo — Frontend

### Arquivo: `frontend/app/signup/page.tsx`

**Mudança:** Atualizar copy do signup/trial

**Antes:**
```tsx
<h2>Teste Grátis por 7 Dias</h2>
<p>3 buscas gratuitas. Sem cartão de crédito.</p>
```

**Depois:**
```tsx
<h2>Experimente o SmartLic Completo por 7 Dias</h2>
<p>3 análises completas com todas as funcionalidades. Sem cartão de crédito.</p>
```

**Detalhamento:**
- Sub-headline: "Não é uma versão limitada. É o produto completo."
- Features do trial listadas:
  - ✅ Excel exportável
  - ✅ Pipeline de acompanhamento
  - ✅ Inteligência de decisão completa
  - ✅ Histórico de 1 ano
  - ✅ 3 análises incluídas

**Linhas afetadas:** Componente `TrialBenefits` (se existir) ou seção hero do `/signup`

### Arquivo: `frontend/lib/copy/valueProps.ts`

**Mudança:** Atualizar seção de trial CTAs

**Antes:**
```typescript
trial: {
  cta: "Teste Grátis",
  description: "3 buscas gratuitas por 7 dias"
}
```

**Depois:**
```typescript
trial: {
  cta: "Experimente Sem Compromisso",
  description: "Produto completo por 7 dias. 3 análises incluídas."
}
```

**Linhas afetadas:** ~30-50 (seção trial)

### Arquivo: `frontend/app/features/page.tsx`

**Mudança:** Atualizar seção de trial na features page

**Antes:**
```tsx
<p>Teste grátis com 3 buscas. Sem cartão.</p>
```

**Depois:**
```tsx
<p>7 dias do produto completo. Sem versão limitada. Sem cartão de crédito.</p>
```

**Linhas afetadas:** Seção "Como Começar" ou "Trial"

### Componente: Quota Display (quando trial)

**Arquivo:** `frontend/app/components/QuotaDisplay.tsx` (ou similar)

**Mudança:** Quando `plan_type === 'free_trial'`, mostrar:

```tsx
"Trial: 3 análises completas restantes. Expira em X dias."
```

**Não mostrar:**
- "Trial limitado"
- "Upgrade para Excel" (Excel já está habilitado)
- "Upgrade para IA completa" (IA já está completa)

## Acceptance Criteria

### Backend

- [x] **AC1: Usuário trial tem acesso a Excel, Pipeline, IA completa**
  - `PLAN_CAPABILITIES["free_trial"]["allow_excel"] == True`
  - `PLAN_CAPABILITIES["free_trial"]["allow_pipeline"] == True`
  - `PLAN_CAPABILITIES["free_trial"]["max_summary_tokens"] == 10000`
  - **Critério de validação:** Login com usuário trial → clicar "Baixar Excel" funciona, botão não está disabled

- [x] **AC2: Limite de 3 análises mantido (quota enforcement)**
  - `PLAN_CAPABILITIES["free_trial"]["max_requests_per_month"] == 3`
  - Após 3 buscas: quota esgotada, mensagem de upgrade
  - **Critério de validação:** Fazer 3 buscas com trial → 4ª busca retorna 429 com mensagem apropriada

- [x] **AC3: Histórico de 1 ano habilitado**
  - `PLAN_CAPABILITIES["free_trial"]["max_history_days"] == 365`
  - Busca com trial pode retornar licitações publicadas até 1 ano atrás
  - **Critério de validação:** Buscar licitações com `data_inicial` = hoje - 300 dias → retorna resultados

- [x] **AC4: Priority normal (não low)**
  - `PLAN_CAPABILITIES["free_trial"]["priority"] == "normal"`
  - Busca não é throttled ou colocada em fila de baixa prioridade
  - **Critério de validação:** Busca com trial tem mesmo tempo de resposta (~10-15s) que smartlic_pro

### Frontend — Copy

- [x] **AC5: Copy de signup diz "produto completo" não "buscas gratuitas"**
  - Headline: "Experimente o SmartLic Completo por 7 Dias" (ou similar)
  - Sub: Menciona "produto completo", "sem versão limitada"
  - Zero menções a "grátis", "teste", "trial limitado"
  - **Critério de validação:** Grep de "grátis", "limitado", "versão básica" em `signup/page.tsx` retorna zero

- [x] **AC6: Features do trial listadas explicitamente**
  - Lista inclui: Excel, Pipeline, IA completa, histórico 1 ano, 3 análises
  - Cada feature com ✅ (não "disponível no plano pago")
  - **Critério de validação:** Signup page exibe lista de features do trial

- [x] **AC7: ValueProps.ts atualizado**
  - `trial.cta` NÃO contém "grátis" ou "teste"
  - Preferred: "Experimente sem compromisso", "Ver como funciona", "Começar agora"
  - **Critério de validação:** `valueProps.ts` seção trial usa copy de experimentação (não de gratuidade)

### Frontend — Quota Messaging

- [x] **AC8: Ao esgotar 3 análises, mensagem focada em valor gerado**
  - Mensagem atual: "Trial expirado. Faça upgrade."
  - Mensagem nova: "Suas 3 análises do trial foram usadas. Uma única licitação ganha pode pagar o sistema. Continue por R$ 1.999/mês."
  - Tom: confiante, não desesperado
  - **Critério de validação:** Esgotar quota → ver mensagem que menciona ROI (não apenas "upgrade")

- [ ] **AC9: Ao expirar 7 dias, mensagem similar focada em experiência**
  - "Seu período de 7 dias terminou. Você experimentou o SmartLic completo. Continue tendo vantagem competitiva."
  - Zero menção a "trial acabou", "sem acesso", "bloqueado"
  - **Critério de validação:** Trial expirado (por tempo) → mensagem positiva focada em continuar

- [x] **AC10: Nenhuma feature é "gated" durante o trial — produto 100% funcional**
  - Botão "Baixar Excel": enabled (não disabled com tooltip "upgrade para desbloquear")
  - Botão "Adicionar ao Pipeline": enabled
  - Resumo IA: completo (não truncado com "... [upgrade para ver mais]")
  - **Critério de validação:** Navegar todas funcionalidades como trial user → zero tooltips/badges de upgrade

### Frontend — Features Page

- [x] **AC11: Features page atualizada**
  - Seção trial: "7 dias do produto completo. Sem versão limitada."
  - Comparação trial vs pago removida (não há diferença de features, só de quota/tempo)
  - **Critério de validação:** `features/page.tsx` não compara "trial vs pago" em termos de capabilities

## Definition of Done

- [ ] Todos os 11 Acceptance Criteria passam
- [x] Backend: `quota.py` atualizado e deployed
- [x] Frontend: signup, features, valueProps atualizados e deployed
- [ ] Teste end-to-end:
  - Criar novo trial account
  - Fazer 3 buscas completas
  - Baixar Excel de cada busca (verificar que funciona)
  - Adicionar licitações ao pipeline (verificar que funciona)
  - Ver resumos IA completos (200+ palavras)
  - Esgotar quota → ver mensagem correta
  - Esperar 7 dias (ou manipular `expires_at`) → ver mensagem de expiração correta
- [ ] Documentação atualizada: `docs/trial-experience.md` (se existir)
- [ ] Monitoring: Track trial→paid conversion nos próximos 14 dias (baseline para GTM-010)
- [ ] Merged to main, deployed to production

## File List

### Backend Modified
- `backend/quota.py` (L63-71, seção `free_trial` — full capabilities)
- `backend/tests/test_quota.py` (updated assertions for new capabilities)

### Frontend Modified
- `frontend/app/signup/page.tsx` (copy + trial features list)
- `frontend/lib/copy/valueProps.ts` (trial CTA, guarantee, comparison copy)
- `frontend/lib/plans.ts` (displayNamePt: "Gratuito" → "Avaliação")
- `frontend/app/features/page.tsx` (hero CTA + final CTA copy)
- `frontend/app/components/QuotaCounter.tsx` (análises copy, ROI messaging)
- `frontend/app/components/QuotaBadge.tsx` (análises copy, title attrs)
- `frontend/app/components/PlanBadge.tsx` (icon "G" → "A")
- `frontend/app/components/InstitutionalSidebar.tsx` (signup benefit copy)
- `frontend/app/components/ComparisonTable.tsx` (CTA copy)
- `frontend/app/components/landing/FinalCTA.tsx` (CTA + subtitle copy)
- `frontend/app/ajuda/page.tsx` (FAQ answers rewritten)
- `frontend/app/planos/page.tsx` (cancel FAQ, bottom CTA)
- `frontend/app/login/page.tsx` (error message copy)

### Tests Updated
- `frontend/__tests__/QuotaCounter.test.tsx` (all "buscas" → "análises")
- `frontend/__tests__/components/QuotaBadge.test.tsx` (all "buscas" → "análises")
- `frontend/__tests__/components/InstitutionalSidebar.test.tsx` (benefit copy)
- `frontend/__tests__/pages/SignupPage.test.tsx` (subtitle copy)
- `frontend/__tests__/pages/PlanosPage.test.tsx` (bottom CTA copy)
- `frontend/__tests__/PlanBadge.test.tsx` (icon "G" → "A", planName)
- `frontend/__tests__/free-user-balance-deduction.test.tsx` (0 análises)
- `frontend/e2e-tests/institutional-pages.spec.ts` (signup benefit)
- `frontend/e2e-tests/landing-page.spec.ts` (CTA name)

### No Migration Needed
- Capabilities são código Python, não database schema

## Notes

- Esta story depende de GTM-002 completar primeiro (plano único deve existir para que trial possa ser comparado ao smartlic_pro)
- Bloqueia GTM-004 (onboarding) pois o onboarding vai usar trial completo como "primeira experiência"
- Bloqueia GTM-010 (conversão trial→paid) pois a mensagem de conversão depende de quanto valor foi gerado durante trial completo
- **Estimativa de 8h:** 2h backend (quota.py + testing) + 4h frontend (copy updates + quota messaging) + 2h end-to-end testing
- **Risco:** Trial completo pode aumentar abuse (usuários criando múltiplas contas). Mitigação: rate limit por IP, email verification obrigatório
- **Oportunidade:** Trial completo aumenta word-of-mouth ("experimentei e realmente mudou meu processo") — pode reduzir CAC
