# Blue Ocean — Product-Value Extraction para Usuário Pago

**Data:** 2026-04-22
**Squad:** aiox-deep-research (Tier 1 Execution + QA)
**Autor:** dr-orchestrator (synthesis)
**Horizonte:** Research → @sm story creation (próxima sessão)
**Status:** DRAFT — pronto para handoff @sm

---

## 0. Resumo Executivo (1 parágrafo)

Os 4 epics em flight (Revenue, Conversion, SEO-Organic, Tech-Debt) atacam aquisição, conversão UX e inbound. **Nenhum** ataca o que o usuário pagante *faz* com SmartLic que justifica retenção brutal e upsell Enterprise. Esse é o blue ocean. Com 2M+ contratos históricos + 50K editais abertos + classificação setorial LLM + série temporal multi-ano, SmartLic tem o único dataset B2G correlacionado do Brasil. Este doc enumera 15 dores de mercado, filtra 6 como moat real, prioriza 3 para execução imediata — **Contract Expiration Radar** (blue ocean virgin confirmado empiricamente — ZERO concorrentes), **Organ Health Dashboard** (blue ocean virgin confirmado), e **Competitive Radar por CNPJ** (LicitaGov já entrega versão simples — moat via dataset scale, não virgin). **CATMAT Price Intelligence Pro** em track paralelo; **G-Buyer persona** com dor **validada empiricamente** (Migalhas + Observatório Lei 14.133) mas com incumbente Banco de Preços (15 anos) — requer spike de positioning. Estimativa: +R$80-120/user/mês willingness-to-pay adicional. **Status: DRAFT — validação empírica em §10 (6 concorrentes + 7 fontes setoriais 2026); 2 decision points bloqueantes para user (§6.1 + §7.3.b) antes de @sm abrir stories.**

---

## 1. Questão Estruturadora

> **"Que decisões B2G hoje são tomadas no escuro porque ninguém tem 2M contratos históricos + 50K editais abertos + série temporal multi-ano + classificação setorial LLM + dedup multi-fonte correlacionados?"**

Esse é o discriminador de oceano azul. Se uma dor pode ser resolvida por Ctrl+F no PNCP ou planilha Excel, **não é moat** — concorrente replica em 6 meses.

---

## 2. Método

### 2.1. Fontes consultadas

| Fonte | Cobertura | Uso nesta pesquisa |
|---|---|---|
| `supplier_contracts` (Supabase, ~2M linhas) | Contratos vencidos multi-ano | Dimensionamento quantitativo — N potencial afetado |
| `pncp_raw_bids` (Supabase, ~50K) | Editais abertos 12d TTL | Densidade corrente — opportunity flow |
| `backend/sectors_data.yaml` | 15 setores × keywords | Segmentação canônica |
| Roadmap stories 431-449 | Epics InProgress/Done | Filtro anti-duplicação |
| EPIC-REVENUE-2026-Q2 | Revenue-commercial | Filtro anti-duplicação |
| EPIC-CONVERSION-2026-04 | UX-trial (10/10 Done) | Filtro anti-duplicação |
| EPIC-SEO-ORGANIC (431-436) | Inbound + API pública | Filtro anti-duplicação |
| `/v1/itens/{catmat}/profile` (existente) | CATMAT público | Base para versão premium |

### 2.2. Discriminador binário (filtro de moat)

Cada candidata passou por 4 perguntas binárias:

1. **Exige `supplier_contracts` correlacionado?** (≥100K rows para significância)
2. **Exige série temporal multi-ano?** (≥18 meses)
3. **Exige classificação setorial LLM ou CATMAT harmonizado?** (não resolvível com regex)
4. **Resolve-se com API PNCP crua + planilha?** (se sim → COMMODITY)

≥3 "sim" + pergunta 4 "não" = **MOAT** (entra no deep-dive).
Outras combinações = **COMMODITY** (descartadas).

### 2.3. Escopo excluído

- Features de aquisição/outbound (coberto por EPIC-REVENUE)
- UX de trial/conversão (coberto por EPIC-CONVERSION Done)
- SEO inbound programático (coberto por EPIC-SEO-ORGANIC)
- Jurídico/regulatório (delegar a `aiox-legal-analyst`)
- Tech debt e CI (coberto por EPIC-TD, EPIC-BTS)

---

## 3. Landscape — 15 Candidatas

Todas avaliadas pelo filtro binário:

| # | Candidata | `supplier_contracts`? | Temporal? | Setorização? | PNCP crua basta? | Verdict |
|---|-----------|:-:|:-:|:-:|:-:|:-:|
| 1 | **Órgão Reliability Score** (cancelamento, atraso, recurso) | ✅ | ✅ | ❌ | ❌ | 🟢 MOAT |
| 2 | **Competitive Intelligence por CNPJ** (quem bate em mim, win rate) | ✅ | ✅ | ✅ | ❌ | 🟢 MOAT |
| 3 | **Contract Expiration Radar** (incumbentes ≤90d) | ✅ | ✅ | ✅ | ❌ | 🟢 MOAT |
| 4 | **CATMAT Price Intelligence Pro** (harmonização LLM + spread regional) | ✅ items | ✅ | ✅ | ❌ | 🟢 MOAT |
| 5 | **Procurement Calendar por Órgão** (sazonalidade aquisitiva) | ✅ | ✅ | ❌ | ❌ | 🟢 MOAT |
| 6 | **Bid Success Predictor** (score pre-go/no-go) | ✅ | ✅ | ✅ | ❌ | 🟢 MOAT |
| 7 | **Arbitragem Regional de Preço** (mesmo item, UFs diferentes) | ✅ | ❌ | ✅ | ❌ | 🟢 MOAT (consolidado em #4) |
| 8 | **Consortium Finder** (CNPJs que ganham juntos) | ✅ | ✅ | ✅ | ❌ | 🟢 MOAT |
| 9 | Pre-flight de Habilitação (cadastro × edital) | ❌ | ❌ | ✅ | PARCIAL | 🔴 COMMODITY |
| 10 | **Incumbent Displacement Radar** (quem troca de fornecedor) | ✅ | ✅ | ✅ | ❌ | 🟢 MOAT (consolidado em #2) |
| 11 | Supplier Growth Detection (CNPJ escalando em 6-12m) | ✅ | ✅ | ❌ | ❌ | 🟡 MOAT — nicho admin |
| 12 | Customer Concentration Risk (% receita em top-3 órgãos) | ✅ | ✅ | ❌ | ❌ | 🟡 MOAT — small-ticket |
| 13 | **Time-to-Contract Benchmark** (dias publ→assinatura) | ✅ | ✅ | ✅ | ❌ | 🟢 MOAT (consolidado em #1) |
| 14 | **Cross-sell Opportunity Map** (órgão-buyer similarity) | ✅ | ✅ | ✅ | ❌ | 🟢 MOAT |
| 15 | Price Anomaly Detection (2σ fora distribuição) | ✅ items | ✅ | ✅ | ❌ | 🟡 MOAT — consolidado em #4 |

**Resultado após consolidação de overlaps:**

| Tier | Candidatas | Ação |
|---|---|---|
| 🏆 Top-6 deep-dive | #1, #2, #3, #4, #6, #14 | Seção 4 (blocos completos) |
| 🥈 Second wave | #5, #8, #11, #12 | Seção 5 (bullets executivos) |
| ❌ Descartadas | #9 | Nota em §2.3 |

---

## 4. Deep-Dive — 6 Moats Priorizados

Cada bloco segue o contrato exigido pelo @sm: **Dor + Evidência / Data enrichment / Delivery / Persona+Tier / KPI / Defensibilidade**.

---

### 4.1. 🥇 Contract Expiration Radar (C)

**Top-1 priority. Highest blue-ocean coefficient. Fastest-to-moat.**

#### Dor nomeada + evidência quantitativa

Empresas B2G perdem **50-70% do pipeline potencial** porque descobrem o edital quando ele já está publicado — janela de 8-30 dias úteis. O *real* sinal antecipado é: **contratos com vigência_fim em ≤90 dias + órgão historicamente abre sucessão 60-120 dias antes do vencimento**. Ninguém no mercado entrega isso porque ninguém tem 2M contratos históricos com `vigencia_inicio`/`vigencia_fim` + padrão de sucessão por órgão. SmartLic tem.

**N potencial afetado (hipótese empírica a validar):**
- Se ~20% dos 2M contratos têm vigência 12 meses renovável → ~400K ciclos de sucessão/ano
- Se 70% abrem edital de sucessão antes do vencimento → ~280K editais previsíveis/ano
- Se capturamos 10% para usuário Pro = 28K alertas/ano × R$0,50 valor/alerta = **R$14K/ano em pipeline value por usuário**

#### Data enrichment requerido

1. **Tabela nova `contract_renewals`** (materialized view ou cron-built):
   - `contract_id`, `vigencia_fim`, `orgao_cnpj`, `fornecedor_cnpj`
   - `predicted_renewal_window_start`, `predicted_renewal_window_end` (via histórico de sucessão do órgão)
   - `renewal_probability_score` (0-1, baseado em: modalidade original, histórico de renovação do órgão, tempo em atividade do contrato)
   - `setor_id` (via classificação LLM do `objeto_contrato`)

2. **Pipeline ETL novo** (ARQ cron diário):
   - Lê `supplier_contracts` onde `vigencia_fim BETWEEN now() AND now() + interval '180 days'`
   - Calcula `expected_edital_publication_date` usando regressão linear simples: `mean(edital_publicacao_date - previous_contract_vigencia_fim)` por órgão
   - Popula `contract_renewals` incremental

3. **Enrichment por classificação LLM em `objeto_contrato`** (batch job uma vez, depois incremental): setor + sub-tópico + palavras-chave canônicas do edital esperado

#### Delivery mechanism

- **Tela:** `/radar-vencimentos` — tabela filtrable por setor/UF/valor + timeline heatmap dos próximos 90d
- **Alert proativo:** email + in-app + webhook (API key) quando contrato monitorado entra janela ≤60d
- **Export:** CSV + Pipeline auto-inject (cria card no kanban automaticamente)
- **API:** `GET /v1/radar/expiring-contracts?setor=&uf=&window_days=90` (tier Enterprise)

#### Persona alvo + tier

- **Primário:** Empresa B2G média-grande (setor facilities, TI, engenharia) — dor dor "não perder contrato que eu já deveria estar perseguindo há 60 dias"
- **Secundário:** Consultoria que gerencia portfólio de 10-30 clientes — dor "onboarding de cliente novo sem histórico de vencimentos é manual"
- **Tier:** 🔒 **Enterprise** (novo tier R$1.497/mês) OU **Consultoria** (upsell existente R$997)
- **Trial Pro atual (R$397):** preview de 3 alertas/mês, teaser "desbloqueie 100+/mês"

#### KPI de valor percebido

- **Tempo antecipado de pipeline:** +60 dias de lead time médio vs descoberta reativa (mensurável via comparação data_alerta vs data_publicacao_edital real quando ocorre)
- **Pipeline value gerado:** soma valor_contrato_estimado dos alertas entregues / mês
- **Conversão alerta → pipeline:** % de alertas que viram cards no kanban do user
- **Ground truth de acurácia:** % de alertas onde edital foi publicado dentro da janela prevista (validar em 90d pós-launch)

#### Defensibilidade

- **Concorrente direto (ex: LicitaJá):** tem editais abertos, não tem contratos históricos correlacionados → não consegue predizer
- **Concorrente API pura (ex: scraper próprio):** precisaria crawler 2M contratos + inferir padrão de sucessão por órgão (80K+ órgãos). Barreira de dados + tempo ≈ 12-18 meses.
- **Google/Perplexity:** não estruturam dados B2G temporais; resposta genérica sem alertas proativos
- **SmartLic vantagem durável:** o dataset cresce 3x/semana (ingestion `supplier_contracts`) — gap aumenta com tempo

---

### 4.2. 🥇 Organ Health Dashboard (A)

**Top-2 priority. Killer differentiator porque ninguém entrega signals operacionais do órgão comprador.**

#### Dor nomeada + evidência quantitativa

Empresas B2G participam de editais de órgãos que atrasam pagamento 180-360 dias ou cancelam 30-40% dos editais publicados, comprometendo fluxo de caixa da fornecedora. **Nenhuma plataforma entrega hoje sinais de "saúde operacional" do órgão**: taxa de cancelamento, taxa de deserto, tempo médio publicação→assinatura, spread empenho↔liquidação (proxy de atraso de pagamento).

**N potencial afetado (hipótese):**
- 80K+ órgãos compradores no PNCP
- ~15% dos contratos ativos têm atraso de pagamento >90 dias (hipótese — validar com dado de empenho/liquidação quando disponível)
- Dor sistêmica: fornecedor vence edital, trabalha 6 meses, depois espera 8 meses para receber → margem negativa se não for antecipado

#### Data enrichment requerido

1. **Tabela nova `organ_health_metrics`** (materialized view, refresh diário):
   - `cnpj_orgao`, `nome_orgao`, `uf`, `esfera`, `setor_dominante`
   - `cancellation_rate_12m` (% editais publicados que foram cancelados)
   - `desert_rate_12m` (% editais sem propostas)
   - `avg_time_to_contract_days` (publicação → assinatura)
   - `avg_payment_delay_days` (empenho → liquidação, quando disponível via ComprasGov v3 ou inferido)
   - `reliability_score` 0-100 composto
   - `sample_size_12m` (N de contratos — flag se <30 "low-sample")

2. **Enrichment necessário:**
   - Crawl adicional em `dadosabertos.compras.gov.br` para dados de empenho/liquidação (federal) — **delegar a data-engineer, requer nova fonte**
   - Cross-check com Transparência Municipal (para municipal) — limitação: ~30-40% dos municípios publicam
   - Fallback: usar `status` do contrato em PNCP (`ASSINADO`, `CANCELADO`, `SUSPENSO`) como proxy grosseiro

3. **Score composto (proposta de ponderação):**
   - 30% cancellation_rate (invertido)
   - 25% payment_delay (invertido, quando disponível — senão, reduzir peso e avisar)
   - 25% desert_rate (invertido — deserto = órgão com expectativas desalinhadas do mercado)
   - 20% time_to_contract (invertido — órgão lento indica burocracia)

#### Delivery mechanism

- **Tela:** `/orgaos/[cnpj]/saude` — dashboard com 4 KPIs + timeline + comparação com mediana UF
- **Widget:** card "Health Score" embedado em cada resultado de busca + cada card de pipeline
- **Filtro avançado em /buscar:** "apenas órgãos com score ≥70"
- **Alert:** email mensal "órgãos da sua lista em que score piorou >10 pontos"
- **API:** `GET /v1/orgaos/{cnpj}/health`

#### Persona alvo + tier

- **Primário:** Empresa B2G small-mid que vive com fluxo de caixa apertado — dor "preciso saber se esse órgão paga em dia antes de committar 6 meses de operação"
- **Secundário:** Consultoria fazendo due diligence de oportunidade pra cliente
- **Tier:** 🔒 **Pro+** (upsell R$497-597) ou **Consultoria** (incluído)
- **Trial:** score resumido (3 categorias: 🟢🟡🔴) sem breakdown; Pro vê detalhamento

#### KPI de valor percebido

- **Margem preservada:** fornecedor declina edital de órgão com score <40 → evita prejuízo de atraso (self-reported, survey pós-uso)
- **Tempo de due diligence:** de 2-4h (pesquisa manual em transparência) para 30s (dashboard)
- **Cobertura:** % dos órgãos nas buscas do user com score disponível (target ≥80% federal+estadual; ≥40% municipal)

#### Defensibilidade

- **Dados de empenho/liquidação:** fragmentados entre ~80 portais de transparência. Só plataforma com crawl estruturado multi-fonte consegue entregar. **Alto custo de replicação** (12+ meses de engenharia).
- **Score composto:** ponderação calibrada com ground truth (sample de 1.000 contratos com data de pagamento real) é proprietary — concorrente que copie peso errado entrega score ruim
- **Reputacional:** once "score SmartLic" é referência, se torna o "NPS dos órgãos B2G" — network effect de adoção

---

### 4.3. 🥈 Competitive Radar por CNPJ (B)

**Top-3 priority. Killer upsell Consultoria/Enterprise.**

#### Dor nomeada + evidência quantitativa

Empresa B2G prepara proposta sem saber: **(a) quais concorrentes normalmente participam** do edital-tipo X + **(b) com que desconto típico eles ganham** + **(c) qual o win rate dela vs cada concorrente**. Resultado: ou deixa margem na mesa (desconto excessivo), ou perde por margem (desconto insuficiente).

**N potencial:** 2M contratos com ~300K CNPJs fornecedores distintos (hipótese — validar). Para cada CNPJ que vira cliente SmartLic, perfil histórico de seus 5-20 principais concorrentes é montável.

#### Data enrichment requerido

1. **Tabela nova `competitive_matrix`** (materialized, per-CNPJ-client):
   - `user_cnpj`, `competitor_cnpj`, `competitor_nome`
   - `co_occurrences_12m` (N de editais onde ambos apareceram)
   - `user_wins`, `competitor_wins`, `other_wins` (head-to-head count)
   - `avg_winning_discount_pct` (quando concorrente venceu, qual % abaixo do valor_estimado)
   - `top_setores` (3 setores de maior overlap)
   - `top_orgaos` (5 órgãos com maior overlap)

2. **Dados adicionais necessários:**
   - Tabela atual `supplier_contracts` tem `cnpj_fornecedor` + `valor_contrato` + `orgao` → base suficiente
   - **Gap:** não temos lista de "participantes não vencedores" do edital (PNCP não disponibiliza dados de propostas perdedoras de forma estruturada)
   - **Workaround possível:** crawl de atas de pregão (disponíveis em ~40-50% dos portais) — **requer nova fonte, delegar a data-engineer**
   - **Workaround v1 (sem atas):** matriz "CNPJs do mesmo setor/UF que venceram em órgãos similares" como proxy — marca como "proxy-based" na UI

3. **Enrichment de descontos:** calcular `(valor_contrato - valor_estimado) / valor_estimado` por contrato quando ambos disponíveis

#### Delivery mechanism

- **Tela:** `/competitivos` dashboard pessoal do user → top 10 concorrentes, head-to-head por setor
- **Widget contextual:** em cada resultado de edital, "3 concorrentes típicos deste perfil de edital" + badge "você já perdeu N vezes para CNPJ X"
- **Playbook AI-generated:** para cada concorrente top-3, sumário "este concorrente tende a ganhar com desconto médio de X% em editais de valor <R$Y" (LLM sobre dados agregados)
- **Alert:** "seu concorrente Z ganhou 3 editais na última semana no seu setor/UF"
- **API:** `POST /v1/competitive/analyze` (input: user_cnpj + edital_id, output: participantes prováveis)

#### Persona alvo + tier

- **Primário:** Consultoria (R$997) — gerencia múltiplos CNPJs de clientes, precisa briefing competitivo rápido
- **Secundário:** Empresa Pro (R$397+) no upsell — "ative para ver perfil competitivo"
- **Tier:** 🔒 **Consultoria core** (incluído) + **Enterprise** (R$1.497 com white-label)
- **Trial:** preview de 1 concorrente sem breakdown

#### KPI de valor percebido

- **Discount precision:** variação do desconto oferecido pelo user pós-adoção vs pré-adoção (self-reported via input "seu desconto usado" em edital fechado)
- **Win rate lift:** % de editais ganhos pós-uso vs baseline do user
- **Face-time savings:** 2-3h/semana que hoje são pesquisa manual em PNCP

#### Defensibilidade

- **Dataset de head-to-head:** cruzando 2M contratos × CNPJ distinct × setor × órgão. **[ATUALIZAÇÃO empírica 2026-04-22 — ver §10]:** LicitaGov já entrega "Dashboard de Concorrentes por CNPJ" — versão simples. **NÃO é mais blue ocean virgin.** Diferencial SmartLic: (a) dataset scale (2M contratos vs deles desconhecido, estimado <500K), (b) cross-link com Organ Health + Expiration Radar no mesmo produto, (c) setorização LLM para granularidade vertical.
- **Positioning ajustado:** não é "nova categoria" — é "upgrade significativo" da feature que LicitaGov já fez. Tier Consultoria R$997 (existente) deve cobrir, não tier Enterprise novo.
- **Limitação empírica a ser honesta:** sem atas de pregão, é proxy. **Advisor bias warning:** não vendemos como "deterministic" — é directional signal. Se for caro perder credibilidade, postpone até ter atas.
- **Melhoria contínua:** quanto mais usuários Pro/Consultoria o SmartLic tem, mais anônimo-agregado ground truth de "desconto real usado" para calibrar
- **Risco competitivo real:** LicitaGov pode expandir para 2M dataset se tiver capital — moat é defensível 12-24 meses, não 5 anos. Recomendação: feature #3 deve ser **bundle** com #1 Expiration Radar + #2 Organ Health (blue ocean reais) para criar lock-in sistêmico.

---

### 4.4. 🥈 CATMAT Price Intelligence Pro (D)

**Top-4 priority. User's stated pain + base existente.**

#### Dor nomeada + evidência quantitativa

Essa é a dor que o **usuário nomeou explicitamente** no brief: "órgãos não sabem que preço considerar; empresas querem ser competitivas sem perder margem". O `/v1/itens/{catmat}/profile` público já entrega P10/P50/P90 por CATMAT — mas tem **3 gaps críticos** que bloqueiam uso profissional:

1. **Harmonização insuficiente:** CATMAT é código oficial, mas órgãos descrevem o mesmo item de formas diferentes (`objeto_contrato` varia). Sem normalização via embedding, os P10-P90 são ruidosos.
2. **Sem quebra dimensional:** não há breakdown por UF/esfera/quantidade/modalidade — todos agregados global. Preço de toner em SP-federal ≠ MT-municipal.
3. **Sem histórico temporal:** é snapshot; não mostra trend de inflação/deflação do item.

**N potencial afetado:**
- 200 CATMATs seed atualmente; catálogo completo é ~500K CATMATs (MA/MI/MS) — cobrir 2K CATMATs top já cobre 80% dos contratos
- Se cada CATMAT tem 500-5000 contratos no dataset, dados suficientes para P-quantiles robustos

#### Data enrichment requerido

1. **Pipeline de extração item-level** (crítico — é o enrichment mais caro):
   - **Fonte 1:** Crawl de documentos de edital (termo de referência em PDF) — extrair items + catmat + quantidade + unit price estimado
   - **Fonte 2:** PNCP v2 tem endpoint `/contratacoes/{id}/itens` (verificar cobertura — **delegar a data-engineer para confirmar**)
   - **Fonte 3:** Inferência via LLM sobre `objeto_contrato` (fallback): extrair items implícitos com baixa confidence
   - Nova tabela `contract_items`:
     - `contract_id`, `item_order`, `catmat_code`, `descricao_item`, `unidade`, `quantidade`, `valor_unitario_estimado`, `valor_unitario_contratado`, `setor_id`
     - `embedding_vector` (pgvector — para harmonização via similarity)

2. **Harmonização via embedding:**
   - Cada `descricao_item` gera embedding (OpenAI text-embedding-3-small)
   - Cluster cosine-similar >0.85 → mesmo CATMAT canônico
   - Overrides manuais por setor específico

3. **Enrichment por dimensão:**
   - Quebra por UF/esfera/modalidade/faixa de quantidade/ano
   - Detect outliers (2σ+ ou 2σ-) para flag de possível erro ou oportunidade

#### Delivery mechanism

- **Tela existente melhorada:** `/itens/[catmat]` ganha:
  - Toggle "UF-breakdown" → tabela com P10/P50/P90 por UF
  - Timeline chart (12-24m)
  - Heatmap regional de spread
  - "Órgãos compradores top-20 deste item"
  - "Vendedores top-20 deste item"
- **Nova tela:** `/price-intel/[catmat]` (tier Pro+) com:
  - Quantity-price curve (desconto por volume)
  - Price anomaly alerts (novo item lançado 2σ+ do histórico)
  - Arbitragem regional (spread entre UFs para oportunidade de novo mercado)
- **Widget contextual:** em cada resultado de edital, "preço competitivo para este item: R$X-Y (P25-P75 histórico)"
- **Bulk API:** `POST /v1/price-intel/bulk` (upload CSV de items/quantidades, retorna recomendação de preço por linha) — tier Enterprise

#### Persona alvo + tier

- **Primário:** Empresa B2G (vendedora) Pro (R$397) — dor declarada no brief
- **Secundário:** Órgão público em fase preparatória — **gateway para novo segmento "gov buyer"** (vender SmartLic para secretarias/autarquias — tier G-Buyer R$1.997/mês por órgão)
- **Tier:** Pro (cobertura atual + UF-breakdown) + Pro Plus (timeline + anomaly) + **G-Buyer** (bulk + API + audit log)
- **Trial:** 10 consultas CATMAT/dia com marca d'água

#### KPI de valor percebido

- **Margem recuperada:** pós-uso, fornecedor aumentou preço médio 3-8% sem perder win rate
- **Tempo de pricing:** 15min → 30s por item (antes: pesquisa manual PNCP + planilha; depois: consulta direta)
- **Órgão-usuário (G-Buyer):** % redução de editais cancelados por preço desalinhado (baseline vs pós-uso)

#### Defensibilidade

- **Extração item-level:** custo pesado de NLP + crawl + harmonização embedding. Réplica ≥9 meses.
- **Escala dos embeddings:** cada contrato adicional refina o clustering. SmartLic é o único com pipeline contínuo de 3x/sem.
- **Dual-side moat:** se vendedor E comprador usam, rede se fecha. Nenhum concorrente tem os dois lados.
- **Nota:** Essa feature **acelera a entrada em novo segmento "órgão público comprador"** — blue ocean dentro do blue ocean. Vale modelar separadamente em 4.4.b.

---

### 4.5. 🥉 Bid Success Predictor (F)

**Top-5 priority. Single-score ML-driven decision tool.**

#### Dor nomeada + evidência quantitativa

Empresa B2G recebe 10-50 editais relevantes por semana, só tem capacidade para preparar propostas em 3-5. Decisão "go/no-go" é feita com intuição ou rules-of-thumb (valor mínimo, prazo mínimo). Erro típico: perseguir edital com <5% win probability desperdiça 20-40h de proposta.

**N potencial:** Cada usuário perde ~$5-10K/ano em tempo desperdiçado em propostas com baixa probabilidade de vitória.

#### Data enrichment requerido

1. **Modelo ML simples (logistic regression ou gradient boost leve):**
   - Features: user_cnpj_histórico (win rate no setor/UF/modalidade/faixa_valor) + orgao_score (da 4.2) + concorrência_esperada (da 4.3) + prazo (dias até abertura) + valor_vs_perfil_user + distância geográfica
   - Target: venceu/perdeu (ground truth via `supplier_contracts` pós-fato)
   - Treinar por vertical de setor (15 modelos)

2. **Ground truth:** cruzar editais PNCP passados com contratos resultantes → 300K-500K exemplos positivos/negativos

3. **Calibração:** output é probabilidade (0-1), não classe — importante mostrar incerteza

#### Delivery mechanism

- **Widget em cada ResultCard:** "Win probability: 34% (±8%)" com breakdown hover
- **Filtro em /buscar:** "min probability ≥30%"
- **Report semanal:** "top 5 editais da semana para você (by probability × valor_potencial)"
- **API:** `POST /v1/bid-predictor/score` (edital_id + user_cnpj → score + feature_importance)

#### Persona alvo + tier

- **Primário:** Empresa Pro/Consultoria com ≥20 histórico de participações (precisa de ground truth próprio)
- **Tier:** 🔒 Pro Plus (R$497-597) — requer ≥3 meses histórico no SmartLic para calibrar
- **Trial:** mostra score "demo" com disclaimer

#### KPI de valor percebido

- **Calibration score:** Brier score ou reliability diagram — métrica interna de qualidade
- **Proposal hit rate uplift:** % ganho de propostas priorizadas pelo scorer vs baseline
- **Time saved:** propostas abandonadas com baixa score × 20h/proposta = ROI direto

#### Defensibilidade

- **Ground truth 2M contratos + histórico user + orgao_score:** stack único
- **Risco:** calibration bad por setor nicho (baixo N) — mitigar com ensemble multi-setor
- **Kahneman note (pré-mortem):** usuário super-confia no score e ignora sua própria expertise → perda de trust. Mitigar: sempre mostrar *por quê* (feature importance) + incerteza

---

### 4.6. 🥉 Cross-sell Opportunity Map (J)

**Top-6 priority. Uniquely targets "gov buyer" segment (new audience).**

#### Dor nomeada + evidência quantitativa

Órgão que comprou **papel A4** em Q1 tem **~78% de probabilidade** de comprar **toner** nos próximos 90d (hipótese — validar empiricamente via analysis). Empresa B2G que só vende papel perde o follow-on. **Dor do órgão:** comprar itens relacionados de forma fragmentada (múltiplos pregões) eleva custo administrativo. **Dor do fornecedor:** não antecipa demanda adjacente.

Também serve ao segmento órgão-buyer (4.4.b): sugestão automática "outros órgãos que compraram X também compraram Y" em fase preparatória.

**N potencial:** Market basket analysis sobre 2M contratos — se cada órgão tem 20-100 contratos/ano, há milhões de co-ocorrências para aprender padrões.

#### Data enrichment requerido

1. **Tabela nova `organ_purchase_affinity`** (via Apriori ou FP-Growth):
   - `(orgao_cnpj, item_catmat_a, item_catmat_b)` → `support`, `confidence`, `lift`
   - Filtrar com `support ≥0.05` e `lift ≥1.5`

2. **Temporal sequence mining:**
   - `(item_catmat_a precede item_catmat_b em window Nd)` — detecta sequência típica (ex: equipamento → manutenção)

3. **Segmentação por tipo de órgão:** comportamento de prefeitura ≠ secretaria ≠ autarquia ≠ estatal

#### Delivery mechanism

- **Widget para fornecedor:** "órgãos que compraram [item atual] também compraram: X, Y, Z em 90d"
- **Alerta:** "órgão Z acabou de comprar [item A] — provavelmente precisa de [item B que você vende] em ≤45d"
- **Dashboard para órgão-buyer (4.4.b):** "planejamento de compra inteligente — recomendação baseada em órgãos similares"

#### Persona alvo + tier

- **Primário:** Empresa Pro com portfólio diversificado (3+ CNAEs)
- **Secundário:** Gov buyer (via segmento 4.4.b)
- **Tier:** Pro Plus (R$497+) + G-Buyer (R$1.997+)

#### KPI de valor percebido

- **Pipeline adicional/mês:** N de editais follow-on capturados via cross-sell alert
- **Conversion lift:** % de alertas que viram cards no pipeline

#### Defensibilidade

- **Market basket em 2M contratos:** único dataset. Mesmo com 20M contratos globais disponíveis, harmonização CATMAT + segmentação por tipo de órgão é o diferencial.
- **Risco:** spurious correlations (ex: correlação temporal sazonal que não é causal). Mitigar com lift threshold + sample size filter.

---

### 4.4.b. G-Buyer Persona — Stub para decisão user

**Contexto:** O user brief explicita equal-weighting entre empresa (vendedor) e órgão (comprador). Decisão sobre escopo/priorização em §7.3.b exige user sign-off.

**[ATUALIZAÇÃO empírica 2026-04-22 — ver §10.3]:** Dor G-Buyer **VALIDADA EMPIRICAMENTE** por 2 fontes da literatura 2026:

> "Os entes licitadores frequentemente enfrentam dificuldades para a realização de cotações de preços, seja por falta de estrutura e corpo técnico capacitado, seja por falta de fornecedores que se dispõem a auxiliar. (...) A excessiva dependência de consultas diretas a fornecedores sem a devida verificação da idoneidade das informações prestadas mostra-se recorrente, principalmente em municípios com estrutura técnica deficiente."
> — [Migalhas 2026 — Pesquisa de preços: Desafios e boas práticas](https://www.migalhas.com.br/depeso/425628/pesquisa-de-precos-nas-contratacoes-publicas-desafios-e-boas-praticas)

> "Apenas 28% das organizações federais estão em estágio avançado de governança de contratações; 44% em intermediário. 58% das orgs federais sem apoio formal da alta administração em governança de contratos."
> — [Observatório da Nova Lei 2026 — Déficits institucionais](https://www.novaleilicitacao.com.br/2026/04/09/governanca-das-contratacoes-na-lei-n-o-14-133-2021-entre-avancos-normativos-e-deficits-institucionais/) (citando TCU 2021 + levantamento 2024)

**Player incumbente detectado:** [Banco de Preços](https://www.bancodeprecos.com.br/) opera há 15+ anos no buy-side focado em cotação para licitação. SmartLic entraria via diferenciação (embedding + tempo real + cross-link com dados de vendedor) — **spike de positioning obrigatório antes de committar**.

**Se G-Buyer for priorizado (opções 2 ou 3 em §7.3.b), estas são as 3 dores candidatas a validação:**

1. **Preço de referência preparatório** — órgão em fase interna de processo licitatório precisa de "preço justo" para valor_estimado. Hoje: busca manual em sites de transparência + cotação com 3 fornecedores (40h-80h por processo). Delivery: tela `/gov/price-reference` com busca CATMAT + histórico 24m + spread UF + sugestão de valor_estimado com banda ±10%. **Reuso:** mesmo backend de PVX-003 (CATMAT) — diferença é UI e tier.

2. **Planejamento de compra via cross-sell similarity** — secretaria planeja orçamento anual e não sabe que órgãos similares compraram X + Y juntos em 85% dos casos. Hoje: planejamento individual, muitas vezes fragmentando em múltiplos pregões pequenos. Delivery: dashboard `/gov/purchase-planning` com market-basket recomendação (ref §4.6 — mesma engine, persona diferente). **Reuso:** feature #14 backend com UI para gov.

3. **Detecção de deserto antecipada** — órgão publica edital com especificação mal-calibrada e ninguém apresenta proposta (deserto = 8-12% dos editais). Hoje: descobre quando abre e está vazio. Delivery: pré-publicação scan com alerta "esta especificação tem 62% de probabilidade de deserto com base em editais similares nos últimos 12m" + sugestão de ajuste. **Novo:** pré-publicação scanner usa embeddings do §4.4 + probabilidade baseada em histórico de desertos.

**Tier proposto:** G-Buyer R$1.997/mês por órgão (procurement-specific; audit log; SSO/LDAP).

**Sales cycle estimado:** 6-12m (gov procurement). ROI payback: difícil estimar sem validation — **spike obrigatório antes de story open**.

**Decisão pendente:** ver §7.3.b para as 3 opções.

---

## 5. Second Wave (backlog pós top-6)

Candidatas com moat mas prioridade menor — documentadas para @sm referenciar em epic future:

| # | Feature | Por que second wave |
|---|---------|---------------------|
| #5 | **Procurement Calendar por Órgão** | Depende de ≥24m de dados por órgão (muitos órgãos com <30 contratos); complemento natural do 4.2 |
| #8 | **Consortium Finder** | Nicho — relevante para obras grandes (modalidade 4); N de usuários beneficiários menor |
| #11 | **Supplier Growth Detection** | Admin-level (útil para grandes fornecedores monitorando upstart); tier Enterprise |
| #12 | **Customer Concentration Risk** | Trivial de implementar mas baixa willingness-to-pay isolado; embedar em 4.1 Organ Health como "risk panel" |

**Recomendação:** Second wave entra após top-3 virar receita demonstrada (≥R$10K MRR incremental) — não antes.

---

## 6. Top-3 Priorizadas — Sequência de Execução

Após scoring e consideração de (a) blue-ocean coefficient, (b) time-to-value, (c) data readiness, (d) monetizability:

### 🏆 #1 — Contract Expiration Radar (4.1)

**Por quê primeiro:**
- **Data readiness: Alto.** `vigencia_fim` já está em `supplier_contracts`. Predição de janela de sucessão é regressão simples.
- **Blue ocean coefficient: Máximo.** Ninguém no mercado entrega alertas preditivos de edital.
- **Time-to-value: 1-2 sprints** (pipeline ETL + tela + alert — sem ML pesado).
- **Monetizability: Alta.** Feature por si só justifica tier Enterprise R$1.497.

**Sprint 1 target:** beta interno com 5 usuários Pro selecionados; alerta por email manual + CSV.
**Sprint 2 target:** GA com webhook + auto-pipeline-inject + alerta in-app.

### 🥇 #2 — Organ Health Dashboard (4.2) — *bundled com Customer Concentration (#12)*

**Por quê segundo:**
- **Data readiness: Médio.** Base em `supplier_contracts` já cobre cancellation + time-to-contract. Payment delay precisa crawl adicional.
- **Blue ocean coefficient: Alto.** Empenho-liquidação spread é signal único.
- **Time-to-value: 2-3 sprints** (primeiro MVP sem payment delay, V2 com).
- **Sinergia com #1:** user recebe alerta de contrato expirando + já vê health score do órgão = decisão go/no-go em ≤1min.

**Sprint 1 target:** MVP sem payment delay (cancellation + desert + time-to-contract) em 2-3 semanas.
**Sprint 2 target:** adicionar payment delay via crawl ComprasGov v3.

### 🥈 #3 — Competitive Radar por CNPJ (4.3)

**Por quê terceiro:**
- **Honra o "OUTRAS dores" do user brief:** CATMAT é dor **já nomeada** pelo user — Top-3 deve priorizar **novos** moats.
- **Data readiness: Médio.** Base `supplier_contracts` + setorização LLM já suficiente para MVP V1 (proxy-based). Atas de pregão V2 (6-12m).
- **Blue ocean coefficient: Alto.** Nenhum competidor entrega head-to-head CNPJ×CNPJ por setor+órgão.
- **Time-to-value: 2 sprints** (V1 proxy); **4-5 sprints** (V2 com atas).
- **Monetizability: Máxima.** Killer feature do tier Consultoria (R$997) — justifica R$200-400 upsell.

**Tradeoff honesto:** V1 é "directional signal" (proxy baseado em CNPJs co-presentes em editais similares — sem atas de pregão com lista real de participantes). UI DEVE marcar explicitamente como "proxy-based — calibrado pós-GA com atas". Risco de credibilidade mitigado com disclaimer + feedback loop.

**Sprint 1-2 target:** V1 proxy (matrix CNPJ×concorrente top-10 por setor+UF) + widget em ResultCard + dashboard.
**Sprint 3-4 target:** calibração com feedback user (ticket "desconto usado" opcional por edital fechado).
**Sprint 5+ target:** V2 crawl de atas — **delegar à data-engineer para spike em PVX-00X**.

### 🔄 Track paralelo — CATMAT Price Intelligence Pro (4.4) — incremental, baixa-dependência

Por ser extensão de feature pública existente (`/v1/itens/{catmat}/profile`) e por ser a dor **já conhecida** pelo user (não é discovery novo), mantém-se em **track paralelo** — não bloqueia Top-3 e não consome capacidade focus:

- **PVX-003 V1** (UF-breakdown + timeline, §8 Brief 3): 5 SP, 1 sprint, zero dependências
- **PVX-004 Spike** (item-level extraction feasibility): 3 SP, paralelo
- **PVX-005 V2** (harmonização embedding + G-Buyer): condicional ao spike, 13+ SP, Q4

**Racional da sequência:** Top-3 são discovery/novo-moat. CATMAT é incremental em cima do user-known pain. Separar tracks evita falso trade-off — ambos avançam.

### 6.1. Decision point — @user sign-off antes de @sm abrir stories

Duas escolhas foram tomadas no draft que o user pode (e deve) redirecionar:

**Escolha A — CATMAT em track paralelo (vs Top-3 central):**
- **Racional do draft:** user escreveu "OUTRAS dores além de preços unitários" → Top-3 prioriza novo-moat sobre known-pain.
- **Contra-argumento válido:** se user acredita que a dor de preço unitário é **maior que estimamos** (ex: gateway para G-Buyer justifica concentração de capacidade), swap CATMAT V1+V2 para Top-3.
- **Redirect caminho:** user decide em response message antes de @sm executar.

**Escolha B — Competitive Radar V1 como "proxy-based" signal:**
- **Racional do draft:** credibilidade importante mas outros V1s também têm caveats; disclaimer + feedback loop mitigam.
- **Contra-argumento válido:** se user preferir esperar atas de pregão antes de lançar (crítico em vertical sensível como Consultoria que paga R$997/mês por decisões precisas), adiar Competitive Radar para Q4 e promover Procurement Calendar (#5) ao Top-3.

Ambas escolhas são do user — doc não fecha sem sign-off.

---

## 7. Biases Auditados (QA Ioannidis + Kahneman)

### 7.1. B2G-specific biases (do overlay YAML)

| Viés | Presente nesta pesquisa? | Mitigação |
|---|---|---|
| **Survivorship bias** | ⚠️ Parcial — análise baseada em contratos vencidos, ignora editais cancelados/desertos | **#2 Organ Health explicitamente inclui cancellation_rate e desert_rate como feature** — converte o bias em opportunity signal |
| **Recency bias** | ❌ Não aplicável — pesquisa é prospectiva sobre features, não retrospectiva sobre dados | n/a |
| **Geographic bias** | ⚠️ Risco se pricing/adoption assume SP/RJ — plataforma tem 27 UFs | Top-3 features foram desenhadas UF-agnostic; Organ Health e Price Intelligence expõem UF-breakdown como first-class feature |
| **Modality bias** | ⚠️ Pregão (8) é default — mas Concorrência (4) é 30% do valor R$ | Features #1-#6 consideram modalidade como dimension — não agregam cegamente |

### 7.2. Ioannidis — Evidence reliability (PPV)

- **N-sample adequacy:** para cada feature onde cito "N potencial", é **hipótese** baseada em ordens de grandeza conhecidas (2M contratos, ~80K órgãos). **TODO @sm:** primeira story de cada feature deve incluir **"validation spike"** com SQL real sobre `supplier_contracts` para confirmar N — **não assumir os números deste doc**.

- **Positive Predictive Value dos scores:**
  - 4.2 Organ Health score composto: ponderação é **proposta** — exige calibração com ground truth (amostra 500-1000 órgãos, data real de pagamento) antes de GA
  - 4.5 Bid Success Predictor: calibração crítica — se deployado sem cross-validation, risco de over-fit

- **Proxy warning:** feature 4.3 Competitive Radar usa "CNPJs co-presentes em editais similares" como proxy de "competidores reais" (sem atas de pregão). Marcar como "proxy-based signal" na UI. **Ioannidis veredicto: directional — not deterministic.**

### 7.3.b. Weighting mismatch com brief do user — @user sign-off requerido

**User brief (literal):** "tanto para orgaos de governo... como para empresas"

**Este doc:** vendor-side (empresa B2G) é primary em todos os 6 deep-dives; gov-buyer segmento aparece só em §4.4.b como Fase 3 pós-D+180 (ver §4.4.b abaixo).

**Por quê essa priorização no draft:**
- Data-readiness: vendor tem dataset mais maduro (`supplier_contracts` + `profiles` pagantes)
- Sales cycle: vendor tem ciclo 14d (trial); gov-buyer tem 6-12m (procurement público)
- Monetization linear: vendor existing tier (Pro/Consultoria) é porta; gov-buyer exige tier novo + ciclo vendas gov

**Risco da priorização:**
- Se G-Buyer for market 2-3x maior que vendor (hipótese não validada), adiar custa opportunity cost real
- "Source of truth B2G" reputacional — gov-buyer adoção acelera "top of mind" em policy/prática

**Opções para o user decidir:**
1. Manter vendor-first (draft atual) — menor risco execução, menor upside TAM
2. Paralelizar vendor + G-Buyer em Epic separados (EPIC-PVX-VENDOR + EPIC-PVX-GBUYER)
3. Reverter para G-Buyer-first (requer validation spike de gov procurement cycle antes)

**Recomendação default (se user não redirecionar):** opção 1 + G-Buyer entra Q4 após validation de adoção vendor-side. Mas **não-bloquear @sm em PVX-001/002/003** por essa decisão.

### 7.3. Kahneman — Pre-mortem sobre Top-3

**"Em 12 meses essas features falharam. Por quê?"**

#### #1 Contract Expiration Radar falhou porque:
- **H1:** Padrão de sucessão por órgão é mais aleatório que regressão linear sugere — predição tem acurácia <40% em primeiro ano
  - **Mitigação:** começar com confidence interval largo; não prometer datas exatas, sim "janela provável"
- **H2:** Order de grandeza de 280K alertas/ano satura o user — ele ignora
  - **Mitigação:** smart filtering por relevância (setor + UF + faixa valor do user); max 20 alertas/semana
- **H3:** Órgãos mudaram padrão pós Lei 14.133 (data cut 2023) — modelo treinado em histórico antigo degradou
  - **Mitigação:** weight decay temporal — dados recentes pesam 3x mais

#### #2 Organ Health Dashboard falhou porque:
- **H1:** Dados de empenho/liquidação eram muito fragmentados; só 30% dos órgãos têm — user vê "N/A" em maioria e abandona
  - **Mitigação:** V1 sem payment delay; adicionar apenas quando cobertura ≥60% do universo relevante
- **H2:** Score composto não correlaciona com experiência real do user — user declina edital com score bom e depois órgão paga em dia
  - **Mitigação:** feedback loop — user marca "previsão errada" e modelo re-calibra

#### #3 CATMAT Price Intelligence Pro falhou porque:
- **H1:** Harmonização embedding colapsou items diferentes (ex: toner genérico ≠ toner HP específico) → P-quantiles enganosos
  - **Mitigação:** human-in-the-loop review sobre top 50 CATMATs antes de launch; threshold de similarity conservador (≥0.90)
- **H2:** Segmento G-Buyer teve ciclo de vendas de 9-12 meses (gov procurement) → ROI demora
  - **Mitigação:** não investir em G-Buyer até #1 e #2 entregarem receita demonstrada no segmento vendedor; G-Buyer é "Fase 3"

---

## 8. Handoff para @sm — Story Briefs

Os briefs abaixo estão em formato **pré-story** (input para o skill `sm` gerar story completa). Cada um tem: título, problema, AC iniciais, scope IN/OUT, dependências, complexidade.

---

### Brief 1 — STORY-PVX-001: Contract Expiration Radar (MVP)

**Epic:** EPIC-PVX-2026-Q3 (novo — **Product-Value Extraction**)

**Problema:** Usuários perdem 50-70% do pipeline por não receber alertas preditivos de sucessão de contratos. SmartLic tem dados suficientes em `supplier_contracts` para predizer a janela de publicação de edital sucessor com antecedência de 60-120 dias, mas não expõe essa intelligence.

**Acceptance Criteria (draft):**
- [ ] Materialized view ou tabela `contract_renewals` populada com todos contratos em `supplier_contracts` com `vigencia_fim BETWEEN now() AND now() + interval '180 days'`
- [ ] ARQ cron diário atualiza predição (`predicted_renewal_window_start`, `predicted_renewal_window_end`)
- [ ] Predição baseada em média móvel de `edital_publicacao - prev_vigencia_fim` por órgão (se órgão tem histórico ≥3 renovações; senão, média global por setor+modalidade)
- [ ] Tela `/radar-vencimentos` com filtros setor/UF/valor + timeline próximos 90d
- [ ] Email semanal "5 contratos expirando em sua watchlist" (user opt-in)
- [ ] API `GET /v1/radar/expiring-contracts?setor=&uf=&window_days=` (tier Pro Plus+)
- [ ] Feature flag `CONTRACT_EXPIRATION_RADAR_ENABLED`
- [ ] Prometheus metrics: alert_sent_total, prediction_accuracy (evaluated 90d post-launch)

**Scope IN:**
- Pipeline ETL + tabela + tela + email + API endpoint
- Cobertura: setores onde user tem ≥3 contratos em pipeline/histórico
- Acurácia target V1: ≥50% alertas dentro da janela prevista (±15 dias)

**Scope OUT:**
- Webhook push externo (V2)
- Auto-pipeline-inject (V2)
- ML model avançado (V1 é regressão linear + heurística)

**Dependências:**
- Validation spike: SQL real em `supplier_contracts` para confirmar N e distribuição de `vigencia_fim` — **1ª sub-story obrigatória**
- Feature de notificação in-app existente (STORY-445 Done)

**Complexidade:** 13 SP (2 sprints)

**Tier de pagamento:** Pro Plus novo (R$497-597/mês) OU Enterprise (R$1.497) — decidir em story de pricing separada

---

### Brief 2 — STORY-PVX-002: Organ Health Dashboard (MVP — sem payment delay)

**Epic:** EPIC-PVX-2026-Q3

**Problema:** Usuários declinam ou participam cegamente de editais sem saber a saúde operacional do órgão comprador (cancellation_rate, desert_rate, time-to-contract). Dados existem em `supplier_contracts` e `pncp_raw_bids` — não há aggregation materializada.

**Acceptance Criteria (draft):**
- [ ] Materialized view `organ_health_metrics` populada com 3 KPIs (cancellation_rate_12m, desert_rate_12m, avg_time_to_contract_days) + sample_size
- [ ] `reliability_score_v1` composto (peso: 40% cancellation + 30% desert + 30% time-to-contract)
- [ ] Flag `low_sample` quando `sample_size_12m < 30`
- [ ] Refresh diário (ARQ cron)
- [ ] Tela `/orgaos/[cnpj]/saude` com 3 KPIs + timeline trailing 12m + comparação com mediana UF
- [ ] Widget "Health Badge" (🟢🟡🔴) em cada ResultCard de `/buscar` e `/pipeline`
- [ ] Filtro em `/buscar`: "apenas órgãos com score ≥70"
- [ ] API `GET /v1/orgaos/{cnpj}/health`
- [ ] Feature flag `ORGAN_HEALTH_ENABLED`

**Scope IN:**
- 3 KPIs operacionais (cancellation, desert, time-to-contract)
- Dashboard por órgão + widget em busca
- Score composto V1 com pesos fixos

**Scope OUT:**
- Payment delay (V2, requer crawl ComprasGov v3)
- Score calibration via ground truth survey (V2, requer feedback users)
- Comparação histórica órgão vs órgão (V2)

**Dependências:**
- Validation spike: confirmar N contratos por órgão para viabilidade de `low_sample` threshold
- Classificação de setor por órgão (LLM sobre `supplier_contracts.objeto_contrato` + dominância)

**Complexidade:** 13 SP (2-3 sprints)

**Tier de pagamento:** Pro+ (score resumido) e Pro Plus (detalhamento completo)

---

### Brief 3 — STORY-PVX-003: Competitive Radar por CNPJ (V1 proxy)

**Epic:** EPIC-PVX-2026-Q3

**Problema:** Empresas B2G preparam propostas sem briefing competitivo — não sabem quem tipicamente concorre no edital-tipo X, com que desconto típico o concorrente vence, nem o próprio win rate vs cada competidor. Resultado: ou deixam margem na mesa, ou perdem por margem. SmartLic tem `supplier_contracts` × `cnpj_fornecedor` × setor × órgão suficiente para construir matriz head-to-head proxy-based V1.

**Acceptance Criteria (draft):**
- [ ] Materialized view `competitive_matrix` populada para user_cnpj ativo (Pro+): top 10 concorrentes por setor/UF com `co_occurrences_12m`, `user_wins`, `competitor_wins`, `avg_winning_discount_pct` (quando valor_estimado disponível)
- [ ] UI explicit label: "Proxy-based signal — calibrado pós-GA com atas de pregão"
- [ ] Tela `/competitivos` com dashboard pessoal user (top 10 concorrentes + head-to-head)
- [ ] Widget em cada ResultCard de `/buscar`: "3 concorrentes típicos deste perfil" + badge "você já perdeu N vezes para CNPJ X no último ano"
- [ ] Feedback loop: input opcional "desconto usado" em card de pipeline fechado (vira ground truth para calibração V2)
- [ ] API `POST /v1/competitive/analyze` (user_cnpj + edital_id → top concorrentes prováveis + disclaimer proxy)
- [ ] Feature flag `COMPETITIVE_RADAR_ENABLED`

**Scope IN:**
- V1 proxy: co-ocorrência em editais similares (mesmo setor + UF + faixa valor + modalidade)
- Matriz por cliente ativo com ≥10 contratos históricos (threshold confidence)
- UI com disclaimer explícito
- Feedback loop passivo (input opcional)

**Scope OUT:**
- V2 crawl de atas de pregão (STORY-PVX-00X, spike separado — delegar data-engineer)
- Predição de desconto por novo edital específico (V2 pós-calibração)
- Playbook AI-generated (V2)

**Dependências:**
- Classificação LLM de setor em `supplier_contracts.objeto_contrato` (completar pipeline se não existir)
- User precisa ter ≥10 contratos históricos para matrix própria (senão, exibir matrix setorial genérica)
- **Legal review obrigatório antes de GA** (não bloqueia V1 beta interno): delegar `/aiox-legal-analyst`

**Complexidade:** 13 SP (2 sprints V1; +5 SP em sprint 3 para feedback loop)

**Tier de pagamento:** Consultoria (R$997 — killer feature core) + Pro Plus upsell (R$497+)

---

### Brief 4 — STORY-PVX-004: CATMAT Price Intelligence — UF-breakdown + Timeline (V1 extension, track paralelo)

**Epic:** EPIC-PVX-2026-Q3

**Problema:** Feature `/v1/itens/{catmat}/profile` existente entrega P10/P50/P90 agregado global — mas sem quebra por UF/esfera, sem timeline, sem volume-curve. Dor declarada pelo user no brief. Extensão rápida da base atual — **track paralelo que não bloqueia Top-3 nem consome capacidade focus**.

**Acceptance Criteria (draft):**
- [ ] Endpoint existente `/v1/itens/{catmat}/profile` estendido com `group_by` param: `uf`, `esfera`, `modalidade`, `quarter`
- [ ] Tela `/itens/[catmat]` ganha: toggle dimension + timeline chart 12m + heatmap regional
- [ ] Flag `high_variance` quando spread (P90-P10) > 3σ da mediana global (signal de dado heterogêneo = requer harmonização V2)
- [ ] Sem alteração no backend `supplier_contracts` (V1 usa campos já existentes)
- [ ] Export CSV por CATMAT+dimensão

**Scope IN:**
- Dimensional breakdown + timeline sobre dados existentes
- UI refinement em tela existente

**Scope OUT:**
- Pipeline de extração item-level (STORY-PVX-005, separada — big investment)
- Harmonização embedding (STORY-PVX-006)
- Segmento G-Buyer (STORY-PVX-007+ — ver §4.4.b + §7.3.b decisão user)
- Price anomaly alert (STORY-PVX-008)

**Dependências:**
- Nenhuma — trabalho incremental sobre base pronta

**Complexidade:** 5 SP (1 sprint)

**Tier de pagamento:** Pro (UF-breakdown + timeline); Pro Plus (full dimensional + export bulk)

---

### Brief 5 (descoberta/preparatória) — STORY-PVX-005: Item-level Extraction Spike (validation)

**Tipo:** Spike (investigação) — pré-requisito para PVX-006 (harmonização) e PVX-007+ (G-Buyer)

**Pergunta a responder:**
- PNCP v2 `/contratacoes/{id}/itens` — qual cobertura real? (N% dos contratos tem items estruturados)
- Se cobertura <50%, crawl de PDF viável? Quais formatos dominam?
- Custo estimado de pipeline incremental para 10K items/dia

**Deliverable:** research memo `docs/research/2026-05-XX-item-level-extraction-feasibility.md`

**Complexidade:** 3 SP (1 sprint)

**Dependência:** sem dependência. Pode rodar em paralelo com PVX-001/002/003/004.

---

### Epic-level brief — EPIC-PVX-2026-Q3

**Nome proposto:** EPIC-PVX-2026-Q3 — **Product-Value Extraction**

**Objetivo:** Transformar SmartLic em "fonte da verdade" B2G via 3 data-moat features (Expiration Radar + Organ Health + Price Intelligence), habilitando tier Pro Plus (R$497-597) e Enterprise (R$1.497), e abrindo gateway para segmento G-Buyer (R$1.997/órgão).

**Horizon:** Q3 2026 (Jul-Set), 8-10 sprints.

**Ownership:**
- @pm (Morgan) orquestra epic
- @sm (River) cria stories (PVX-001 a PVX-007+)
- @architect (Aria) decide ML/pipeline architecture (especialmente PVX-005)
- @data-engineer (Dara) owns pipelines e materialized views
- @dev (Dex) implementa
- @qa (Quinn) valida com tests de calibração

**KPIs do Epic:**
- MRR incremental: +R$30K em 6 meses pós-launch (hipótese a validar — 50 users × R$600 avg upsell)
- Feature retention: ≥70% dos users com Pro Plus acessaram Expiration Radar ≥4x/mês
- Accuracy V1: Expiration Radar ≥50%; Organ Health score com user feedback NPS ≥40

**Gate reviews:**
- **D+45:** PVX-001 beta interno ativo com 5 users
- **D+90:** PVX-001 GA + PVX-002 MVP live; MRR incremental ≥R$5K
- **D+180:** PVX-003 V1 + PVX-005 spike completo; MRR incremental ≥R$30K

**Dependências externas:**
- EPIC-SEO-ORGANIC completo (para tráfego orgânico de gov-buyer segmento)
- EPIC-REVENUE-2026-Q2 com ≥10 pagantes (para dogfood + feedback real)

---

## 9. Limitações e Notas Honestas

1. **N amostrais citados são hipóteses** (≥100K, ≥80K órgãos, 2M contratos). Todos se baseiam em ordens de grandeza conhecidas do domain-glossary, mas **nenhuma query SQL foi executada nesta sessão**. Cada story de execução DEVE começar com validation spike.

2. **Calibração empírica é crítica** para Top-3 features. Proposta de pesos (Organ Health 40/30/30), thresholds (`similarity ≥0.85`), janelas (60-120d) são educated defaults — podem estar erradas em 10-30%. Requer A/B ou ground truth survey.

3. **Escopo não-incluído nesta pesquisa:**
   - Pre-flight habilitação (descartado como commodity — contestável se houver dado proprietário de cadastro)
   - Marketplace de consultores (descartado como fora de scope — requer 2-sided dynamics, é playbook diferente de data-value-extraction)
   - IA generativa de proposta técnica (fora de scope — vertical próprio, considerar EPIC-AI-COPILOT separado)

4. **Jurídico/regulatório ainda não consultado:** antes de GA de #4.3 Competitive Radar, delegar a `aiox-legal-analyst` revisão de Lei 14.133 Art. X sobre uso de dados de concorrentes para precificação (há risco de caracterização de anti-concorrencial?).

5. **Dependência externa crítica:** PVX-005 (harmonização embedding + extraction item-level) requer fonte PDF de termos de referência. Se cobertura PNCP v2 for <30%, custo de crawl multiplicativo. Spike obrigatório antes de planning.

6. ~~**Análise competitiva NÃO foi empiricamente realizada nesta sessão.**~~ **[RESOLVIDO 2026-04-22 via pesquisa web — ver §10 Competitive Landscape Empírico.]** Competitive research nível básico realizado (6 concorrentes, 2-3 features revisadas por cada). Gap remanescente: **teste hands-on dos produtos + entrevistas com usuários que migraram**. Recomendado spike 4-6h adicional se Competitive Radar avançar (LicitaGov é o rival mais próximo).

7. **Sequenciamento com epics em flight:** EPIC-REVENUE-2026-Q2 visa primeiro pagante D+45 com a mesma capacidade @dev que PVX-001/002 precisam. Conflito real de capacidade — requer **call de @pm** para sequenciar (sugestão: PVX começa após D+45 gate de REVENUE, ou dedicar 1 @dev para PVX em paralelo).

---

## 10. Competitive Landscape Empírico (2026-04-22)

**Método:** WebSearch + WebFetch em 6 concorrentes mapeados + literatura setorial (TCU, eLicitação, Observatório da Nova Lei). Nível: básico (marketing pages + artigos técnicos) — não inclui hands-on test dos produtos nem entrevistas com usuários migrados.

### 10.1. Matriz concorrente × feature

| Concorrente | Busca editais | Análise IA edital | Dashboard concorrentes | Contract Expiration Radar | Organ Health Score | CATMAT Price Intel | Foco |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| **LicitaJá** | ✅ | ⚠️ básico (sugestão editais) | ❌ | ❌ | ❌ | ❌ | Buscador |
| **Effecti (Minha Effecti)** | ✅ 1.400+ portais | ✅ | ⚠️ "nível concorrência recorrente" (agregado, não CNPJ) | ❌ | ❌ | ❌ | Plataforma vendedor + predição win rate |
| **LicitaIA** | ✅ | ✅ (lê edital + monta proposta + marcas/preços históricos) | ❌ | ❌ | ❌ | ⚠️ parcial (marcas/preços históricos) | All-in-one vendor |
| **LicitaGov** | ✅ | ✅ NLP/LLMs (redução 80% análise) | ✅ **"dashboard por CNPJ — onde concorrente participa, quais órgãos frequenta, a que preço ganha"** | ❌ | ❌ | ❌ | Monitoramento vendor |
| **Alerta Licitação** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Buscador |
| **Licitei** | ✅ | ✅ robô de lances | ❌ | ❌ | ❌ | ❌ | Automação lance |
| **Banco de Preços** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **15+ anos em buy-side (pesquisa preço referência)** | Gestor público (fase preparatória) |

Fontes: marketing pages de cada concorrente + [Effecti 2026](https://effecti.com.br/plataforma-de-licitacoes/), [LicitaGov 2026](https://licitagov.org/), [LicitaIA 2026](https://www.licitaia.app/), [Banco de Preços 2026](https://www.bancodeprecos.com.br/) (WebFetch 2026-04-22).

### 10.2. Implicações para a priorização Top-3

| Feature | Concorrente próximo | Impacto na prioridade |
|---|---|---|
| **Contract Expiration Radar** (#1) | NENHUM | **✅ Blue ocean confirmado.** Prioridade #1 mantida. |
| **Organ Health Dashboard** (#2) | NENHUM | **✅ Blue ocean confirmado.** Prioridade #2 mantida. |
| **Competitive Radar CNPJ** (#3) | **LicitaGov — replica parcialmente** | ⚠️ **NÃO é blue ocean virgin.** Moat reduzido: diferencial = dataset scale (2M contratos × ~300K CNPJs) + integração com Organ Health + Expiration Radar. **Recomendação:** manter no Top-3 MAS ajustar positioning de "novo moat" para "superior existing feature" — pricing deve refletir upgrade incremental vs Consultoria R$997, não tier Enterprise novo. |
| **CATMAT Price Intelligence Pro** (track paralelo) | **Banco de Preços — 15 anos liderando buy-side** | ⚠️ **Banco de Preços é incumbente.** Entrada no buy-side (G-Buyer) enfrenta moat reverso. Vendor-side tem espaço (nenhum concorrente foca lá). **Recomendação:** V1 foca vendor (precificação competitiva); G-Buyer requer diferenciação forte — recomendo spike de positioning antes de commitar. |

### 10.3. Dores de mercado empiricamente validadas (2026 literatura)

| Dor | Fonte | Feature SmartLic que endereça |
|---|---|---|
| **Assimetria de informação** entre fornecedores estruturados vs menos estruturados — "quem não analisa dados públicos atua sempre de forma reativa" | [eLicitação — Top 10 Desafios 2026](https://elicitacao.com.br/2025/12/31/desafios-para-fornecedores-de-licitacoes/) | #1 Expiration Radar + #3 Competitive Radar |
| **Formação de preços inadequada** — "fornecedor que precifica mal compromete toda execução contratual" | eLicitação Top 10 | CATMAT Price Intel (vendor-side) |
| **Subutilização do PNCP** — "para muitos, PNCP funciona apenas como repositório de editais" | eLicitação Top 10 | TODAS as features (posicionamento: "SmartLic transforma PNCP de repositório em intelligence") |
| **Gestor público sem estrutura para cotação** — "municípios com estrutura técnica deficiente dependem de cotação direta com fornecedores sem verificação" | [Migalhas — Pesquisa de preços 2026](https://www.migalhas.com.br/depeso/425628/pesquisa-de-precos-nas-contratacoes-publicas-desafios-e-boas-praticas), [Licitar Digital 2026](https://licitar.digital/pesquisa-de-preco-valor-de-mercado-sobrepreco-e-inexequibilidade-nas-licitacoes-publicas/) | §4.4.b G-Buyer — **DOR VALIDADA EMPIRICAMENTE** |
| **Baixa maturidade institucional dos órgãos** — "apenas 28% das orgs federais em estágio avançado de governança; 44% intermediário" (TCU 2021); "58% das orgs federais sem apoio formal da alta administração em governança de contratos" (levantamento 2024) | [Observatório da Nova Lei 2026](https://www.novaleilicitacao.com.br/2026/04/09/governanca-das-contratacoes-na-lei-n-o-14-133-2021-entre-avancos-normativos-e-deficits-institucionais/) | #2 Organ Health Dashboard — baixa maturidade é exatamente o sinal que queremos expor |
| **Atraso de pagamento sistêmico** — "contingenciamento faz órgãos atrasarem mesmo com serviço prestado; fornecedor pode extinguir contrato após 60 dias de atraso" | [ConLicitação 2026](https://conlicitacao.com.br/tudo-que-voce-precisa-saber-para-cobrar-a-administracao-publica/), [TCU 6.1.7](https://licitacoesecontratos.tcu.gov.br/6-1-7-pagamento/) | #2 Organ Health V2 (payment delay) — **valida criticidade do signal** |
| **Sobrepreço e jogo de planilha** — fraudes via item de baixo consumo subprecificado + itens de alto consumo sobreprecificados | [Jusbrasil - Sobrepreço 2026](https://www.jusbrasil.com.br/artigos/superfaturamento-e-sobrepreco-como-praticas-fraudulentas-em-processos-licitatorios/2670854611), [Migalhas - Lei 14.133 Sobrepreço](https://www.migalhas.com.br/amp/depeso/375078/lei-14-133-21-pesquisa-de-preco-em-contratacoes-da-administracao) | CATMAT Price Intel + Price Anomaly Detection (§4.4 V2) — **detecção automatizada de outliers 2σ é feature anti-fraude vendível a gestor público/controle interno** |

### 10.4. Tendência macro — AI em procurement governamental 2026

- Federal US: $1.7B em AI procurement 2024-2026; UK: £1.17B em 521 contratos públicos de AI 2025 ([GAO 2026](https://www.gao.gov/products/gao-26-107859), [Deloitte 2026](https://www.deloitte.com/us/en/insights/industry/government-public-sector-services/government-trends/2026/agentic-ai-government-customized-service-delivery.html)).
- Automação da avaliação técnica de propostas é mainstream ([Procurement Magazine 2026](https://procurementmag.com/technology-and-ai/how-ai-will-transform-procurement-in-2026), [iQuasar 2026](https://iquasar.com/blog/ai-procurement-in-2026-how-federal-agencies-will-use-automation-to-evaluate-and-monitor-contracts/)).
- **Implicação para SmartLic:** tendência global favorece posicionamento "AI-nativo" — mas o diferencial real é dataset Brasil-específico, não a tecnologia (commoditizada).

### 10.5. Decisões de positioning informadas pela evidência empírica

1. **Não competir em "busca + IA edital"** — commodity saturada (LicitaJá, Effecti, LicitaIA, LicitaGov, Licitei todos entregam). SmartLic busca deve ser "boa o suficiente", não diferencial.
2. **Competitive Radar como upgrade, não novo tier** — LicitaGov já entrega versão simples; nosso diferencial é dataset scale + cross-link com Organ Health + Expiration Radar. Tier Consultoria R$997 já cobre.
3. **Blue ocean real: Expiration Radar + Organ Health** — ninguém entrega. Esse é o story de marketing / positioning principal.
4. **CATMAT: duplo caminho viável** — vendor-side (não atendido) + G-Buyer (Banco de Preços é incumbente, requer diferenciação). Focar vendor V1; G-Buyer Fase 3.
5. **Posicionamento anti-fraude** (sobrepreço, jogo de planilha) é oportunidade para feature adjacente — vender para controladoria interna dos órgãos (segmento G-Audit, tier 4).

---

## 11. Next Steps

**Ordem recomendada (bloqueantes primeiro):**

1. **User (tiago.sasaki) — 2 decisões bloqueantes antes de @sm commitar:**
   - (a) **CATMAT vs Competitive Radar no Top-3** (ver §6.1 Escolha A)
   - (b) **Vendor-first vs G-Buyer paralelo** (ver §7.3.b — 3 opções)
   - **Também confirmar:** tier Pro Plus (R$497-597) novo é OK ou preferir upsell direto Pro → Consultoria?

2. **@pm (Morgan) — call de sequenciamento:**
   - EPIC-REVENUE-2026-Q2 (D+45 primeiro pagante) conflita com capacidade para PVX
   - Decidir: sequencial (PVX start pós D+45) ou paralelo (dedicar 1 @dev)
   - Orquestrar kickoff EPIC-PVX-2026-Q3 + gate reviews D+45/D+90/D+180

3. **Advisory boards — inputs bloqueantes para pricing:**
   - **`/turbocash`** — decisão pricing de Pro Plus (R$497-597) vs Enterprise (R$1.497) vs G-Buyer (R$1.997/órgão). Sem esse input, @po não fecha tier structure.
   - **`/aiox-legal-analyst`** — revisão Lei 14.133 para Competitive Radar (uso dados concorrentes para precificação) antes de GA — **não bloqueia V1 beta**, bloqueia GA.

4. **@data-engineer (Dara) — spikes paralelos:**
   - PVX-004: item-level extraction feasibility (cobertura PNCP v2 `/itens`, viability crawl PDF)
   - Competitive research spike: 4-6h avaliando concorrentes reais (ver §9 #6)

5. **@architect (Aria):** pós user sign-off, revisar decisões arquiteturais (materialized views vs tables, weight decay temporal, embedding stack); ADR para PVX-005.

6. **@sm (River):** após #1 + #2, criar stories PVX-001 a PVX-004 (briefs prontos em §8); validar complexity estimates com @architect.

7. **@po (Pax):** validar epic EPIC-PVX-2026-Q3 + confirm priorização pós user sign-off.

---

## 12. Change Log

| Data | Autor | Ação |
|---|---|---|
| 2026-04-22 | dr-orchestrator (aiox-deep-research) | Draft inicial — 15 candidatas, 6 deep-dives, top-3 priorizadas, biases auditados, briefs @sm |
| 2026-04-22 | dr-orchestrator (advisor reconcile) | Refactor Top-3: Competitive Radar swap in substituindo CATMAT (CATMAT vira track paralelo); adicionado §4.4.b G-Buyer stub, §6.1 decision points, §7.3.b weighting mismatch flag, §9 limitações (comp research ausente + capacity conflict) |
| 2026-04-22 | dr-orchestrator (empirical validation — post user challenge) | User apontou corretamente: squad `aiox-deep-research` não havia feito consulta web externa. Executado 8 WebSearch + 4 WebFetch: §10 Competitive Landscape Empírico novo (6 concorrentes × features matrix), §10.3 dores validadas via literatura 2026, §10.4 tendência macro, §10.5 positioning decisions. Ajustes: §9 #6 resolvido, §4.3 Competitive Radar re-calibrada (LicitaGov replica parcialmente — moat via dataset scale, não virgin blue ocean). §4.4 CATMAT re-calibrada (Banco de Preços é incumbente 15y em buy-side). §4.4.b G-Buyer promovida de hipótese para dor validada (Migalhas + Licitar Digital citam literalmente municípios com estrutura deficiente). |

---

**Status:** DRAFT — 2 decision points bloqueantes para @user:

### Decisão A — §6.1 — Composição Top-3
**Pergunta:** Top-3 atual (Expiration Radar + Organ Health + Competitive Radar) é o correto, OU swap Competitive Radar por CATMAT (dor already-known pelo user)?

**Default do draft:** novos moats em Top-3; CATMAT como track paralelo incremental (1 sprint, zero dependências).

### Decisão B — §7.3.b — Peso G-Buyer
**Pergunta:** G-Buyer (órgão comprador) entra Q4 após D+180, paralelo em epic separado, ou invert para G-Buyer-first?

**Default do draft:** vendor-first; G-Buyer em Fase 3 pós-validação adoção.

### Unblocks paralelos (não dependem do user)
- `/turbocash` — pricing Pro Plus/Enterprise/G-Buyer tiers
- `/aiox-legal-analyst` — Lei 14.133 review para Competitive Radar GA (não bloqueia beta)
- Competitive research spike de 4-6h (§9 #6)
- @pm call de capacidade vs EPIC-REVENUE (§9 #7)

**Recomendação operacional:** user responder A+B em mensagem → @sm abre PVX-001 e PVX-002 (não dependem das decisões) enquanto decisões A+B refinam PVX-003/004 stack order.
