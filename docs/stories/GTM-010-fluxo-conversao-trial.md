# GTM-010: Fluxo de Conversão Trial → Assinatura

| Metadata | Value |
|----------|-------|
| **ID** | GTM-010 |
| **Priority** | P1 |
| **Sprint** | 2 |
| **Estimate** | 10h |
| **Type** | GTM (Go-to-Market) |
| **Dependencies** | GTM-002 (plano único definido), GTM-003 (trial configurado) |
| **Blocks** | — |
| **Status** | In Progress |
| **Created** | 2026-02-15 |
| **Squad** | Full-Stack (Backend + Frontend + UX) |

---

## Problem Statement

### Fluxo de Conversão Inexistente

**Problema central:** Não há fluxo otimizado para converter trial em assinante. O trial expira e o usuário vê mensagem genérica:

> "Trial expirado. Faça upgrade para continuar."

**Por que isso falha:**

1. **Não conecta com valor gerado:** Mensagem ignora o que o usuário fez durante o trial (buscas executadas, oportunidades encontradas, valor analisado)
2. **Tom genérico:** Não aproveita o contexto do usuário para personalizar argumentação
3. **Sem urgência real:** Não comunica custo de NÃO converter (perder oportunidades futuras)
4. **Sem notificação proativa:** Usuário descobre que trial expirou quando tenta usar — experiência frustrante

### Impacto no Negócio

- **Trial → Paid Conversion Rate:** Métrica crítica para sustentabilidade
- **Receita perdida:** Usuários que viram valor mas não converteram por falta de "empurrão" no momento certo
- **Churn precoce:** Usuários que experimentaram e abandonaram sem saber o valor total que deixaram para trás

---

## Solution/Scope

### Novo Fluxo de Conversão

```
Trial ativo (dia 1-5) → Valor sendo gerado (analytics tracking)
                           ↓
Trial ativo (dia 6) → Notificação proativa: "Amanhã seu acesso expira"
                           ↓
Trial expira (dia 7) → Tela de conversão customizada com valor gerado
                           ↓
                    "Você analisou X oportunidades totalizando R$ Y"
                           ↓
                    "Uma única licitação ganha pode pagar o sistema por um ano"
                           ↓
                    CTA: "Continuar por R$ 1.999/mês"
                           ↓
                    3 níveis de compromisso (mensal/semestral/anual)
```

---

## Arquivos Afetados

### Backend

| Arquivo | Mudança | Detalhes |
|---------|---------|----------|
| `backend/quota.py` (L651-665) | **Atualizar mensagem de trial expirado** | Substituir mensagem genérica por direcionamento para tela de conversão |
| **NOVO:** `backend/routes/analytics.py` | **Endpoint `/api/trial-value`** | Retorna valor total de oportunidades analisadas durante trial |
| `backend/routes/user.py` | **Endpoint para trial status** | Retornar `days_remaining`, `searches_used`, `searches_limit` |
| **NOVO:** `backend/services/notifications.py` | **Notificação dia 6 do trial** | Sistema de mensagens in-app (ou email se disponível) |

### Frontend

| Arquivo | Mudança | Detalhes |
|---------|---------|----------|
| **NOVO:** `frontend/app/components/TrialConversionScreen.tsx` | **Componente de conversão** | Tela full-screen com valor gerado + CTA upgrade |
| `frontend/app/buscar/page.tsx` | **Exibir TrialConversionScreen** | Quando `user.plan === 'free_trial' && isExpired`, renderizar tela de conversão (não toast genérico) |
| `frontend/app/components/TrialCountdown.tsx` (se não existir) | **Badge/banner de contagem regressiva** | Exibir "X dias restantes no trial" em header ou sidebar |
| `frontend/lib/api/analytics.ts` | **Fetch trial value** | Função para chamar `/api/trial-value` |

---

## Acceptance Criteria

### Backend: Analytics e Mensagens

- [x] **AC1:** Endpoint `GET /api/trial-value` retorna valor total analisado durante trial
  - Response schema:
    ```json
    {
      "total_opportunities": 47,
      "total_value": 12450000.00,  // R$ 12.45M
      "searches_executed": 3,
      "avg_opportunity_value": 264893.62,
      "top_opportunity": {
        "title": "Uniformes escolares - SP",
        "value": 850000.00
      }
    }
    ```
  - Cálculo: soma dos `valor_estimado` de todas as licitações retornadas nas buscas do usuário durante trial
  - Cache: 1 hora (analytics não precisam ser real-time)

- [x] **AC2:** Mensagem de trial expirado em `quota.py` atualizada
  - **Antes:** `"Trial expirado. Faça upgrade."`
  - **Depois:** `"Seu trial expirou. Veja o valor que você analisou e continue tendo vantagem."`
  - Backend retorna HTTP 403 com `detail` contendo mensagem

- [x] **AC3:** Endpoint `GET /api/user/trial-status` retorna status detalhado
  - Response schema:
    ```json
    {
      "plan": "free_trial",
      "days_remaining": 2,
      "searches_used": 2,
      "searches_limit": 3,
      "expires_at": "2026-02-22T14:30:00Z",
      "is_expired": false
    }
    ```

### Frontend: Tela de Conversão

- [x] **AC4:** Componente `TrialConversionScreen` criado
  - Renderização full-screen (não modal — tela inteira)
  - Estrutura:
    1. Hero: "Veja o que você descobriu em 7 dias"
    2. Estatísticas do trial (total opportunities, total value, top opportunity)
    3. Mensagem âncora: "Uma única licitação ganha pode pagar o sistema por um ano inteiro"
    4. 3 níveis de compromisso (mensal R$ 1.999, semestral R$ 1.799/mês, anual R$ 1.599/mês)
    5. CTA primário: "Continuar com SmartLic Pro - Mensal"
    6. Link secundário: "Ver outras opções de compromisso"

- [x] **AC5:** Tela de conversão mostra **valor gerado durante trial** (via `/api/trial-value`)
  - Exemplo: "Você analisou 47 oportunidades totalizando **R$ 12.450.000** em contratos públicos"
  - Destaque visual (número grande, cor esmeralda/verde sucesso)

- [x] **AC6:** Tom confiante, não desesperado
  - ✅ "Continue tendo vantagem competitiva"
  - ✅ "Seu concorrente pode estar usando SmartLic agora"
  - ❌ "Não perca!", "Última chance!", "Oferta limitada!"

### Frontend: Integração na Buscar Page

- [x] **AC7:** `buscar/page.tsx` detecta trial expirado e exibe `TrialConversionScreen`
  - Condição: `user.plan === 'free_trial' && isExpired`
  - Substituir toast genérico de "trial expirado" por tela de conversão
  - Usuário não consegue executar nova busca até converter ou fazer logout

- [x] **AC8:** Se usuário fechar tela de conversão (via "X" ou ESC), redirecionar para `/planos`
  - Não permitir voltar para `/buscar` — fluxo força decisão

### Notificação Proativa

- [x] **AC9:** Notificação no **dia 6 do trial** (1 dia antes de expirar)
  - Mensagem: "Seu acesso ao SmartLic expira amanhã. Continue tendo vantagem competitiva a partir de R$ 1.599/mês."
  - Implementação: sistema de mensagens in-app (banner persistente no topo) ou email
  - Link para `/planos` ou tela de conversão

- [x] **AC10:** Badge de contagem regressiva durante trial ativo
  - Exibir em header ou sidebar: "X dias restantes no trial"
  - Cores: verde (5-7 dias), amarelo (3-4 dias), vermelho (1-2 dias)
  - Link para `/planos` no hover

### 3 Níveis de Compromisso

- [x] **AC11:** Tela de conversão apresenta 3 billing periods (não 3 planos diferentes)
  - **Mensal:** R$ 1.999/mês — "Avaliação constante de oportunidades"
  - **Semestral:** R$ 1.799/mês (-10%) — "Consistência competitiva"
  - **Anual:** R$ 1.599/mês (-20%) — "Domínio do mercado"

- [x] **AC12:** Copy NUNCA usa "plano", "assinatura", "tier"
  - Usa: "nível de compromisso", "período de faturamento"
  - Alinha com GTM-002 (modelo de assinatura único)

### Acesso Pós-Expiração

- [x] **AC13:** Se usuário não converter, acesso a buscas novas bloqueado
  - Mensagem: "Seu trial expirou. Para continuar analisando oportunidades, escolha seu nível de compromisso."
  - Buscas antigas (salvas) permanecem acessíveis em modo leitura (sem executar novas)

- [ ] **AC14:** Usuário pode acessar pipeline de oportunidades salvas (read-only)
  - Argumento: "Você já identificou oportunidades. Não perca o acompanhamento delas."
  - CTA dentro do pipeline: "Continuar monitorando + buscar novas oportunidades"

---

## Definition of Done

- [ ] Todos os Acceptance Criteria marcados como concluídos
- [ ] Endpoint `/api/trial-value` implementado e testado
- [ ] Endpoint `/api/user/trial-status` implementado e testado
- [ ] Componente `TrialConversionScreen` implementado e responsivo (375px, 768px, 1024px)
- [ ] Integração em `buscar/page.tsx` funcional (trial expirado → tela de conversão)
- [ ] Notificação dia 6 implementada (in-app banner ou email)
- [ ] Badge de contagem regressiva exibido durante trial
- [ ] Copy alinhada com GTM-002 (plano único, 3 billing periods)
- [ ] Tom confiante validado (review de copy)
- [ ] Build passa (TypeScript clean, lint clean)
- [ ] Testes manuais: trial ativo → dia 6 notificação → dia 7 conversão → bloqueio
- [ ] PR aberto, revisado e merged
- [ ] Deploy em staging verificado

---

## Technical Notes

### Cálculo de Valor Analisado

**Endpoint:** `GET /api/trial-value`

**Query SQL (exemplo):**

```sql
SELECT
  COUNT(*) as total_opportunities,
  SUM(l.valor_estimado) as total_value,
  AVG(l.valor_estimado) as avg_opportunity_value,
  MAX(l.valor_estimado) as max_value
FROM licitacoes l
JOIN search_results sr ON l.id = sr.licitacao_id
JOIN searches s ON sr.search_id = s.id
WHERE s.user_id = :user_id
  AND s.created_at >= :trial_start_date
  AND s.created_at <= :trial_end_date
```

**Detalhes:**
- `trial_start_date`: `profiles.created_at` (signup date)
- `trial_end_date`: `profiles.trial_expires_at` ou `NOW()`
- Se usuário executou 0 buscas durante trial, retornar zeros (não erro)

**Edge case:** Se busca retornou 0 resultados (não encontrou oportunidades), `total_opportunities = 0`, `total_value = 0` — mensagem ajustada: "Configure seu perfil para encontrar oportunidades adequadas"

---

### Estrutura do TrialConversionScreen

```tsx
// frontend/app/components/TrialConversionScreen.tsx

interface TrialConversionScreenProps {
  trialValue: {
    total_opportunities: number;
    total_value: number;
    searches_executed: number;
  };
  onSelectPlan: (billingPeriod: 'monthly' | 'semiannual' | 'annual') => void;
}

export function TrialConversionScreen({ trialValue, onSelectPlan }: TrialConversionScreenProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-surface-0 to-surface-1 flex items-center justify-center p-4">
      <GlassCard variant="pricing" className="max-w-4xl w-full p-8 md:p-12">
        {/* Hero */}
        <h1 className="text-3xl md:text-4xl font-bold text-center mb-4">
          Veja o que você descobriu em 7 dias
        </h1>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-6 my-8">
          <StatCard
            label="Oportunidades Analisadas"
            value={trialValue.total_opportunities}
            icon={<Search />}
          />
          <StatCard
            label="Valor Total em Contratos"
            value={formatCurrency(trialValue.total_value)}
            icon={<TrendingUp />}
            gemAccent="emerald"
          />
          <StatCard
            label="Buscas Executadas"
            value={`${trialValue.searches_executed}/3`}
            icon={<Zap />}
          />
        </div>

        {/* Anchor message */}
        <div className="bg-gem-amethyst rounded-lg p-6 mb-8 text-center">
          <p className="text-lg md:text-xl font-semibold">
            Uma única licitação ganha pode pagar o sistema por um ano inteiro.
          </p>
        </div>

        {/* Billing periods */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <BillingPeriodCard
            period="monthly"
            price="R$ 1.999"
            label="Mensal"
            subtitle="Avaliação constante"
            onClick={() => onSelectPlan('monthly')}
          />
          <BillingPeriodCard
            period="semiannual"
            price="R$ 1.799"
            label="Semestral"
            subtitle="Consistência competitiva"
            discount="10%"
            onClick={() => onSelectPlan('semiannual')}
            recommended
          />
          <BillingPeriodCard
            period="annual"
            price="R$ 1.599"
            label="Anual"
            subtitle="Domínio do mercado"
            discount="20%"
            onClick={() => onSelectPlan('annual')}
          />
        </div>

        {/* CTA */}
        <div className="text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Seu concorrente pode estar usando SmartLic agora. Continue tendo vantagem.
          </p>
        </div>
      </GlassCard>
    </div>
  );
}
```

---

### Notificação Proativa (Dia 6)

**Opção 1: In-App Banner (Recomendado para MVP)**

```tsx
// frontend/app/components/TrialExpiringBanner.tsx

export function TrialExpiringBanner({ daysRemaining }: { daysRemaining: number }) {
  if (daysRemaining > 1) return null; // Só exibe no dia 6 (1 dia restante)

  return (
    <div className="bg-gem-ruby border-l-4 border-red-500 p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="font-semibold">
            Seu acesso ao SmartLic expira amanhã.
          </p>
        </div>
        <Link href="/planos">
          <Button variant="primary">
            Continuar tendo vantagem
          </Button>
        </Link>
      </div>
    </div>
  );
}
```

**Opção 2: Email (Se sistema de email estiver configurado)**

- Template: `backend/templates/email/trial_expiring.html`
- Subject: "Seu acesso ao SmartLic expira amanhã"
- Body: Valor gerado durante trial + CTA para planos
- Send: Cron job ou scheduled task no dia 6 (trial_expires_at - 1 day)

---

### Mensagens de Erro Atualizadas

**Arquivo:** `backend/quota.py` (L651-665)

**Antes:**

```python
raise HTTPException(
    status_code=403,
    detail="Seu período de trial expirou. Faça upgrade para continuar."
)
```

**Depois:**

```python
raise HTTPException(
    status_code=403,
    detail="Seu trial expirou. Veja o valor que você analisou e continue tendo vantagem.",
    headers={"X-Trial-Expired": "true"}  # Frontend pode usar para detectar
)
```

**Frontend detection:**

```tsx
try {
  await api.post('/buscar', payload);
} catch (error) {
  if (error.response?.status === 403 && error.response?.headers['x-trial-expired']) {
    // Exibir TrialConversionScreen
    setShowConversionScreen(true);
  }
}
```

---

### Alinhamento com GTM-002 e GTM-003

**GTM-002 (Plano Único):**
- Tela de conversão oferece **1 plano** (SmartLic Pro) com **3 billing periods**
- Não compara features entre "planos" (todas features são iguais)
- Diferenciação apenas por desconto de compromisso longo

**GTM-003 (Trial Completo):**
- Trial dá acesso a **produto completo** (Excel, Pipeline, IA 10k tokens, 365 dias histórico)
- Tela de conversão diz: "Continue com o mesmo acesso completo que você experimentou"
- Não há downgrade de features — apenas bloqueio de novas buscas

---

## File List

### Backend (New/Update)
- `backend/routes/analytics.py` (novo endpoint `/api/trial-value`)
- `backend/routes/user.py` (endpoint `/api/user/trial-status` se não existir)
- `backend/quota.py` (atualizar mensagem de trial expirado L651-665)
- `backend/services/notifications.py` (opcional: notificação dia 6)
- `backend/templates/email/trial_expiring.html` (opcional: email template)

### Frontend (New/Update)
- `frontend/app/components/TrialConversionScreen.tsx` (novo componente)
- `frontend/app/components/TrialExpiringBanner.tsx` (novo componente)
- `frontend/app/components/TrialCountdown.tsx` (novo ou atualizar badge)
- `frontend/app/buscar/page.tsx` (integração: detectar trial expirado → TrialConversionScreen)
- `frontend/lib/api/analytics.ts` (fetch trial value)
- `frontend/lib/api/user.ts` (fetch trial status se não existir)

---

## Testing Scenarios

### Scenario 1: Trial Ativo (Dias 1-5)
- **Ação:** Usuário executa busca
- **Esperado:** Busca funciona normalmente, badge "X dias restantes" visível

### Scenario 2: Trial Dia 6
- **Ação:** Usuário acessa `/buscar`
- **Esperado:** Banner amarelo/vermelho "Expira amanhã. Continuar tendo vantagem" visível

### Scenario 3: Trial Expirado (Dia 7+)
- **Ação:** Usuário tenta executar nova busca
- **Esperado:** `TrialConversionScreen` renderizada full-screen, mostrando valor analisado

### Scenario 4: Trial Expirado, 0 Buscas Executadas
- **Ação:** Usuário nunca executou busca, trial expirou
- **Esperado:** `TrialConversionScreen` renderizada, mas com mensagem ajustada: "Configure seu perfil e descubra oportunidades"

### Scenario 5: Conversão via Tela
- **Ação:** Usuário clica "Continuar com Mensal" na tela de conversão
- **Esperado:** Redireciona para checkout Stripe, após pagamento → plan = smartlic_pro

### Scenario 6: Fechar Tela de Conversão
- **Ação:** Usuário clica "X" ou ESC na tela de conversão
- **Esperado:** Redireciona para `/planos`, não permite voltar para `/buscar`

---

## Related Stories

- **GTM-002:** Plano único R$ 1.999 (tela de conversão oferece 3 billing periods deste plano)
- **GTM-003:** Trial completo (trial com produto integral, não versão limitada)
- **GTM-001:** Landing rewrite (alinhamento de tom: confiante, focado em resultado)
- **GTM-008:** IA reposicionamento (mensagens focam em "valor analisado", não "buscas executadas")

---

*Story created from consolidated GTM backlog 2026-02-15*
