# GTM Validation Report — SmartLic

**Date:** 2026-02-25
**Squad:** squad-gtm-validation-final
**Methodology:** 6 parallel investigation tracks + consolidation
**Auditors:** Analyst, UX Expert, QA, DevOps, Product Owner, Architect (AI agents)

---

## EXECUTIVE SUMMARY

# VERDICT: CONDITIONAL-GO

**SmartLic pode ir ao mercado em até 7 dias, condicionado à resolução de 3 BLOCKERs operacionais e 1 BLOCKER estratégico.**

O produto tem tecnologia genuinamente diferenciada (classificação IA, viabilidade 4 fatores, agregação multi-fonte), landing page profissional, infraestrutura estável, e segurança sólida (8.9/10). Porém, a experiência de busca (o core do produto) tem falhas de UX que causarão churn imediato, e o pricing está 5-13x acima do mercado sem social proof para justificar.

**A recomendação é: lançar em modo "beta privado com convite" a R$499/mês (ou free com cap) enquanto resolve os BLOCKERs, e escalar pricing após validação com 10-20 early adopters.**

---

## DECISION MATRIX

### BLOCKERs (4) — Must fix before ANY paid acquisition

| # | Track | Issue | Fix Estimate | Impact se não resolver |
|---|-------|-------|--------------|----------------------|
| **B1** | A+E | **Pricing 5-13x acima do mercado** (R$1.999 vs R$149-397 dos concorrentes) sem social proof, sem features de execução (auto-bid, propostas, alertas) | Decisão estratégica: 1 dia | Zero conversões de tráfego frio |
| **B2** | B | **Barra de progresso trava em 10% por 90+ segundos** — não reflete progresso real por UF | 2-3 dias de dev | Usuário trial conclui que o produto está quebrado |
| **B3** | B | **Duas mensagens de erro sobrepostas na falha** (caixa vermelha + card cinza "fontes indisponíveis") | 1 dia de dev | Sobrecarga cognitiva → abandono |
| **B4** | A | **Sem alertas por email/WhatsApp** — todo concorrente desde R$45/mês oferece | 3-5 dias de dev | Feature table-stakes ausente |

### HIGH (12) — Fix within 2 weeks of launch

| # | Track | Issue | Fix Estimate |
|---|-------|-------|-------------|
| H1 | B+E | Zero social proof (0 depoimentos, 0 logos, 0 cases) | 3 dias (coletar de beta users) |
| H2 | E | Termos de Serviço menciona planos fantasma (Free/Professional/Enterprise) | 30 min |
| H3 | A | Apenas 3 fontes de dados vs 19+ portais (Siga Pregão) ou 6.000+ (ConLicitação) | Roadmap (não bloqueia GTM) |
| H4 | A | Sem features de execução (auto-bid robot, geração de propostas, gestão documental) | Roadmap (não bloqueia GTM) |
| H5 | B | Busca 60-120s para 27 UFs com feedback insuficiente | 2 dias (default para UFs do onboarding) |
| H6 | B | Estados "Indisponível" (X vermelho) sem explicação ou retry individual | 1 dia |
| H7 | B | Botão "Tentar novamente" em vermelho (sinal de perigo, não de ação) | 2 horas |
| H8 | C | CVEs em Starlette (2) + python-multipart (1) — no request path | 1 dia |
| H9 | D | PNCP health canary usa formato de data errado + falta parâmetro obrigatório | 2 horas |
| H10 | D | `PNCP_TIMEOUT_PER_MODALITY=120` ignorado no Railway (stale config) | 5 minutos |
| H11 | F | Senhas hardcoded em `seed_users.py` (committed no git) | 1 hora (rotacionar + env vars) |
| H12 | E | Sem Boleto/PIX (Stripe suporta, mas não ativado) | 2 dias |

### MEDIUM (18)

| # | Track | Issue |
|---|-------|-------|
| M1 | B | Signup tem campo telefone (fricção desnecessária) |
| M2 | B | Onboarding exige CNAE (nem todo empresário sabe) |
| M3 | B | Default de busca é "Todo o Brasil" (maximiza tempo de espera) |
| M4 | B | "87% de editais descartados" pode ser lido como negativo |
| M5 | B | Título do pricing "Escolha Seu Nível de Compromisso" soa pesado |
| M6 | B | Ícones emoji no dashboard inconsistentes entre plataformas |
| M7 | B | Banner motivacional "só mais um instante!" após 84 segundos é desonesto |
| M8 | B | "Personalizar busca" colapsado esconde filtros importantes |
| M9 | C | OpenAPI snapshot stale (1 teste falhando) |
| M10 | C | 326 erros ruff lint (253 auto-fixáveis) |
| M11 | C | cryptography CVE (atualizar para 46.0.5) |
| M12 | C | 2 vulnerabilidades npm (ajv + minimatch — build-time only) |
| M13 | D | FK violation no cache warming (WARMING_USER_ID não existe em profiles) |
| M14 | D | `/api/health/cache` retorna 404 no frontend (sem proxy route) |
| M15 | D | Prometheus metrics geradas mas sem scraper conectado |
| M16 | E | `/sobre` linkado no footer é 404 |
| M17 | E | Política de privacidade menciona "Mercado Pago" (não implementado) |
| M18 | F | CSP usa `unsafe-inline` e `unsafe-eval` (padrão Next.js) |

### LOW (11)

Footer "LGPD Compliant" em inglês, magic link redireciona para /planos, "Pular por agora" duplicado no onboarding, título do login assume usuário recorrente, links de conteúdo no footer possivelmente 404, 7 TODOs no código, 30 issues tech debt abertas, Jest worker leak warning, co-occurrence triggers mortos, HEAD /health retorna 405, ComprasGov health check aceita 404 como saudável.

---

## COMPETITIVE LANDSCAPE (Track A)

### Principais Concorrentes

| Plataforma | Preço | Clientes | AI? | Diferencial |
|-----------|-------|----------|-----|-------------|
| **ConLicitação** | ~R$149/mês | 16.000-20.000+ | Sim (Dr. Licita) | Maior base, 6.000+ fontes |
| **Siga Pregão** | R$397/mês | 2.700+ avaliações | Sim | 4.9★ no B2B Stack, robô de lance |
| **Effecti** | Não público | 1.000+ | Sim | 1.400 portais, propostas automáticas |
| **Licitei** | R$101-393/mês | N/A | Sim ("Pergunte ao Edital") | IA Q&A sobre editais |
| **LicitaIA** | R$67-247/mês | N/A | Core | IA nativa, via Hotmart |
| **Alerta Licitação** | R$45/mês | N/A | Não | Mais barato, app mobile |
| **SmartLic** | **R$1.999/mês** | **0 (pré-revenue)** | Sim (GPT-4.1-nano) | Viabilidade 4 fatores, multi-fonte |

### Posicionamento de Preço

```
R$45 ←——— R$149 ———→ R$397 ————————————————→ R$1.999
Alerta    ConLicit.   Siga Pregão              SmartLic
(alertas) (busca+doc) (busca+robô+IA)         (busca+IA)
```

**SmartLic cobra 5-13x mais que o mercado com MENOS features que competidores na faixa R$149-397.**

### Features Table-Stakes Ausentes

1. **Alertas por email/WhatsApp** — todo competidor desde R$45/mês tem
2. **Robô de lance automático** — Siga Pregão, Effecti, Licitei, Lance Fácil
3. **Geração automática de propostas** — Effecti, LicitaIA, eLicitação
4. **Gestão documental** (certidões, habilitação) — ConLicitação, Licitei
5. **Download de editais** — expectativa básica

### Diferenciadores Reais do SmartLic

1. **Agregação multi-fonte com dedup** — genuinamente único
2. **Classificação IA setorial automática** — melhor que keyword search
3. **Análise de viabilidade 4 fatores** — ninguém mais oferece
4. **Resumo executivo com IA** — diferenciador forte

---

## TECHNICAL HEALTH (Track C)

| Métrica | Resultado | Baseline | Veredicto |
|---------|-----------|----------|-----------|
| Backend tests | 5.549 pass / 1 fail / 5 skip | 5.419 / 0 / 5 | OK (1 fail = snapshot stale) |
| Frontend tests | 3.473 pass / 0 fail | 2.681 / 0 | EXCELENTE (+792) |
| TypeScript | 0 erros | 0 | OK |
| TODO/FIXME | 7 total (0 críticos) | — | OK |
| GitHub issues | 30 open (todos tech debt) | — | OK |
| CVEs produção | 3 HIGH (starlette, python-multipart, cryptography) | — | Precisa atualizar |
| CodeQL | PASS | — | OK |

---

## INFRASTRUCTURE (Track D)

| Endpoint | Status | Latência |
|----------|--------|----------|
| smartlic.tech (landing) | 200 | 0.93s |
| /api/health | 200 | 1.07s |
| PNCP API | 200 | 0.99s |
| PCP v2 API | 200 | 0.53s |

**Timeout chain:** Pipeline(110s) > Consolidation(100s) > PerSource(80s) > PerUF(30s) — **sólido**
**Monitoramento:** UptimeRobot + Sentry ativos. Prometheus sem scraper.
**Score:** 8/10

---

## SECURITY (Track F)

| Categoria | Score |
|-----------|-------|
| Auth & Authorization | 9/10 |
| API Security | 9/10 |
| Secrets Management | 7/10 (senhas em seed_users.py) |
| LGPD Compliance | 9/10 |
| Payment Security | 10/10 |
| Error Handling | 9/10 |
| Infrastructure Security | 9/10 |
| **Overall** | **8.9/10** |

---

## RECOMMENDED GTM STRATEGY

### Opção Recomendada: "Beta Privado com Convite"

Em vez de GTM aberto a R$1.999/mês (que vai gerar zero conversões), lançar em modo **beta privado**:

#### Semana 1 (Dias 1-3): Fixes Críticos
- [ ] Fix barra de progresso (B2) — refletir progresso real por UF
- [ ] Consolidar mensagens de erro (B3) — uma mensagem, um botão azul
- [ ] Corrigir Termos de Serviço (H2) — remover planos fantasma
- [ ] Rotacionar senhas hardcoded (H11)
- [ ] Fix PNCP health canary (H9) + stale env var (H10)
- [ ] Atualizar starlette + python-multipart (H8)

#### Semana 1 (Dias 3-7): Ajustes Estratégicos
- [ ] **Decisão de pricing** (B1): Opções:
  1. **Beta gratuito** com cap de 50 buscas/mês → coletar feedback → definir preço
  2. **R$497/mês** (Essencial) + **R$1.999/mês** (Pro) → tier de entrada
  3. **R$1.999/mês mantido** mas com 30 dias grátis (não 7) → mais tempo para provar valor
- [ ] Default de busca para UFs do onboarding (H5) — reduz tempo de espera
- [ ] Botão retry em azul (H7) — 2 horas de fix
- [ ] Explicação nos estados "Indisponível" (H6)

#### Semana 2: Social Proof + Alertas
- [ ] Coletar 3-5 depoimentos de beta users (H1)
- [ ] Implementar alertas email diários (B4) — feature table-stakes
- [ ] Criar página /sobre (M16)
- [ ] Remover Mercado Pago da privacidade (M17)

#### Semana 3: GTM Aberto
- [ ] Ativar aquisição paga (Google Ads, LinkedIn)
- [ ] Landing page com social proof
- [ ] Pricing validado com 10-20 early adopters

### Critérios de Saída para GTM Aberto
- [ ] 10+ buscas consecutivas sem falha visível ao usuário
- [ ] 5+ depoimentos reais na landing page
- [ ] Taxa de conversão trial→paid > 5% nos primeiros 20 trials
- [ ] NPS > 30 dos early adopters
- [ ] Alerta email funcional (diário/semanal)

---

## SCORES POR TRACK

| Track | Área | Score | Veredicto |
|-------|------|-------|-----------|
| A | Market Intelligence | 4/10 | Pricing desalinhado com mercado |
| B | Production UX | 5/10 | Landing excelente, core flow problemático |
| C | Technical Health | 8/10 | Testes sólidos, CVEs para atualizar |
| D | Infrastructure | 8/10 | Estável, monitoramento parcial |
| E | Business Model | 6/10 | VP forte, pricing/social proof fracos |
| F | Security | 9/10 | Sólido, 1 fix obrigatório |
| **CONSOLIDADO** | | **6.7/10** | **CONDITIONAL-GO** |

---

## FONTES

- Siga Pregão (sigapregao.com.br)
- ConLicitação (conlicitacao.com.br/planos)
- Effecti (effecti.com.br)
- Licitei (licitei.com.br/planos)
- LicitaIA (licitaia.app)
- Alerta Licitação (alertalicitacao.com.br)
- B2B Stack - Tender Management (b2bstack.com.br)
- PNCP Compras Governamentais R$1T+ (convergenciadigital.com.br)
- Decreto 12.807/2025 (elicitacao.com.br)

---

*Report generated by GTM Validation Squad (squad-gtm-validation-final)*
*6 parallel tracks × ~10 minutes each = ~1 hour total investigation*
