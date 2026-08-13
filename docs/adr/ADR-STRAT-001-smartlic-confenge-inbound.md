# ADR-STRAT-001: SmartLic é o braço público de inbound da CONFENGE

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-13 |
| Authors | @architect, @pm |
| Stakeholders | @po, @devops, @qa |
| Issue | [#1262](https://github.com/tjsasakifln/SmartLic/issues/1262) |
| Supersedes | MRR/SaaS as product north star; `docs/strategy/kill-criteria.md` (MRR R$3.000) as current strategy |
| Superseded by | — |
| Companion of | #2111 (SaaS sunset), #2113 (SEO), [extra-cli#354](https://github.com/tjsasakifln/extra-cli/issues/354) (`public_read_v1`), #2108 (consumer) |

## Context

O repositório e o backlog comunicavam duas estratégias incompatíveis:

1. **SaaS independente** — trial, Stripe, 9 planos, quotas, workspace privado, DataLake e crawler próprios, Railway + Supabase como autoridade.
2. **Ativo público da CONFENGE** — páginas e ferramentas indexáveis que transformam dados públicos canônicos em descoberta verificável e conduzem demanda qualificada à consultoria.

Essa ambiguidade gerava retrabalho, dois DataLakes, billing sem tese comercial e pSEO disputando prioridade com o caminho crítico. O `extra-cli` já é o PostgreSQL/truth plane na Netcup ([extra-cli#354](https://github.com/tjsasakifln/extra-cli/issues/354)). O SmartLic já possui patrimônio orgânico (CNPJ, órgãos, municípios, contratos, licitações, observatório) documentado no GSC versionado.

A decisão de produto não é mais "monetizar assinatura". É **gerar demanda consultiva para a CONFENGE** sem destruir o que já está indexado.

## Decision

O SmartLic deixa de ser um SaaS independente. A arquitetura estratégica autoritativa é:

```
extra-cli  = truth / data plane canônico
SmartLic   = public discovery / intelligence / inbound plane
CONFENGE   = conversion / service plane
Warmbly    = action / outreach plane separado (NÃO bloqueia go-live)
```

### Fronteiras obrigatórias

| Plano | Responsável por | Proibido de |
|-------|-----------------|-------------|
| **extra-cli** | Aquisição, crawling, DataLake, identidade canônica, provenance, freshness, deduplicação, fatos públicos, contrato de leitura versionado (`public_read_v1`) | UI pública, SEO, CTA, billing |
| **SmartLic** | Experiência pública, páginas indexáveis, inteligência baseada em dados, apresentação, descoberta, SEO, pSEO controlado, ferramentas públicas, contexto, CTA, aquisição inbound | Ser autoridade de dados; vender assinatura; crawler próprio como fonte da verdade |
| **CONFENGE** | Serviço, diagnóstico, análise, consultoria, conversão comercial, relacionamento com lead | Operar o DataLake ou o site público |
| **Warmbly** | Action/outreach posterior, consumidor eventual de handoff | Ser requisito de go-live do SmartLic |

### O que o SmartLic NÃO é mais (direção estratégica)

- venda de assinatura, trial, billing, Stripe, quotas comerciais;
- DataLake concorrente ou crawling próprio como autoridade;
- login obrigatório para conteúdo público;
- expansão de SaaS ou features privadas multi-tenant sem evidência comercial;
- segundo CRM, Kafka, Kubernetes ou microservices sem necessidade demonstrável.

### Destino explícito dos componentes de runtime

Justificativa exigida para manter. Ausência de justificativa implica remoção na onda correspondente.

| Componente | Destino | Justificativa atual | Issue |
|------------|---------|---------------------|-------|
| **FastAPI** | KEEP + ADAPT — adapter de apresentação até o cutover | 187 endpoints e SSR/ISR dependem dele; reescrever agora é retrabalho | #2108, #2115 |
| **Next.js** | KEEP + PRIORITIZE — superfície pública | Patrimônio SEO e ferramentas públicas | #2112, #2113 |
| **Redis** | KEEP + ADAPT na transição; reavaliar no runtime mínimo | Cache, rate-limit, locks; não é truth plane | #2115, #2116 |
| **ARQ / workers** | SUNSET AFTER DEPENDENCY para ingestão/billing; não criar jobs novos de crawler | Ingestão passa ao extra-cli; jobs SaaS saem com #2111 | #2108, #2111 |
| **Supabase** | REPLACE como autoridade; KEEP + ADAPT como store transicional | Nunca migrar o DataLake legado para a Netcup; nunca manter segunda autoridade | #2108 |
| **Stripe** | SUNSET em ondas | Premissa comercial morta | #2111 |
| **Railway** | REPLACE pelo runtime mínimo na Netcup | Custo e acoplamento legado | #2115 |
| **Warmbly** | DEFER | Não bloqueia go-live | — |

### Caminho crítico autoritativo (ordem estrita)

1. **#1262** — esta decisão e freeze estratégico.
2. **#2111** — congelar/retirar SaaS, Stripe, billing, trial e quotas sem perder ativos públicos.
3. **#2113** — preservar patrimônio SEO e migrar URLs sem perda de indexação.
4. **extra-cli#354** — disponibilizar `public_read_v1`.
5. **#2108** — consumir `public_read_v1` e aposentar DataLake/crawling SmartLic.
6. **#2112** — relançar public intelligence MVP.
7. **#2116** — isolamento/performance (tráfego público não degrada o truth plane).
8. **#2115** — runtime mínimo na Netcup.
9. **#2114** — marca SmartLic ↔ CONFENGE e jornada consultiva.
10. **#2117** — attribution e handoff mínimo.
11. **Go-live público** somente com os gates aplicáveis verdes.

Trabalhos independentes só em paralelo quando não criam acoplamento, retrabalho ou violação dessa sequência. Nenhuma issue P1/P2 disputa recursos com esse caminho.

### Critério econômico de priorização

1. Reduzir tempo até geração de demanda qualificada para a CONFENGE.
2. Preservar ativos já existentes.
3. Eliminar duplicação operacional.
4. Reduzir dependência de infraestrutura legada.
5. Reduzir babysitting humano.
6. Aumentar qualidade e confiabilidade da inteligência pública.
7. Melhorar aquisição orgânica.
8. Melhorar conversão.
9. Somente depois expandir funcionalidades.

### Classificação obrigatória de capabilities

Toda capability relevante deve estar em exatamente uma categoria:

- `KEEP + PRIORITIZE`
- `KEEP + ADAPT`
- `SUNSET`
- `REPLACE`
- `DEFER`

Inventário vigente: [`docs/strategy/capability-disposition-1262.md`](../strategy/capability-disposition-1262.md).

## Consequences

### Positivas

- Uma única direção operacionalmente executável.
- Backlog deixa de otimizar MRR/trial.
- extra-cli é reconhecido como única autoridade de fatos públicos.
- Warmbly não atrasa o relançamento.
- Patrimônio SEO entra no caminho crítico em vez de ser tratado como later.

### Negativas / custos

- Código SaaS permanece até as ondas de #2111 — a decisão não apaga billing no mesmo PR.
- Documentos históricos (PRD corpo, CASE STUDY, ADRs de billing) descrevem o legado; passam a carregar aviso de supersessão.
- Agentes e contribuidores precisam ler este ADR antes de criar issues ou features.

### Enforcement

- `scripts/check_strategic_positioning.py` falha se README, `llms.txt`, cabeçalhos de PRD/ROADMAP ou este ADR voltarem a definir SmartLic como SaaS independente.
- Issue templates exigem alinhamento a este ADR e proíbem billing/DataLake/crawler próprios em P0/P1.
- Labels `roadmap:now` / `roadmap:next` / `roadmap:later` só descrevem o caminho crítico vigente.

## Alternatives Considered

### A — Manter SaaS + inbound em paralelo

Rejeitada. Duas teses competem por runtime, copy, SEO e operação. Evidência: 318 arquivos Stripe e 1.106 menções billing/trial/quota sem receita que justifique o custo.

### B — Desligar SmartLic e publicar tudo em confenge.com.br

Rejeitada. Destruiria patrimônio orgânico (10k+ URLs, GSC com consultas de CNPJ/contratos/licitações 2026) e atrasaria demanda. A marca SmartLic permanece como ativo público da CONFENGE.

### C — Migrar o DataLake legado do SmartLic para a Netcup e continuar crawler próprio

Rejeitada. Cria segundo DataLake e perpetua autoridade duplicada. extra-cli já é o truth plane.

### D — Acoplar go-live ao Warmbly / CRM / outreach

Rejeitada. Action plane é posterior. Handoff mínimo (#2117) basta para conversão inicial.

## Rollback

Reverter este ADR exigiria nova decisão explícita (status `Superseded`) e um PR que reescreva README/PRD/ROADMAP/`llms.txt`. Não há rollback implícito por inércia de código SaaS residual.

## References

- Issue #1262 e sub-issues #2111, #2114.
- Caminho crítico: [`docs/strategy/critical-path.md`](../strategy/critical-path.md).
- Runtime: [`docs/strategy/runtime-destination.md`](../strategy/runtime-destination.md).
- Revisão de backlog: [`docs/strategy/backlog-review-1262.md`](../strategy/backlog-review-1262.md).
- Producer: [tjsasakifln/extra-cli#354](https://github.com/tjsasakifln/extra-cli/issues/354), #289, #273.
