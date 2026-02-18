# Relatório de Teste de Produção — 2026-02-18

**Testador:** Sessão automatizada via Playwright MCP
**URL:** https://smartlic.tech/
**Usuário:** tiago.sasaki@gmail.com (admin)
**Duração:** ~15 minutos

---

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Score Geral** | 4/10 |
| **Issues Críticos (P0)** | 1 |
| **Issues Altos (P1)** | 3 |
| **Issues Médios (P2)** | 1 |
| **Total de Pontos de Frustração** | 30+ |

**Veredicto:** O produto **não está pronto para uso por clientes pagantes**. A busca — ação principal do produto — falha silenciosamente mesmo quando o backend completa com sucesso. A UI tem problemas sistemáticos de encoding (20+ textos sem acentos) que comprometem a credibilidade de um produto B2B a R$1.999/mês.

---

## Pontos de Frustração Detalhados

### P0 — Crítico (bloqueia uso)

| # | Página | Frustração | Story |
|---|--------|-----------|-------|
| F27-F29 | /buscar | Busca completa no backend (1717 bids, Excel gerado) mas frontend mostra erro "Não foi possível processar". Usuário perde resultado. Progress bar reseta de 80%+ para erro. | GTM-FIX-033 |

### P1 — Alto (erode confiança)

| # | Página | Frustração | Story |
|---|--------|-----------|-------|
| F13-F24 | /buscar | **20+ textos sem acentos** em labels, filtros, validações: "Localizacao", "Avancados", "Licitacao", "Concorrencia Eletronica", "Pregao Eletronico", "Minimo", "Maximo", "Ate 50k", "opcoes" | GTM-FIX-034 |
| F25-F26,F28 | /buscar | Progress tracker abaixo da dobra. Formulário não recolhe durante busca. Dados contraditórios ("1/1 estado processado" mas 10%). | GTM-FIX-035 |
| F12 | /buscar | Copy diz "últimos 15 dias" mas período real é 10 dias (alterado em GTM-FIX-031). | GTM-FIX-036 |

### P2 — Médio (impacta conversão)

| # | Página | Frustração | Story |
|---|--------|-----------|-------|
| ~~F02~~ | ~~Landing~~ | ~~Sem botão "Login/Entrar" na navbar.~~ **INVALIDADO** — navbar tem Login para não-auth (`LandingNavbar.tsx:76-104`). Teste foi feito com sessão ativa. | ~~GTM-FIX-037~~ |
| F04-F06 | /signup | "Ja tem conta?" (sem acento), placeholder sem acentos. | GTM-FIX-034 |
| F08-F10 | /signup | Validações sem acentos: "Minimo", "maiuscula", "nao coincidem". | GTM-FIX-034 |
| F11 | /signup | Email inválido sem feedback — botão disabled sem explicação. | GTM-FIX-037 |
| F05 | /signup | Botão "Criar conta" disabled sem tooltip explicativo. | GTM-FIX-037 |

### P3 — Baixo (polish)

| # | Página | Frustração | Ação |
|---|--------|-----------|------|
| F01 | Landing | Contadores animados mostram "0" antes da animação trigger. | Fix menor — usar IntersectionObserver + fallback |
| F03 | Landing | CTA é `<button>` não `<a>` — sem JS, não navega. | Fix menor — usar `<Link>` do Next.js |
| F07 | /signup | Campo "Confirmar senha" é fricção extra para trial grátis. | Decisão de UX |
| F17 | /buscar | 27 estados selecionados por default — busca lenta. | Decisão de UX |

---

## Logs de Produção (Railway)

```
[PCP] Reached page limit (100). Total records (1807) may exceed fetched.
[PCP] Fetch complete: 36 records (truncated=True)
[CONSOLIDATION] PORTAL_COMPRAS: 36 records in 130091ms    ← 130 SEGUNDOS para PCP
[MULTI-SOURCE] PNCP: 1733 records, error=None
[MULTI-SOURCE] PORTAL_COMPRAS: 36 records, error=None
[CONSOLIDATION] Complete: 1769 raw -> 1717 deduped in 130110ms
✅ Excel available via signed URL (TTL: 60min)               ← SUCESSO no backend
```

**Análise:** O PCP levou 130s para um único estado (SP). Isso é 4x o timeout recomendado (30s). O backend completou mas a combinação de SSE failure + delay causou o frontend a desistir.

---

## Console Errors

| Tipo | Mensagem | Impacto |
|------|----------|---------|
| WARNING | "SSE connection error in useUfProgress" | Progress tracking degrada para simulação |
| ERROR | (após timeout) | Frontend mostra erro genérico |

## Network Issues

- Múltiplas chamadas `/api/me` em sequência (3+) — possível polling excessivo
- `supabase.co/auth/v1/token?grant_type=refresh_token` chamado na landing (session leak)
- Prefetch de `/planos` e `/buscar` na landing (bom para performance)

---

## Screenshots Capturados

1. `test-01-landing-hero.png` — Landing page hero
2. `test-02-signup-page.png` — Signup form
3. `test-03-already-logged-in.png` — Already logged in redirect
4. `test-04-buscar-bottom.png` — Filtros avançados sem acentos
5. `test-05-search-loading.png` — Loading state (formulário não recolheu)
6. `test-06-search-30s.png` — Progresso 10% após 30s
7. `test-07-search-error.png` — Erro final após busca bem-sucedida no backend

---

## Stories Criadas

| Story | Prioridade | Effort | Descrição |
|-------|-----------|--------|-----------|
| [GTM-FIX-033](GTM-FIX-033-search-frontend-timeout-disconnect.md) | P0 | M | Busca completa no backend mas frontend exibe erro (7 ACs) |
| [GTM-FIX-034](GTM-FIX-034-systematic-missing-accents.md) | P1 | S | 20+ textos sem acentos na UI (6 ACs) |
| [GTM-FIX-035](GTM-FIX-035-progress-tracker-ux.md) | P1 | M | Progress tracker UX — posição, contradições (6 ACs) |
| [GTM-FIX-036](GTM-FIX-036-copy-period-15-to-10-days.md) | P1 | XS | Copy "15 dias" → "10 dias" (2 ACs) |
| [GTM-FIX-037](GTM-FIX-037-signup-login-ux-friction.md) | P2 | S | Fricção no signup — email validation, disabled button (3 ACs) |

## Ordem de Execução Recomendada

1. **GTM-FIX-036** (XS, 30 min) — quick win, corrige informação incorreta
2. **GTM-FIX-034** (S, 2-3h) — credibilidade profissional
3. **GTM-FIX-033** (M, 4-6h) — o bug mais grave, requer investigação
4. **GTM-FIX-035** (M, 4-6h) — melhoria significativa de UX durante busca
5. **GTM-FIX-037** (S, 2-3h) — otimização de conversão

**Estimativa total:** 12-18h de trabalho dev.
