# GTM-FIX-028: Filtro Inteligente — LLM Classifica, Zero Resultado Fantasma

**Priority:** P0 (BLOCKER — sistema retorna 0 resultados para todos os 15 setores)
**Score Impact:** D02 3→7 (produto entrega valor), D09 4→8 (data quality percebida)
**Estimated Effort:** 4-6 horas (2 tracks paralelos)
**Sprint:** Current (imediato — pós GTM-FIX-027)
**Depends on:** GTM-FIX-027 (pipeline fixes — merged em `43b88d0`)
**Reviewed by:** @architect (Aria), @data-engineer (Dara) — 2026-02-17

---

## Filosofia do Produto

> **"Se a oportunidade existe, será exibida. Se algo não é relevante, será descartado. Só o ouro, zero ruído."**

O sistema DEVE filtrar — mas o filtro precisa FUNCIONAR. Keywords sozinhas não determinam relevância. GPT-4.1-nano determina.

---

## Problema

### O que acontece hoje (todos os 15 setores)

1. PNCP+PCP retornam **N licitações reais** (22-228 dependendo de UFs)
2. `filter.py` **linha ~2175**: `match_keywords()` retorna `False` → `stats["rejeitadas_keyword"] += 1` → **descartada sem jamais consultar LLM**
3. Licitações que passam keyword gate (match > 0) chegam à Camada 2A — mas com 0% match, **NENHUMA** chega lá
4. Frontend recebe `licitacoes: []`, mostra **"Nenhuma Oportunidade Relevante Encontrada"**

### A falha arquitetural (corrigida por @architect)

O ponto de interceptação correto NÃO é a Camada 2A (density thresholds). O problema está **antes**, no keyword matching loop (filter.py linhas 2149-2185):

```python
# filter.py ~linha 2150 — AQUI está o bloqueio
for lic in resultado_valor:
    match, matched_terms = match_keywords(objeto, kw, exc, ...)
    if match:
        resultado_keyword.append(lic)  # → segue para Camada 2A
    else:
        stats["rejeitadas_keyword"] += 1  # ← 100% das licitações caem aqui
        # NUNCA chega ao LLM arbiter
```

A Camada 2A (linhas 2187+) só opera sobre `resultado_keyword` — que está **vazio** quando nenhuma keyword casa. O LLM arbiter (linhas 2281+) nunca é consultado.

### Dados por fonte

| Fonte | Campo usado | Qualidade | Nota |
|-------|------------|-----------|------|
| PNCP | `objetoCompra` | Alta — descrições detalhadas (50-500 chars) | Ideal para LLM |
| PCP v2 | `resumo` | Variável — pode ser curta (3-10 palavras) | Precisa guard < 20 chars |
| PCP v2 | `valor_estimado` | **Sempre 0.0** (v2 listing não retorna valor) | Não enviar ao LLM como "R$ 0,00" |

### Evidência de produção (2026-02-17)

| Busca | Retornadas | Keyword match | LLM consultado | Exibidas |
|-------|-----------|---------------|----------------|----------|
| Saúde, SP+RJ+MG | 59 | 0/59 (0%) | 0/59 | **0** |
| Software, 27 UFs | 228 | 0/228 (0%) | 0/228 | **0** |
| Vestuário, SP | 22 | 0/22 (0%) | 0/22 | **0** |

**Zero LLM calls** — o arbiter nunca foi consultado porque nenhuma licitação passou o keyword gate.

### Custo da inação

- Produto inutilizável para **todos** os 15 setores
- Trial → 0 resultados → 0 conversão → R$0 revenue
- "Inteligência de decisão em licitações" que não mostra licitações

---

## Solução

### Princípio: Keywords são pré-filtro rápido. LLM é o decisor final. "Zero ruído" = LLM rejeita, não keyword sozinha.

**Antes:** `0 keyword matches → auto-reject (sem LLM)`
**Depois:** `0 keyword matches → LLM classifica → SIM: exibe / NAO: descarta`

### Nova arquitetura do filtro

```
PNCP+PCP retornam 59 licitações
    ↓
Filtros OBRIGATÓRIOS (inalterados):
  - UF, Modalidade, Valor, Prazo/Status
    ↓
59 licitações passam filtros obrigatórios
    ↓
Keyword matching (filter.py ~linha 2150):
  match_keywords() = True   → resultado_keyword (segue para Camada 2A normal)  [inalterado]
  match_keywords() = False  → resultado_llm_zero (NOVO — era reject)           [MUDANÇA]
    ↓
resultado_keyword → Camada 2A density thresholds (inalterado):
  density > 5%    → auto-ACCEPT
  2-5%            → LLM prompt standard
  1-2%            → LLM prompt conservative
  < 1%            → LLM prompt conservative (era reject, agora LLM)           [MUDANÇA]
    ↓
resultado_llm_zero → LLM prompt sector-aware (NOVO):
  Guard: skip se objeto < 20 chars (PCP resumo curto demais para LLM)
  Guard: valor=0.0 → "Não informado" no prompt (PCP v2 não tem valor)
  LLM GPT-4.1-nano: SIM/NAO
    ↓
Async concurrency (semáforo 10):
  asyncio.gather() com até 10 chamadas LLM simultâneas
  (Batching 10/prompt impossível — max_tokens=1 força resposta single-token)
    ↓
SIM → exibida ao usuário (ouro), relevance_source="llm"
NAO → descartada (ruído)
    ↓
FLUXO 2 (recovery): DESATIVADO quando LLM_ZERO_MATCH_ENABLED=true
  (Evita double-classification: bids já avaliados por zero_match
   não precisam de synonym recovery — LLM já analisou contexto completo)
    ↓
Resultado: só oportunidades relevantes, zero falso-negativo
```

### Por que funciona

1. **O LLM arbiter já existe** (`llm_arbiter.py`) — `classify_contract_primary_match()` com cache MD5, fallback, logging
2. **O prompt já está calibrado** — sistema conservador ("Em caso de dúvida, responda NAO"), com exemplos dinâmicos do setor
3. **O custo é desprezível** — R$ 0.005/busca (59 bids), R$ 1.10/mês por usuário, **0.06% da receita**
4. **Async concurrency** — semáforo de 10 chamadas simultâneas, ~300ms para 59 bids (vs ~3s sequencial)

### Custo detalhado (GPT-4.1-nano)

| Cenário | Bids | LLM calls | Custo/busca | Custo/mês (200 buscas) |
|---------|------|-----------|-------------|------------------------|
| 1 UF | 22 | 22 | R$ 0.002 | R$ 0.40 |
| 3 UFs | 59 | 59 | R$ 0.005 | R$ 1.10 |
| 27 UFs | 228 | 228 | R$ 0.021 | R$ 4.20 |
| Com cache 75% | 59 | ~15 | R$ 0.001 | R$ 0.27 |

**Pior caso absoluto** (1000 buscas/mês x 228 bids, sem cache): **R$ 21/mês** = 1.05% de R$1.999. **Irrelevante.**

---

## Acceptance Criteria

### Track 1: Backend — LLM para Zero Keyword Match (filter.py + llm_arbiter.py)

- [ ] **AC1**: `filter.py` linha ~2175 — licitações com `match_keywords() = False` são coletadas em `resultado_llm_zero` em vez de auto-reject. O keyword gate deixa de ser eliminatório.
- [ ] **AC2**: `filter.py` Camada 2A — licitações com density < 1% (`TERM_DENSITY_LOW_THRESHOLD`) que JÁ passaram keyword gate são enviadas ao LLM com prompt conservative em vez de auto-reject (linha ~2215).
- [ ] **AC3**: `filter.py` — Guard para PCP `resumo` curto: se `len(objeto) < 20`, skip LLM e auto-REJECT com log warning (sinal insuficiente para classificação).
- [ ] **AC4**: `llm_arbiter.py` — `classify_contract_primary_match()` aceita `prompt_level="zero_match"` e usa `_build_zero_match_prompt()` que inclui:
  - Nome e descrição do setor (de `sectors_data.yaml`)
  - Top 5 keywords como exemplos de SIM
  - Top 3 exclusions como exemplos de NAO
  - Valor: `"Não informado"` quando `valor == 0.0` (PCP v2 não tem valor — não confundir LLM com "R$ 0,00")
  - Instrução: "Este contrato é sobre {setor_name}? Responda APENAS: SIM ou NAO"
- [ ] **AC5**: `llm_arbiter.py` — Migrar default model de `gpt-4o-mini` para `gpt-4.1-nano` via env `LLM_ARBITER_MODEL` (33% mais barato, mesma qualidade para classificação binária SIM/NAO)
- [ ] **AC6**: `filter.py` — Async concurrency com `asyncio.Semaphore(10)` + `asyncio.gather()` para chamadas LLM paralelas. NÃO batching (impossível com `max_tokens=1`).
- [ ] **AC7**: `schemas.py` — `FilterStats` ganha campos:
  - `llm_zero_match_calls: int` — chamadas LLM para bids sem keyword match
  - `llm_zero_match_aprovadas: int` — aprovadas pelo LLM na zona zero
  - `llm_zero_match_rejeitadas: int` — rejeitadas pelo LLM na zona zero
  - `llm_zero_match_skipped_short: int` — skipped por objeto curto (< 20 chars)
- [ ] **AC8**: `schemas.py` — `LicitacaoItem` ganha campo `relevance_source: Optional[str]` com valores: `"keyword"` (density > 5%), `"llm_standard"` (2-5%), `"llm_conservative"` (1-2%), `"llm_zero_match"` (0%).
- [ ] **AC9**: Fallback se LLM falhar: **REJECT** (manter filosofia "zero ruído"). Consistente com fallback existente em `classify_contract_primary_match()` linha 275: `return False`.
- [ ] **AC10**: `filter.py` — Quando `LLM_ZERO_MATCH_ENABLED=true`, desativar FLUXO 2 (recovery pipeline linhas 2553-2716) para bids já classificados por zero_match. Evita double-classification e custo duplicado.
- [ ] **AC11**: `config.py` — Novo env `LLM_ZERO_MATCH_ENABLED=true` (feature flag para rollback). Quando `false`, comportamento idêntico ao atual (auto-reject).

### Track 2: Frontend — Indicador Visual + Empty State Fix

- [ ] **AC12**: Cada card de resultado ganha badge baseado em `relevance_source`:
  - `"keyword"` → "Keyword match" (verde)
  - `"llm_standard"` / `"llm_conservative"` / `"llm_zero_match"` → "Validado por IA" (azul)
  - `null/undefined` → sem badge (retrocompatível)
- [ ] **AC13**: Header mostra contagem: "{total_raw} analisados, {total_filtrado} relevantes para {setor}"
- [ ] **AC14**: `EmptyState.tsx` — Mensagem revisada quando LLM rejeita TODAS:
  - "Analisamos {N} licitações com IA e nenhuma é relevante para {setor} neste período. Tente ampliar a busca."
  - Diferente do "zero resultados" atual — comunica que a análise FOI feita
- [ ] **AC15**: `EmptyState.tsx` — Só aparece quando: (a) PNCP+PCP retornaram 0 resultados OU (b) LLM rejeitou todas. NUNCA por keyword match sozinho.
- [ ] **AC16**: `SearchResults.tsx` — Se `filter_stats.llm_zero_match_calls > 0`, mostrar nota: "IA analisou {N} licitações adicionais para identificar oportunidades relevantes"

### Testes

- [ ] **AC17**: Teste: 59 licitações com 0 keyword matches → todas passam pelo LLM → N>0 aprovadas (mock LLM retorna SIM para ~30%)
- [ ] **AC18**: Teste: LLM rejeita todas → EmptyState mostra mensagem "analisamos N com IA"
- [ ] **AC19**: Teste: LLM fallback (API down) → licitações REJEITADAS (zero ruído preservado)
- [ ] **AC20**: Teste: async concurrency com semáforo 10 — verifica que no máximo 10 chamadas simultâneas
- [ ] **AC21**: Teste: `FilterStats` registra `llm_zero_match_calls`, aprovadas e rejeitadas
- [ ] **AC22**: Teste: density > 5% continua auto-accept sem LLM (regressão)
- [ ] **AC23**: Teste: density 1-5% continua usando LLM standard/conservative (regressão)
- [ ] **AC24**: Teste: PCP bid com `valor_estimado=0.0` → prompt mostra "Não informado" (não "R$ 0,00")
- [ ] **AC25**: Teste: PCP bid com `resumo` < 20 chars → skipped, registrado em `llm_zero_match_skipped_short`
- [ ] **AC26**: Teste: FLUXO 2 desativado para bids já classificados por zero_match
- [ ] **AC27**: Teste frontend: badge "Validado por IA" aparece quando `relevance_source` contém "llm"

### Validação em Produção

- [ ] **AC28**: Busca "Saúde" SP+RJ+MG retorna N > 0 resultados (vs 0 hoje)
- [ ] **AC29**: Busca "Software" 27 UFs retorna N > 0 resultados (vs 0 hoje)
- [ ] **AC30**: Busca "Vestuário" SP retorna N > 0 resultados (vs 0 hoje)
- [ ] **AC31**: Testar pelo menos 5 dos 15 setores — nenhum retorna 0 quando PNCP tem dados
- [ ] **AC32**: Logs mostram `llm_zero_match_calls > 0` e `llm_zero_match_aprovadas > 0`

---

## Implementação

### Track 1: Backend (AC1-AC11, AC17-AC26)

**Arquivos:**
- `backend/filter.py` — Interceptar keyword gate (~L2175), coletar zero-match bids, async LLM, desativar FLUXO 2
- `backend/llm_arbiter.py` — Novo prompt `zero_match` com guards PCP, migrar para gpt-4.1-nano
- `backend/config.py` — `LLM_ZERO_MATCH_ENABLED`, atualizar `LLM_ARBITER_MODEL` default
- `backend/schemas.py` — Novos campos em `FilterStats`, campo `relevance_source` em `LicitacaoItem`

**Mudança principal em filter.py (keyword gate ~L2175):**
```python
# ANTES (auto-reject):
else:
    stats["rejeitadas_keyword"] += 1

# DEPOIS (coletar para LLM):
else:
    if llm_zero_match_enabled:
        resultado_llm_zero.append(lic)
    else:
        stats["rejeitadas_keyword"] += 1
```

**Processamento LLM zero-match (novo bloco após Camada 2A):**
```python
# Async LLM classification para zero-match bids
if resultado_llm_zero and llm_zero_match_enabled:
    sem = asyncio.Semaphore(10)

    async def classify_one(lic):
        objeto = lic.get("objetoCompra", "")
        valor = lic.get("valorTotalEstimado", 0)

        # Guard: PCP resumo muito curto
        if len(objeto) < 20:
            stats["llm_zero_match_skipped_short"] += 1
            return None

        is_relevant = classify_contract_primary_match(
            objeto=objeto,
            valor=valor,
            setor_name=setor_name,
            setor_id=setor_id,
            prompt_level="zero_match",
        )
        stats["llm_zero_match_calls"] += 1
        if is_relevant:
            lic["_relevance_source"] = "llm_zero_match"
            stats["llm_zero_match_aprovadas"] += 1
            return lic
        else:
            stats["llm_zero_match_rejeitadas"] += 1
            return None

    results = await asyncio.gather(*[classify_one(lic) for lic in resultado_llm_zero])
    resultado_densidade.extend([r for r in results if r is not None])
```

**Novo prompt zero_match em llm_arbiter.py:**
```python
def _build_zero_match_prompt(setor_id, setor_name, objeto_truncated, valor):
    from sectors import get_sector
    sector = get_sector(setor_id)
    top_kw = sorted(list(sector.keywords))[:5]
    top_exc = sorted(list(sector.exclusions))[:3]

    # AC4: PCP v2 valor=0.0 → "Não informado"
    valor_str = "Não informado" if valor == 0.0 else f"R$ {valor:,.2f}"

    return f"""Setor: {setor_name}
Descrição: {sector.description}

CONTRATO:
Valor: {valor_str}
Objeto: {objeto_truncated}

Exemplos de contratos RELEVANTES para {setor_name}:
{chr(10).join(f'- {kw}' for kw in top_kw)}

Exemplos de contratos NÃO relevantes:
{chr(10).join(f'- {exc}' for exc in top_exc)}

Este contrato é sobre {setor_name}?
Responda APENAS: SIM ou NAO"""
```

### Track 2: Frontend (AC12-AC16, AC27)

**Arquivos:**
- `frontend/app/buscar/components/SearchResults.tsx` — Badge "Validado por IA", nota de análise
- `frontend/app/components/EmptyState.tsx` — Mensagem revisada
- `frontend/types/` — Novo campo `relevance_source` no tipo LicitacaoItem

---

## Decisões Arquiteturais (@architect + @data-engineer)

### R1: Ponto de interceptação correto ✅
O keyword gate (linha ~2175) é onde bids são eliminados — não a Camada 2A. A Camada 2A opera sobre `resultado_keyword` que já está vazio. Fix: interceptar no `else` do keyword loop.

### R2: Async concurrency, não batching ✅
`max_tokens=1` força resposta single-token (SIM/NAO). Impossível fazer batching 10/prompt. Solução: `asyncio.Semaphore(10)` + `asyncio.gather()` para 10 chamadas paralelas.

### R3: Fallback = REJECT (zero ruído) ✅
Fallback INCLUDE contradiz a filosofia "zero ruído". Em outage da OpenAI, incluir TUDO inunda o usuário com ruído. Manter `return False` no except — consistente com o arbiter existente (linha 275).

### R4: PCP valor=0.0 → "Não informado" ✅
PCP v2 listing endpoint não retorna valor. Enviar "R$ 0,00" ao LLM confunde a classificação. Mostrar "Não informado" no prompt.

### R5: PCP resumo curto → skip LLM ✅
PCP `resumo` pode ter 3-10 palavras. Abaixo de 20 chars, sinal insuficiente para classificação LLM. Guard: skip + contabilizar em `llm_zero_match_skipped_short`.

### R6: FLUXO 2 overlap → desativar para zero_match ✅
FLUXO 2 (synonym recovery + `classify_contract_recovery()`) reprocessaria bids já classificados por zero_match, causando double-classification e custo duplicado. Solução: quando `LLM_ZERO_MATCH_ENABLED=true`, skip FLUXO 2 para bids no `resultado_llm_zero`.

---

## O que NÃO muda

- Filtros obrigatórios (UF, valor, modalidade, prazo) — eliminam normalmente
- Pipeline 7 stages — inalterada
- Keywords de setor — mantidas (pre-filter rápido para density > 5%)
- LLM arbiter zona 1-5% — inalterado (standard/conservative)
- Cache MD5 — inalterado (ampliado para cobrir zero_match)
- Endpoint schema — retrocompatível (campos novos são adicionais/opcionais)
- Feature flag `LLM_ARBITER_ENABLED` — inalterado
- Fallback LLM — mantém REJECT (zero ruído)

## O que muda

| Antes | Depois |
|-------|--------|
| 0 keyword matches → auto-reject | 0 keyword matches → LLM classifica |
| density < 1% → auto-reject | density < 1% → LLM conservative |
| 0 LLM calls quando keywords não casam | LLM chamado para TODA licitação sem match |
| "Nenhuma Oportunidade" quando keywords falham | "N resultados (M validados por IA)" |
| PCP valor=0.0 → "R$ 0,00" no prompt | PCP valor=0.0 → "Não informado" |
| FLUXO 2 recovery ativo sempre | FLUXO 2 desativado para zero_match bids |
| gpt-4o-mini | gpt-4.1-nano (33% mais barato) |
| LLM fallback = REJECT | LLM fallback = REJECT (inalterado — confirmado) |

---

## Definição de Done

- [ ] Nenhum dos 15 setores retorna "Nenhuma Oportunidade" quando PNCP tem dados
- [ ] LLM consultado para TODA licitação sem keyword match (exceto objeto < 20 chars)
- [ ] Licitações relevantes que antes eram invisíveis agora são exibidas
- [ ] Badge visual diferencia "keyword match" de "validado por IA"
- [ ] PCP bids com valor=0.0 recebem "Não informado" no prompt LLM
- [ ] FLUXO 2 não reprocessa bids já classificados por zero_match
- [ ] Custo LLM < R$ 5/mês por usuário (monitorar via FilterStats)
- [ ] Testes backend + frontend passam, zero regressão
- [ ] Validação em produção com ≥ 5 setores
