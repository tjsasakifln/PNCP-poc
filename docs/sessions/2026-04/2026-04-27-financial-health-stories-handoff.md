# Session financial-health-stories-handoff — 2026-04-27

## Objetivo

Identificar e priorizar stories críticas para **saúde financeira da plataforma SmartLic** dentro do roadmap aprovado de 42 stories (3 epics, 8 sprints) gerado a partir da auditoria sistêmica pós-incidente P0 e do pivô estratégico 100% inbound (2026-04-26).

Esta sessão consome o trabalho prévio (plano aprovado + 42 stories Ready + PO validation 100% GO) e produz **mapa de criticalidade financeira** consumível pelo @pm para priorização de Sprint 1, e pelo @dev para sequenciamento de execução.

---

## Contexto autoritativo

- **Plano:** `/home/tjsasakifln/.claude/plans/sistema-est-amea-ado-por-serene-hanrahan.md`
- **Epics:** `docs/stories/2026-04/EPIC-{RES-BE,SEO-PROG,MON-FN}-2026-Q2.md`
- **Stories:** 42 arquivos `.md` em `docs/stories/2026-04/` (13 RES-BE + 14 SEO-PROG + 15 MON-FN)
- **PO validation:** 100% GO (42/42), score médio 9.5/10, 0 NO-GO, 7 conditional
- **Estado financeiro:**
  - n=2 signups em 30 dias (abaixo do noise floor)
  - Pre-revenue: 0 MRR pago, trial-only
  - Backlog trial→paid bloqueado até `n≥30` (memory `feedback_n2_below_noise_eng_theater`)
  - Pivô 2026-04-26: 100% inbound via SEO programático (off-page descartado)
  - GSC 28d baseline: 126 clicks, 9.9k impressions, CTR 1.3%, position 7.1
- **Estado operacional:**
  - Backend recém-recuperado de incidente P0 (PR #529, hotfix em 2 endpoints; 56 callsites totais sem budget)
  - Janela 7-14 dias antes da próxima onda Googlebot reincidir
  - 8 rotas SSR puras indexáveis ainda vulneráveis

---

## Tese de saúde financeira

A plataforma sobrevive ou morre em quatro caminhos financeiros distintos. **Story qualifica como "crítica financeiramente" se entra em pelo menos um destes caminhos:**

| Caminho | O que dá errado sem | Magnitude do dano |
|---|---|---|
| **A. Receita reconhecida** | Pagamento concluído mas plataforma marca como trial | Receita perdida 1:1 + churn por confusão |
| **B. Conversão funil** | Trial usuário não consegue chegar até checkout | Lost revenue oportunidade × N |
| **C. Operação funcional** | Wedge backend → 0 signups durante incidente | Linear: minutos × signup_rate × LTV |
| **D. Compliance** | LGPD violation Brasil | Multa ANPD até 2% receita global, máx R$ 50M |

Stories são classificadas em **Tier 1-4** abaixo, com mecanismo de dano explícito.

---

## Tier 1 — Receita direta em risco (Caminho A)

**Cada story aqui = dinheiro perdido 1:1 ou pagamento que entra mas não é reconhecido.**

| Story | Mecanismo de dano | Sprint | Score PO | Esforço |
|---|---|---|---|---|
| **MON-FN-002** Stripe webhook DLQ + retry exponencial | Handler crashes → evento perde → assinatura ativa em Stripe mas `profiles.plan_type=trial` no DB. Receita entra Stripe, plataforma trata user como inadimplente. | 1-2 | 10/10 | M (3-4d) |
| **MON-FN-003** Plan status cache invalidação atômica (Redis Pub/Sub) | TTL puro 5min → janela onde usuário pago vê paywall. UX hostil pós-pagamento → churn voluntário ("paguei e não funciona"). | 2 | 10/10 | M (3d) |
| **MON-FN-004** Race condition `/planos/obrigado` polling | Frontend redireciona antes do webhook confirmar `plan_type=paid` → "Obrigado" exibido com paywall ativo. Refund request inevitável. | 2 | 10/10 | M (2-3d) |
| **MON-FN-007** Dunning workflow (D+1, D+2, D+3, suspend D+4) | Payment fail = bloqueio imediato sem recovery. Benchmark Fortune-500: dunning recupera 15-30% de payment fails. Sem isso, todo `card_declined` vira churn permanente. | 4-5 | 10/10 | L (5-7d) |
| **MON-FN-009** Abandoned cart recovery (`checkout.session.expired` + email D+1/D+3) | Usuário inicia checkout mas sai antes de pagar → `session.expired` em 24h → 0 follow-up → lead morre. Benchmark e-commerce: abandoned cart email recupera 10-15%. | 4 | 9/10 | M (3-4d) |

**Total Tier 1:** 5 stories. Investimento: ~17-21 dias de dev. Retorno esperado (após n≥30): +30-50% receita reconhecida vs cenário sem.

---

## Tier 2 — Conversão de funil (Caminho B)

**Sem estas, tráfego inbound chega mas funil vaza antes do checkout.**

| Story | Mecanismo de dano | Sprint | Score PO | Esforço |
|---|---|---|---|---|
| **MON-FN-005** MIXPANEL_TOKEN startup assertion | Gap silenciou eventos `paywall_hit`, `trial_started` por período não definido (memory 2026-04-24). Funil cego = decisões editoriais SEO (EPIC B) e de produto são especulativas. n=2 baseline já é precário; tracking gap é fatal. | 1 | 10/10 | S (0.5-1d) |
| **MON-FN-006** 8 eventos funil backend completos (first_search → paid) | Funil Mixpanel mostra dropout fictício. Sem eventos `first_search`, `trial_expiring_d3/d1`, `trial_expired`, `checkout_started`, `payment_failed`, `trial_converted` → impossível identificar onde funil quebra → otimização é palpite. | 2-3 | 10/10 | L (5-7d) |
| **MON-FN-008** Free tier (5 buscas/mês) downsell paywall | Trial expira → paywall instantâneo → 0 retention. Sem free tier, leads inbound que não convertem em 14d viram churn permanente. Free tier converte parte deles em paid em meses subsequentes (compostagem). | 4-5 | 10/10 | L (5-7d) |
| **MON-FN-015** Email confirmation soft-bypass (browse + 1ª busca pré-verify) | Supabase força `email_verified` antes de qualquer ação valiosa → usuário fecha aba antes de confirmar email → 30-50% drop-off típico em B2B SaaS. Soft-bypass permite browse + 1ª busca, bloqueia apenas trial start. | 5 | 7/10 (conditional) | M (3d) |
| **MON-FN-001** Resend webhook HMAC verify | Bounces silenciosos → email `trial_started` não chega → usuário criou trial mas nunca soube que ativou → não retorna → churn invisível. Deliverability cega impede triagem. | 1 | 10/10 | S (1d) |
| **MON-FN-014** Onboarding tracking server-side (deprecate localStorage) | Métrica `first_search` via localStorage flag não é confiável (limpo por incognito, multi-device). Sem evento server-side, `n` cumulativo (gating do backlog trial→paid) não é audível. | 3 | 7/10 (conditional) | S (1d) |

**Total Tier 2:** 6 stories. Investimento: ~16-22 dias de dev. Retorno: destrava funil mensurável + reduz drop-off de email gate (estimado 20-35% de signups recuperados).

---

## Tier 3 — Operação funcional (Caminho C)

**Sem estas, backend cai sob carga e zera signups durante o incidente. Cada minuto down = receita futura perdida.**

| Story | Mecanismo de dano | Sprint | Score PO | Esforço |
|---|---|---|---|---|
| **RES-BE-001** Auditoria automatizada `.execute()` sem budget (CI gate) | Sem gate, regressão silenciosa em PRs futuros reintroduz callsites desprotegidos → próxima wave reincide P0. Custo de 1 hora down em produto inbound: ~3-5 signups perdidos × LTV. | 1 | 10/10 | M (2-3d) |
| **RES-BE-002** Hotfix budget temporal nas top-5 rotas (mfa, referral, founding, conta, sitemap) | Top-5 sustentam 80% requests Googlebot. Sem budget, próxima wave em 7-14d → wedge → 0 signups durante incidente. PR #529 cobriu apenas 2 endpoints; 32 callsites desprotegidos restam. | 1 | 10/10 | M (3d) |
| **RES-BE-011** Healthcheck `/health/live` + `/health/ready` dependency-aware | Stage 3 do incidente: `/health` sondava 5 APIs externas → falha 11/11 attempts sob load → Railway nunca promove novos containers → wedge perpetuado. Fix em PR #529, mas precisa generalizar e instrumentar. | 1 | 9/10 (conditional) | S (1d) |
| **RES-BE-013** Audit env vars Railway pós-incidente (CI gate) | `PYTHONASYNCIODEBUG=1` descoberto em prod durante Stage 2; debug flags persistem despercebidos → degradação latente que amplifica próximo P0. CI gate previne. | 1 | 10/10 | S (1d) |
| **SEO-PROG-001..005** Migrar 5 rotas SSR puro → ISR (cnpj, orgaos, itens, observatorio, fornecedores 2-seg) | Cada rota SSR puro indexável é gatilho de wedge na próxima Googlebot wave. SSG fan-out + concurrent crawl + DB pool exhaustion = recidiva PR #529. ISR + fallback blocking + AbortSignal.timeout elimina superfície. | 2-3 | 10/10 (×5) | M (3-4d cada) |
| **SEO-PROG-008** Verificar Dockerfile ARG BACKEND_URL Railway | Build SSG hits `localhost:8000` se var ausente → sitemap/4.xml renderiza com 0 URLs → GSC perde 60-70% das URLs indexáveis silenciosamente → tráfego inbound cai. Memory `reference_frontend_dockerfile_backend_url_gap`. | 1 | 10/10 | S (0.5-1d) |
| **SEO-PROG-006** Sitemap particionado + sitemap_index.xml | Cap Google 50k/sitemap; atual ~10k em sitemap/4.xml com margem 5x. Em 6-9 meses de SEO ramp, hit do cap = Google drop-out silencioso = tráfego inbound congelado. | 2-3 | 8/10 (conditional) | L (5-7d) |
| **RES-BE-003** Negative cache padrão em 41 failure paths | Sem negative cache, falha de query repete a cada request → amplificação de cascata downstream → DB pool consumido por queries falhando → wedge. Generaliza padrão hotfix do PR #529. | 2 | 10/10 | L (5-7d) |
| **RES-BE-010** Bulkheads asyncio nas 10 rotas top tráfego | Saturação de 1 rota afoga healthchecks de outras → false-positive de wedge → Railway recicla → cascade. Bulkhead isola por rota, devolve HTTP 503 + Retry-After=2 quando saturado. | 3 | 10/10 | M (3-4d) |

**Total Tier 3:** 13 stories (incluindo SEO-PROG-001..005 contadas individualmente). Investimento: ~30-40 dias de dev. Retorno: reduz superfície de wedge a ~0 sob carga 5x baseline; preserva janela de signups em ramp-up SEO.

---

## Tier 4 — Compliance financeiro (Caminho D)

**Stories de exposição legal direta a multa.**

| Story | Mecanismo de dano | Sprint | Score PO | Esforço |
|---|---|---|---|---|
| **MON-FN-010** LGPD data export endpoint (`POST /api/me/data-export`) | Brasil = LGPD obrigatório. Right to portability. Sem endpoint funcional com SLA <72h, ANPD pode multar até 2% receita global, máx R$ 50M. Mesmo pre-revenue, multa fixa pode ser aplicada. | 3-4 | 10/10 | M (3-4d) |
| **MON-FN-011** LGPD data deletion (right to erasure, soft + hard D+30) | Right to erasure obrigatório LGPD Art. 18. Sem endpoint + audit log + soft/hard delete pipeline → exposição legal direta a partir do primeiro request não atendido. | 4 | 10/10 | M (3-4d) |

**Total Tier 4:** 2 stories. Investimento: ~6-8 dias de dev. Retorno: elimina exposição legal binária. **Pre-revenue não isenta de LGPD.**

---

## Tier 5 — Visibilidade financeira (decisões informadas)

**Sem estas, decisões de pricing/produto pós-n≥30 são cegas.**

| Story | Mecanismo de dano | Sprint | Score PO | Esforço |
|---|---|---|---|---|
| **MON-FN-013** ARPU/MRR/churn analytics dashboard | Sem MRR (new + expansion + churn + contraction), ARPU, churn rate → impossível instrumentar pricing. Decisão de R$ 297 vs R$ 397 vs R$ 497 anual vira palpite. | 6 | 8/10 | M (3-4d) |
| **MON-FN-012** Cohort retention dashboard (W1/W4/W12) | Sem cohort retention, impossível responder "quantos trial signups de Maio ainda estão ativos em Agosto?". Decisão de investir em onboarding vs aquisição → palpite. | 6 | 9/10 | M (3-4d) |
| **SEO-PROG-013** GSC API ingestion → Mixpanel | Sem GSC ingest, decisões editoriais SEO (qual conteúdo escalar) baseadas em GSC web UI manual. Cross-validação com Mixpanel funnel ausente → impossível ligar tráfego SEO a conversão. | 6 | 10/10 | M (3-4d) |

**Total Tier 5:** 3 stories. Investimento: ~9-12 dias de dev. Retorno: habilita decisões empíricas de pricing + retention + SEO content prioritization no Sprint 6+.

---

## Sequenciamento financeiro recomendado (caminho crítico de receita)

Reordenado dos sprints originais do roadmap para priorizar saúde financeira:

### Sprint 1 (29/abr–05/mai) — Não-negociável anti-reincidência + observabilidade financeira

**Track Backend (P0 anti-wedge):**
- RES-BE-001 → RES-BE-002 → RES-BE-011 → RES-BE-013 (sequencial)

**Track Frontend (P0 reduce SSR surface):**
- SEO-PROG-008 (Dockerfile audit, paralelo)

**Track Monetização (P0 visibilidade + deliverability):**
- MON-FN-005 (MIXPANEL assertion — desbloqueia tudo)
- MON-FN-001 (Resend HMAC — paralelo, S effort)

**Saída do Sprint 1:** backend protegido contra próxima Googlebot wave + funil Mixpanel funcional + email deliverability mensurável.

### Sprint 2-3 (06–19/mai) — Receita reconhecida + funil instrumentado

**Track Receita (CRÍTICO Tier 1):**
- MON-FN-002 → MON-FN-003 → MON-FN-004 (sequencial; cada um desbloqueia o próximo)

**Track Funil (Tier 2):**
- MON-FN-006 (8 eventos completos; depende de MON-FN-005)
- MON-FN-014 (onboarding server-side)

**Track SEO (Tier 3 anti-wedge):**
- SEO-PROG-001..005 (5 rotas SSR→ISR, paralelos; depende de RES-BE-002 em staging)
- SEO-PROG-006 (sitemap particionado)

**Track Compliance (Tier 4):**
- MON-FN-010 (LGPD export, paralelo)

**Saída do Sprint 2-3:** receita reconhecida 1:1 com Stripe + funil mensurável + 5 rotas SEO escaláveis + LGPD export.

### Sprint 4-5 (20/mai–02/jun) — Recovery + retention + downsell

**Track Recovery (Tier 1):**
- MON-FN-007 (dunning) — recupera 15-30% payment fails
- MON-FN-009 (abandoned cart) — recupera 10-15% checkouts expirados

**Track Retention (Tier 2):**
- MON-FN-008 (free tier downsell)
- MON-FN-015 (email soft-bypass)

**Track Compliance (Tier 4):**
- MON-FN-011 (LGPD deletion)

**Track Backend resilience (Tier 3 contínuo):**
- RES-BE-003 (negative cache 41 paths)
- RES-BE-010 (bulkheads)

**Saída do Sprint 4-5:** recovery loops fechados + retention mecânica + LGPD compliance completa.

### Sprint 6 (03–09/jun) — Visibilidade financeira (Tier 5)

- MON-FN-012 (cohort retention)
- MON-FN-013 (ARPU/MRR/churn)
- SEO-PROG-013 (GSC ingest)

**Saída do Sprint 6:** dashboards financeiros prontos para decisão de pricing pós-n≥30.

---

## Estimativa conservadora de impacto financeiro

Premissas (cenário inbound em ramp-up, atingindo n=30 em 60-90 dias):

- LTV trial→paid hipotético: R$ 297/mês × 12 meses × 50% retenção = ~R$ 1.800/conta convertida
- Conversion rate trial→paid alvo: 8-12% (benchmark B2B SaaS pre-revenue)
- Volume signup pós-MON-FN-015 (email soft-bypass): +25% sobre baseline

| Story group | Mecanismo | Receita salva/recuperada | Horizonte |
|---|---|---|---|
| Tier 1 (5 stories) | Receita reconhecida + dunning + abandoned cart | 30-50% receita reconhecida adicional vs cenário sem | Imediato pós-Sprint 5 |
| Tier 2 (6 stories) | Funil mensurável + free tier + email bypass | +20-35% signups; +10-15% trial→paid | 60-90 dias |
| Tier 3 (13 stories) | Anti-wedge + escala SEO | Preserva 100% signup rate sob carga; habilita 10x tráfego | Imediato pós-Sprint 1; escala em 90-180d |
| Tier 4 (2 stories) | LGPD compliance | Elimina exposição multa até R$ 50M | Imediato pós-Sprint 4 |
| Tier 5 (3 stories) | Decisões pricing/retention informadas | Não-quantificável; precondição para alinhar pricing pós-n≥30 | Sprint 6+ |

**Conclusão:** investimento total ~80-100 dias de dev (1 dev FTE em 4-5 sprints) preserva e desbloqueia caminho crítico de receita. Sem este investimento, plataforma sobrevive operacionalmente mas não escala financeiramente.

---

## Stories explicitamente não-críticas para saúde financeira

Stories importantes mas que **não entram em nenhum dos 4 caminhos financeiros**. Mantê-las no backlog para qualidade de código / dev velocity, mas **não priorizar antes do Tier 1-4 acima**:

| Story | Por que não é crítica financeira |
|---|---|
| RES-BE-005, RES-BE-006, RES-BE-007, RES-BE-008 (god-module splits) | Reduz blast radius e velocidade de futura refator; não afeta receita ou wedge atual. |
| RES-BE-009 (test triage) | Habilita CI velocity e signal-to-noise; não afeta receita. |
| RES-BE-012 (circuit breaker Supabase) | Defense-in-depth incremental; redundante com RES-BE-002 + RES-BE-003 + RES-BE-010 cobertura combinada. |
| SEO-PROG-009 (bundle reduction) | Otimização LCP; impacto financeiro indireto via CTR (capturado em SEO-PROG-010). |
| SEO-PROG-010 (Lighthouse CI) | Gate de qualidade; previne regressão mas não desbloqueia receita. |
| SEO-PROG-011 (internal linking) | SEO incremental; impacto difuso. |
| SEO-PROG-012 (schema.org expansion) | Rich results — incremental sobre baseline. |
| SEO-PROG-014 (defer build CI) | Dev velocity; sem impacto financeiro. |
| RES-BE-004 (datalake observability) | Visibilidade técnica; sem impacto financeiro direto. |

---

## Riscos vivos (entrar em handoff de próxima sessão)

| Risco | Severidade | Mitigação |
|---|---|---|
| Próxima Googlebot wave em 7-14d sem RES-BE-002 + SEO-PROG-001..005 deployados | ALTO | Sprint 1 não-negociável; auditoria de progresso D+5 |
| Backlog trial→paid bloqueado até n≥30; risco de pricing prematuro | MÉDIO | Manter `feedback_n2_below_noise_eng_theater`; não decidir quotas em MON-FN-008 sem dados |
| LGPD endpoint não implementado expõe a multa ANPD | MÉDIO | Sprint 3-4 obrigatório; backup manual handler até deploy |
| Required Fixes de 7 stories conditional GO podem atrasar Sprint 1 | BAIXO | Resolver pré-Phase 3 conforme tabela em PO Validation; não bloqueia transição Ready |
| MIXPANEL_TOKEN ausente em prod (gap memory 2026-04-24) | DESCONHECIDO | MON-FN-005 Sprint 1 implementa assertion; verify atual via `railway variables --service bidiq-backend --kv \| grep MIXPANEL` antes de Sprint 1 |

---

## Pendências (donos + prazo)

- [ ] **Resolver Required Fixes pré-Phase 3** — @architect (RES-BE-005, SEO-PROG-006), @data-engineer (RES-BE-011), @dev (SEO-PROG-009, MON-FN-014, MON-FN-015) — antes de Sprint 1 commit
- [ ] **Auditar MIXPANEL_TOKEN backend Railway** — @devops — antes de Sprint 1 (verifica se gap memory 2026-04-24 ainda persiste)
- [ ] **Iniciar Sprint 1 P0 paralelos** — @dev — RES-BE-001/002/011/013, SEO-PROG-008, MON-FN-001/005 — janela 5 dias úteis
- [ ] **Validate-story-ready em Required Fixes resolvidos** — @po — ad-hoc conforme @architect/@dev resolvem TODOs
- [ ] **Soak monitor Sprint 1 deploy** — @devops — Locust 200 req/s top-10 rotas após Sprint 1 deploy; confirmar 0 wedge
- [ ] **Auditoria progresso Sprint 1** — agente agendado D+5 (2026-05-02) — abrir Sprint 2 stories conforme entrega Sprint 1

---

## Bootstrap empírico (próxima sessão)

| Probe | Comando | Esperado pré-Sprint 1 | Esperado pós-Sprint 1 |
|---|---|---|---|
| Stories Ready | `grep -c "Status:.*Ready" docs/stories/2026-04/{RES-BE,SEO-PROG,MON-FN}-*.md` | 42 | 42 (sem regressão) |
| `.execute()` desprotegidos | `python backend/scripts/audit_execute_without_budget.py` (após RES-BE-001) | 56 | < 30 (top-5 cobertas pós RES-BE-002) |
| MIXPANEL_TOKEN prod | `railway variables --service bidiq-backend --kv \| grep MIXPANEL_TOKEN` | desconhecido | presente; assertion ativa |
| `/health/ready` Railway | `curl https://api.smartlic.tech/health/ready -m 5` | 200 ou 503 (depende implementação atual) | 200 com ping Redis+Supabase <1s |
| GSC sitemap submissions | dashboard | 10 sitemaps, ~10k URLs | 10 sitemaps (paginado), 10k+ URLs sem regressão |
| Mixpanel funnel (signup→paid) | Mixpanel UI | 4/12 eventos (paywall_hit, signup, trial_started parcial) | 12/12 eventos visíveis |

---

## Memory updates (não-essenciais; opcionais)

- Considerar atualizar `project_smartlic_onpage_pivot_2026_04_26.md` com pointer para este handoff (roadmap consolidado).
- Considerar nova `reference_financial_health_tier_classification.md` se Tier 1-5 framework for reutilizado em sessões futuras de priorização.

---

## Próxima ação recomendada

1. `/dev` ou `/devops` validar bootstrap empírico (5 min).
2. Resolver Required Fixes (1-2h).
3. Iniciar Sprint 1 paralelizando 3 tracks: RES-BE-001 → RES-BE-002, SEO-PROG-008, MON-FN-005 (workspace ou worktrees separados).
4. `/schedule` agente D+5 para audit Sprint 1 + open Sprint 2.

**Status final desta sessão:** 42 stories Ready, 5 epics+plano disponíveis, mapa Tier 1-5 entregue. Pronto para Phase 3 implementation.
