# STORY-GROWTH-001: Paid Acquisition Smoke Test — Google Ads R$ 300-500 em 7 dias

**Priority:** P1 — Testa viabilidade de CAC antes de escalar
**Effort:** S (2 dias setup + 7 dias run + 1 dia análise)
**Squad:** Founder (execução) + @dev (landing + tracking)
**Status:** Ready (condicional: ativar no gate D+30 ou D+45)
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Sprint:** Disparar W5-W6 dependendo do gate D+30

---

## Contexto

SEO orgânico leva 3-6 meses para tração meaningful. B2G outbound leva 2-6 semanas por lead. **Paid ads leva 1-7 dias para primeiro signal de CAC**.

Orçamento mínimo (R$ 300-500) é suficiente para responder:

1. Existe demanda searchável pelo problema que o SmartLic resolve?
2. Qual é o CAC real (não estimado)?
3. Qual a intenção dos cliques — é fit com produto ou é ruído?

Resultado possível:
- **CAC < R$ 500:** escalar. LTV/CAC favorável justifica investir.
- **CAC R$ 500-R$ 2.000:** depende de LTV observado. Iterar keywords e landing.
- **CAC > R$ 2.000 ou zero conversão:** kill paid acquisition. Voltar a foco outbound + SEO.

**Quando disparar:**
- Gate D+30 PASS + TIER 1 em execução: disparar em paralelo a STORY-B2G-001 continuation
- Gate D+45 sem pagante: disparar como experimento de última milha antes de pivot

**Impacto esperado:**
- Se CAC ≤ R$ 500 e conversão trial→paid bate 10%+: **story GROWTH-002** escala budget para R$ 3-5k/mês
- Se não: kill explícito, sem over-investment

---

## Acceptance Criteria

### AC1: Setup Google Ads
- [ ] Conta Google Ads ativa (se não existe) + billing configurado
- [ ] Conversion tracking configurado:
  - Signup completed (evento primário)
  - Trial started (secundário)
  - Checkout started (tertiário)
- [ ] Integração via Google Tag Manager ou gtag direto em `frontend/app/layout.tsx`
- [ ] Testar conversions em produção antes de lançar campanhas (verificar via GA Realtime)

### AC2: 3 campanhas segmentadas
- [ ] Campanha 1: **"Pesquisa genérica"** — keywords: "como participar de licitação", "software licitação", "sistema de editais"
- [ ] Campanha 2: **"Setor específico"** — keywords: "licitação [setor]" para top 5 setores (construção, TI, saúde, serviços, manutenção)
- [ ] Campanha 3: **"Long-tail intent"** — keywords: "licitação [UF] 2026", "edital [setor] [cidade]"
- [ ] Budget: R$ 20/dia × 7 dias × 3 campanhas = R$ 420 máx
- [ ] Lances: CPC manual inicial R$ 2-5 (ajustar após 2 dias)

### AC3: Landing page dedicada /lp/ads-v1
- [ ] Route: `frontend/app/lp/ads-v1/page.tsx` (noindex + nofollow)
- [ ] Copy **focado em outcome**, não em features:
  - Headline: "Licitações que combinam com você, não uma lista infinita"
  - Sub: "Analisamos 50 mil editais abertos com IA e entregamos só os que seu CNAE tem fit"
  - Social proof: "Avaliado por [N] empresas ativas" (quando houver dado real)
  - CTA: "Ver editais do meu CNAE" (form leve — só email + CNAE)
- [ ] Form submit cria conta "lite" (sem cartão ainda — coletar lead) e redireciona para primeira busca
- [ ] Performance >90 Lighthouse (paid ads penalizam slow pages)
- [ ] Mobile-first — maioria dos cliques virão de mobile

### AC4: UTM tracking e analytics
- [ ] URLs de campanhas usam `utm_source=google`, `utm_medium=cpc`, `utm_campaign=smoke-v1`, `utm_content=kw-{keyword}`
- [ ] Mixpanel event `ads_landing_viewed` com props `{utm_*}` 
- [ ] Mixpanel event `ads_form_submitted` com props `{utm_*, email, cnae}`
- [ ] Dashboard simple em Mixpanel: funnel `landed → submitted → signup → search → upgrade_view → paid`

### AC5: Relatório diário
- [ ] `docs/growth/reports/ads-smoke-test-day-{N}.md` (7 arquivos, um por dia)
- [ ] Métricas por dia:
  - Cliques
  - CPC médio
  - Landing page conversion rate
  - Signups criados
  - Trials iniciados (≥1 busca)
  - CAC calculado (gasto / signups)
  - Quality score médio Google Ads
- [ ] Decisão diária: continuar/ajustar/pausar

### AC6: Relatório final + decisão
- [ ] `docs/growth/reports/ads-smoke-test-final.md` ao fim dos 7 dias
- [ ] Estrutura:
  1. Gasto total
  2. Cliques totais
  3. Signups atribuídos
  4. CAC calculado
  5. Projeção de LTV baseada em cohort (se houver sinal)
  6. **Decisão vai/não-vai** com critério pré-definido:
    - CAC ≤ R$ 500 + ≥5 signups: GO — criar STORY-GROWTH-002
    - R$ 500 < CAC ≤ R$ 2.000: ITERATE — 1 nova iteração (landing ou keywords), orçamento adicional R$ 300
    - CAC > R$ 2.000 ou <3 signups: KILL — desligar campanhas, documentar aprendizado

---

## Arquivos

**Frontend (novos):**
- `frontend/app/lp/ads-v1/page.tsx`
- `frontend/app/lp/ads-v1/components/LeadForm.tsx`

**Backend (modificar):**
- `backend/routes/auth.py` (modificar — endpoint `POST /v1/auth/signup-lite` que cria profile sem senha + mágica auth via email)

**Documentação (nova):**
- `docs/growth/ads-smoke-test-plan.md` (plano operacional antes de lançar)
- `docs/growth/reports/ads-smoke-test-day-{1-7}.md` (gerados durante)
- `docs/growth/reports/ads-smoke-test-final.md` (gerado ao fim)
- `docs/growth/keyword-research-v1.md` (research prévio)

---

## Riscos e Mitigações

**Risco 1:** Quality score baixo Google Ads (primeira vez)
- **Mitigação:** Landing page-speed otimizada + copy relevante + keywords filtradas (não usar broad match no MVP)

**Risco 2:** Click fraud / bots
- **Mitigação:** Reserva IP para validação manual de conversões nas primeiras 48h

**Risco 3:** Google Ads approval demora (ramp up 2-3 dias)
- **Mitigação:** Submeter campanhas na W4, rodar smoke test na W5-W6

**Risco 4:** Gastar orçamento antes de aprender
- **Mitigação:** Budget máx rígido R$ 500 total + pause automático se CAC >R$ 2.000 após dia 3

---

## Definition of Done

- [ ] AC1-AC6 todos marcados `[x]`
- [ ] 7 dias de campanha rodados com dados coletados
- [ ] Relatório final commitado com decisão vai/não-vai documentada
- [ ] Se GO: `STORY-GROWTH-002-scale-paid-acquisition` criada
- [ ] Se KILL: campanhas pausadas, aprendizados documentados
- [ ] PR mergeado (código da landing + lead form)

---

## Dev Notes

**Landing copy-esboço:**
```
# Licitações que combinam com você, não uma lista infinita.

50.000 editais abertos agora no Brasil. Apenas N% fazem sentido para o seu CNAE.

O SmartLic usa IA para analisar cada edital e entregar só os que passam em 4 filtros:
- Modalidade compatível com seu histórico
- Valor dentro da sua capacidade operacional
- Localização atendível
- Timeline viável

Teste grátis por 14 dias. Sem cartão.

[Formulário: email + CNPJ]
[CTA: Ver editais do meu CNAE]

Já usado por [N] empresas.
```

**Keyword research:** fazer via Google Keyword Planner + Ahrefs (free tier) + SEMrush (free tier). Documentar top-30 keywords com volume + competição em `docs/growth/keyword-research-v1.md` antes de lançar.

---

## File List

_(populado pelo @dev + founder durante execução)_

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Condicional ao gate D+30/D+45. |
