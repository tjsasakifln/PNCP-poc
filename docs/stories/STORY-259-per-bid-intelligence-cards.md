# STORY-259: Per-Bid Intelligence Cards — Análise Batch + Análise Aprofundada On-Demand

**Status:** Draft
**Priority:** P0 — Critical (Landing Page Parity)
**Track:** GTM — Go-to-Market Readiness
**Created:** 2026-02-23
**Depends on:** —
**Blocks:** STORY-260 (progressive profiling alimenta dados para análise)

---

## Contexto

A landing page promete "cada oportunidade vem com critérios objetivos" e mostra cards detalhados com justificativa, ação recomendada e % de compatibilidade. Hoje o produto entrega badges genéricos sem explicação.

### Arquitetura Decidida: 2 Níveis de Análise

**Nível 1 — Batch Analysis (automático, todos os editais aprovados):**
- 1 chamada LLM (GPT-4.1-nano) para o lote completo de editais aprovados
- Gera justificativa resumida + ação recomendada + % compatibilidade para CADA edital
- Executado como parte do pipeline de busca (via ARQ job, como o resumo executivo)
- Custo: ~$0.001-0.003 por busca (1 call batch)
- Latência: ~200-500ms (1 call, não N calls)

**Nível 2 — Análise Aprofundada (on-demand, por edital):**
- Botão "Analisar em detalhe" em cada card de resultado
- 1 chamada LLM dedicada cruzando: texto do edital × perfil completo do licitante
- Gera card completo no padrão da landing (ProofOfValue):
  - Score de compatibilidade (X/10)
  - Decisão sugerida (PARTICIPAR / AVALIAR COM CAUTELA / NÃO PARTICIPAR)
  - Análise de prazo (dias restantes + avaliação)
  - Análise de requisitos (atestados, certificações detectadas)
  - Análise de competitividade (estimativa baseada na modalidade)
  - Riscos identificados
- Custo: ~$0.0001 por análise individual
- Latência: ~100-200ms (1 call individual)

---

## Acceptance Criteria

### Backend — Nível 1: Batch Analysis (Pipeline)

- [ ] **AC1:** Nova função `batch_analyze_bids()` em `llm_arbiter.py` (ou novo módulo `bid_analyzer.py`):
  - Input: lista de editais aprovados (max 50) + perfil do usuário (setor, porte, UFs, faixa_valor)
  - Output: `list[BidAnalysis]` com campos: `bid_id`, `justificativas: list[str]`, `acao_recomendada: str`, `compatibilidade_pct: int`
  - Prompt envia editais em formato condensado (id + objeto + valor + UF + modalidade) + perfil
  - Response: JSON array com análise por edital
  - Model: GPT-4.1-nano, structured output (response_format)

- [ ] **AC2:** Schema `BidAnalysis` em schemas.py:
  ```python
  class BidAnalysis(BaseModel):
      bid_id: str
      justificativas: list[str]      # 3-5 bullets no padrão landing
      acao_recomendada: str           # PARTICIPAR | AVALIAR COM CAUTELA | NÃO PARTICIPAR
      compatibilidade_pct: int        # 0-100
  ```

- [ ] **AC3:** Pipeline stage 6 (GenerateOutput) dispara `batch_analyze_bids()` como ARQ job (paralelo ao resumo executivo):
  - Se ARQ disponível: job `bid_analysis_job` (background)
  - Se ARQ indisponível: executa inline
  - Fallback se LLM falhar: justificativa calculada (puro Python, baseada em scores de viabilidade)

- [ ] **AC4:** SSE event `bid_analysis_ready` entrega resultado batch ao frontend:
  - Mesmo padrão de `llm_ready` e `excel_ready`
  - Frontend atualiza cards com justificativas quando recebe evento
  - Resultado persistido em Redis: `bidiq:job_result:{search_id}:bid_analysis`, 1h TTL

- [ ] **AC5:** Prompt batch inclui perfil do usuário quando disponível:
  ```
  PERFIL DO LICITANTE:
  - Setor: {setor}
  - Porte: {porte} (se disponível)
  - Faixa de valor: R$ {min} – R$ {max}
  - UFs de atuação: {ufs}
  - Atestados: {atestados} (se disponível)
  ```
  Se campo ausente no perfil, omite da prompt (não envia "N/A")

- [ ] **AC6:** Fallback Python (sem LLM) gera justificativas baseadas nos scores de viabilidade:
  - Setor: "Setor compatível: {nome}" / "Setor parcialmente compatível"
  - Valor: "R$ {valor} — dentro da faixa {range}" / "fora da faixa"
  - Prazo: "{X} dias restantes — prazo {adequado/apertado/insuficiente}"
  - Região: "{UF} — {dentro/fora} da sua região"
  - Ação: Alta→PARTICIPAR, Média→AVALIAR COM CAUTELA, Baixa→NÃO PARTICIPAR
  - Compatibilidade: `combined_score` arredondado

### Backend — Nível 2: Análise Aprofundada (On-Demand)

- [ ] **AC7:** Novo endpoint `POST /v1/bid-analysis/{bid_id}`:
  - Input: `{ search_id: str, bid_id: str }` + auth (user_id do token)
  - Carrega dados do edital do cache/search_session
  - Carrega perfil completo do usuário (profiles.context_data)
  - Executa 1 chamada LLM dedicada com prompt detalhado
  - Output: `DeepBidAnalysis`

- [ ] **AC8:** Schema `DeepBidAnalysis` em schemas.py:
  ```python
  class DeepBidAnalysis(BaseModel):
      bid_id: str
      score: float                        # 0.0-10.0 (formato landing)
      decisao_sugerida: str               # PARTICIPAR | AVALIAR COM CAUTELA | NÃO PARTICIPAR
      compatibilidade_pct: int            # 0-100
      analise_prazo: str                  # "15 dias — prazo viável para preparar proposta"
      analise_requisitos: list[str]       # ["Exige atestado X", "Requer certificação Y"]
      analise_competitividade: str        # "3-5 concorrentes previstos (pregão eletrônico)"
      riscos: list[str]                   # ["Prazo apertado", "Valor acima do habitual"]
      justificativas_favoraveis: list[str] # Pontos positivos
      justificativas_contra: list[str]     # Pontos negativos
      recomendacao_final: str             # 1-2 frases com recomendação
  ```

- [ ] **AC9:** Prompt da análise aprofundada cruza **texto completo do edital** (objeto + descrição, max 2000 chars) × **perfil completo do licitante**:
  ```
  Analise esta licitação para o perfil do licitante abaixo.

  LICITAÇÃO:
  - Objeto: {objeto}
  - Valor estimado: R$ {valor}
  - Modalidade: {modalidade}
  - UF: {uf}
  - Órgão: {orgao}
  - Prazo: {data_abertura} ({dias_restantes} dias)

  PERFIL DO LICITANTE:
  - Setor: {setor}
  - Porte: {porte}
  - Faixa de valor ideal: R$ {min} – R$ {max}
  - UFs de atuação: {ufs}
  - Atestados/certificações: {atestados}
  - Experiência: {experiencia}
  - Capacidade: {capacidade}

  Responda em JSON com: score (0-10), decisao_sugerida, ...
  ```

- [ ] **AC10:** Rate limit: 20 análises aprofundadas por hora por usuário (`DEEP_ANALYSIS_RATE_LIMIT`)
- [ ] **AC11:** Cache da análise aprofundada: Redis key `bidiq:deep_analysis:{user_id}:{bid_id}`, 24h TTL (perfil pode mudar, mas análise é válida por 1 dia)
- [ ] **AC12:** Se edital não encontrado no cache/session: retorna 404 com mensagem clara

### Frontend — Cards com Análise Batch (Nível 1)

- [ ] **AC13:** `BidCard` exibe badge **"X% compatível"** quando `compatibilidade_pct` disponível:
  - Verde (emerald) ≥ 70%
  - Amarelo (amber) 40-69%
  - Cinza (slate) < 40%
  - Visível sem expandir o card

- [ ] **AC14:** `BidCard` exibe label **ação recomendada**:
  - "PARTICIPAR" — badge verde com ícone check
  - "AVALIAR COM CAUTELA" — badge amarelo com ícone alerta
  - "NÃO PARTICIPAR" — badge cinza com ícone X
  - Visível sem expandir o card

- [ ] **AC15:** `BidCard` expandido mostra seção **"Por que foi recomendado"** com lista de justificativas:
  - Bullets com ícone (check verde para positivo, alerta para neutro)
  - Se viabilidade Baixa: título "Por que não recomendado"

- [ ] **AC16:** Cards iniciam com placeholder/skeleton enquanto `bid_analysis_ready` não chega:
  - Badge "Analisando..." com spinner discreto
  - Quando SSE `bid_analysis_ready` chega, atualiza cards com animação sutil

- [ ] **AC17:** Fallback: se batch analysis não disponível (timeout, erro), cards mostram apenas badges existentes (viabilidade + relevância) — **zero degradação**

### Frontend — Análise Aprofundada (Nível 2)

- [ ] **AC18:** Botão **"Analisar em detalhe"** (ícone lupa + texto) em cada BidCard:
  - Aparece no card expandido
  - Desabilitado se rate limit atingido (tooltip: "Limite de análises atingido")

- [ ] **AC19:** Ao clicar: loading state no botão → `POST /v1/bid-analysis/{bid_id}` → abre **modal/drawer** com card completo:
  - Layout no padrão ProofOfValue da landing page
  - Score X/10 (badge circular grande)
  - Decisão sugerida (label colorido)
  - Seções: Prazo | Requisitos | Competitividade | Riscos
  - Justificativas favoráveis vs. contra (2 colunas)
  - Recomendação final (destaque)
  - Botão "Adicionar ao Pipeline" (CTA)

- [ ] **AC20:** Componente `DeepAnalysisModal` (NOVO):
  - Modal responsivo (full-screen no mobile)
  - Loading skeleton enquanto LLM processa
  - Transição suave ao receber dados
  - Botão fechar (X) + ESC + click outside

- [ ] **AC21:** Se análise aprofundada já em cache (feita anteriormente): exibe instantaneamente sem loading

### Testes

- [ ] **AC22:** Backend: ≥12 testes em `test_bid_analysis.py`:
  - batch_analyze_bids com 0, 1, 50 editais
  - Fallback Python quando LLM falha
  - Endpoint /bid-analysis com perfil completo/parcial/vazio
  - Rate limit enforcement
  - Cache hit/miss
  - Prompt inclui/omite campos ausentes do perfil

- [ ] **AC23:** Frontend: ≥10 testes em `bid-intelligence-cards.test.tsx`:
  - CompatibilityBadge renderiza 3 cores
  - ActionLabel renderiza 3 estados
  - Justificativas expandíveis
  - SSE bid_analysis_ready atualiza cards
  - DeepAnalysisModal abre/fecha
  - Loading states e fallbacks

- [ ] **AC24:** Zero regressões nos testes existentes

### Backward Compatibility

- [ ] **AC25:** Todos os campos novos são **Optional** — cache existente continua funcionando
- [ ] **AC26:** Se batch analysis job não dispara (ARQ indisponível), fallback Python gera análise imediata

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Nível 1: Batch Analysis (automático)                     │
│                                                          │
│  Pipeline Stage 6 (GenerateOutput)                       │
│       ↓                                                  │
│  ARQ Job: bid_analysis_job                               │
│       ↓                                                  │
│  GPT-4.1-nano (1 call, N editais condensados + perfil)   │
│       ↓                                                  │
│  SSE: bid_analysis_ready → Frontend atualiza cards       │
│                                                          │
│  Fallback: Python puro baseado em viability scores       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Nível 2: Análise Aprofundada (on-demand)                 │
│                                                          │
│  Botão "Analisar em detalhe" → POST /v1/bid-analysis/X  │
│       ↓                                                  │
│  GPT-4.1-nano (1 call, edital completo × perfil)         │
│       ↓                                                  │
│  DeepAnalysisModal com card no padrão landing page       │
│                                                          │
│  Cache: Redis 24h (mesmo user+bid = instant)             │
└─────────────────────────────────────────────────────────┘
```

### Custo Estimado

| Cenário | Calls LLM | Custo |
|---------|-----------|-------|
| 1 busca (batch 50 editais) | 1 | ~$0.002 |
| + 3 análises aprofundadas | 3 | ~$0.0003 |
| 100 buscas/dia | 100 batch + ~50 deep | ~$0.25/dia |
| 1000 buscas/mês | ~1000 batch + ~500 deep | ~$7.50/mês |

---

## File List

| File | Action |
|------|--------|
| `backend/bid_analyzer.py` | CREATE — batch_analyze_bids + deep_analyze_bid |
| `backend/routes/bid_analysis.py` | CREATE — POST /v1/bid-analysis/{bid_id} |
| `backend/schemas.py` | MODIFY — BidAnalysis + DeepBidAnalysis schemas |
| `backend/search_pipeline.py` | MODIFY — dispatch bid_analysis_job in stage 6 |
| `backend/job_queue.py` | MODIFY — add bid_analysis_job |
| `backend/main.py` | MODIFY — register bid_analysis router |
| `backend/config.py` | MODIFY — DEEP_ANALYSIS_RATE_LIMIT |
| `frontend/app/buscar/components/CompatibilityBadge.tsx` | CREATE |
| `frontend/app/buscar/components/ActionLabel.tsx` | CREATE |
| `frontend/app/buscar/components/DeepAnalysisModal.tsx` | CREATE |
| `frontend/app/buscar/components/SearchResults.tsx` | MODIFY — integrate new components |
| `frontend/app/buscar/components/ViabilityBadge.tsx` | MODIFY — tooltip text |
| `frontend/hooks/useSearch.ts` | MODIFY — handle bid_analysis_ready SSE |
| `frontend/app/api/bid-analysis/[bidId]/route.ts` | CREATE — API proxy |
| `backend/tests/test_bid_analysis.py` | CREATE |
| `frontend/__tests__/bid-intelligence-cards.test.tsx` | CREATE |
