# STORY-448: Barra de Progresso do Trial no Header

**Priority:** P1 — Urgência visual + engagement recognition
**Effort:** S (1-2 dias)
**Squad:** @dev + @qa
**Status:** Ready
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 1 — Semanas 1-2

---

## Contexto

Não há indicador visual persistente do progresso do trial. O usuário muitas vezes esquece que está num período de 14 dias. Uma barra de progresso no header cria urgência natural (scarcity) enquanto reconhece as ações do usuário (engagement positive reinforcement).

Benchmarks SaaS B2B mostram que trial progress indicators aumentam conversão em 0.5-1pp ao criar consciência de limite temporal sem ser agressivo.

**Impacto estimado:** +0.5pp em trial-to-paid conversion.

---

## Acceptance Criteria

### AC1: Barra persistente no header (apenas trial ativos)
- [ ] Componente `TrialProgressBar` renderizado abaixo da navbar principal
- [ ] Visível em TODAS as páginas autenticadas exceto: `/login`, `/signup`, `/onboarding`, `/auth/*`
- [ ] Visível APENAS para usuários com `plan_type === "free_trial"` E trial não expirado

### AC2: Conteúdo dinâmico da barra
- [ ] Texto: "Dia {X} de 14 — Você já fez {Y} buscas e encontrou {Z} editais."
- [ ] Botão/link à direita: "Ver Planos →" com href="/planos"
- [ ] {X}: calculado de `trial_expires_at` (disponível no contexto de auth)
- [ ] {Y} e {Z}: buscados do analytics summary endpoint existente (`GET /api/analytics?endpoint=summary` ou similar)
- [ ] Se Y/Z não disponíveis (erro de fetch): exibir apenas "Dia {X} de 14 — Veja os planos antes que seu trial expire."

### AC3: Cor muda com urgência do trial
- [ ] Dias 1-7: fundo verde claro, texto verde escuro (`bg-green-50 text-green-800`)
- [ ] Dias 8-11: fundo amarelo claro, texto amarelo escuro (`bg-yellow-50 text-yellow-800`)
- [ ] Dias 12-14: fundo vermelho claro, texto vermelho escuro (`bg-red-50 text-red-800`)

### AC4: CTA de conversão
- [ ] Link "Ver Planos →" usa `<Link href="/planos">` (não abre nova aba)
- [ ] CTA visualmente em destaque (bold ou cor de acento) dentro da barra

### AC5: Não aparece para pagantes/expirados
- [ ] Usuários com plano pago (`smartlic_pro`, `consultoria`, etc.) NÃO veem a barra
- [ ] Usuários com trial expirado NÃO veem a barra (eles veem o hard block em /planos)
- [ ] Usuários não autenticados NÃO veem a barra

### AC6: Exclusão de páginas
- [ ] Barra NÃO aparece em: `/login`, `/signup`, `/onboarding`, `/auth/callback`, `/recuperar-senha`, `/redefinir-senha`
- [ ] Barra NÃO aparece em páginas de marketing públicas: `/`, `/pricing`, `/features`, `/termos`, `/privacidade`

### AC7: Tracking Mixpanel
- [ ] Click em "Ver Planos →" dispara: `trial_progress_bar_cta_clicked` com propriedade `trial_day: number`

### AC8: Testes
- [ ] Teste: trial dia 5 → barra verde visível com "Dia 5 de 14"
- [ ] Teste: trial dia 10 → barra amarela
- [ ] Teste: trial dia 13 → barra vermelha
- [ ] Teste: pagante → barra não renderizada
- [ ] Teste: trial expirado → barra não renderizada
- [ ] Teste: página /login → barra não renderizada

---

## Scope

**IN:**
- Componente `TrialProgressBar.tsx`
- Integração no layout raiz (`layout.tsx`)
- Cálculo de dias baseado em `trial_expires_at`
- Tracking Mixpanel no CTA

**OUT:**
- Notificações push
- Emails triggered por dias restantes (→ STORY-444)
- Alteração no hard block de trial expirado (comportamento atual mantido)
- Countdown timer em tempo real (basta texto "Dia X de 14")

---

## Dependencies

- Contexto de autenticação disponível no `layout.tsx` (verificar como `useUser()` ou similar funciona no App Router)
- Analytics summary endpoint para {Y} e {Z} (pode ter loading state se lento)

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Analytics endpoint lento → CX degradada | Média | Mostrar barra com apenas o dia (sem Y/Z) enquanto carrega, atualizar quando disponível |
| App Router layout não tem acesso direto ao contexto de auth | Baixa | Usar hook `useUser()` do Supabase SSR (já utilizado em outros componentes) |

---

## File List

- [ ] `frontend/components/TrialProgressBar.tsx` — AC1, AC2, AC3, AC4, AC5: novo componente
- [ ] `frontend/app/layout.tsx` — AC1, AC6: integrar TrialProgressBar condicionalmente
- [ ] `frontend/__tests__/TrialProgressBar.test.tsx` — AC8: testes unitários

---

## Dev Notes

- Usar `usePathname()` (Next.js) para excluir rotas específicas
- Dados do trial: `trial_expires_at` pode estar no Supabase profile ou no contexto de auth. Verificar onde outros componentes buscam essa informação (ex: `TrialCountdown` existente)
- Analytics {Y} e {Z}: verificar se `GET /api/analytics?endpoint=summary` retorna `total_searches` e `total_results` — se não, o texto fallback é aceitável
- Componente deve ser client-side (`"use client"`) para usar hooks de roteamento e auth

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +0.5pp |
