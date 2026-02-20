# STORY-179: LLM Arbiter para Eliminação de Falsos Positivos e Falsos Negativos

**Status:** Aprovada
**Prioridade:** P0 - Crítica (impacta credibilidade do produto)
**Estimativa:** 8 story points (1 sprint)
**Tipo:** Enhancement (Brownfield)
**Épico:** Qualidade de Busca & Relevância
**Dependências:** STORY-178 (Filtragem Inteligente por Termos)
**Aprovado por:** @po (Business Owner)

---

## Contexto

### Problema Crítico Identificado

> **Caso Real:** Busca por setor "Vestuário e Uniformes" retornou contrato de **R$ 47,6 milhões** para "melhorias urbanas" (infraestrutura) em Niterói. O resumo LLM indicou erroneamente como "oportunidade significativa para uniformes ou vestuário".

**Impacto:** Destrói completamente a confiança do usuário no sistema.

### Análise da Causa Raiz

**Cenário típico:**
- **Contrato principal:** R$ 47,6M para infraestrutura urbana (pavimentação, drenagem, sinalização)
- **Item secundário:** R$ 50K-500K para uniformes de agentes de trânsito (< 1% do valor total)
- **Match atual:** "fornecimento de uniformes" → keyword match → APROVADO ❌
- **Problema:** O contrato é 99% engenharia civil, 1% uniformes

**Por que keyword matching falha:**
- Keywords corretas: "fornecimento de uniformes" É mencionado no texto
- Exclusões insuficientes: Impossível listar infinitos contextos para 12+ setores
- Sem análise de proporção: Não distingue objeto principal de item secundário

### Limitações da Solução por Exclusões

| Problema | Impacto |
|----------|---------|
| **12 setores × infinitos contextos** | Explosão combinatória |
| **Manutenção insustentável** | Cada falso positivo = nova exclusão manual |
| **Whack-a-mole** | Resolver um problema cria outro |
| **Conflito entre setores** | "Drenagem" é exclusão em vestuário, mas keyword em facilities |

**Conclusão do PO:** "Se a saída for por keywords de exclusão fica um negócio sem fim."

### Problema 2: Falsos Negativos (Contratos Relevantes Rejeitados)

**Cenários típicos de falsos negativos:**

| Cenário | Causa | Impacto |
|---------|-------|---------|
| **Exclusão over-zealous** | "Servidor público" rejeita contrato de servidores de TI | Perde oportunidade legítima de R$ 500K |
| **Context mismatch** | "Obra" rejeita manutenção predial (facilities) | Perde contrato de R$ 2M de conservação |
| **Keyword near-miss** | "Farda policial" não matcha "uniforme" (synonym) | Perde oportunidade de uniformes militares |
| **Multi-sector ambiguity** | "Material de limpeza e mobiliário" rejeitado em ambos setores por conflict | Perde contrato misto legítimo |

**Exemplos reais:**
1. **Busca "facilities"** → Contrato "Obra de manutenção predial preventiva" rejeitado por exclusão "obra"
2. **Busca "informática"** → Contrato "Aquisição de servidores para secretaria" rejeitado por exclusão "servidor público"
3. **Busca "vestuário"** → Contrato "Fardamento para guardas municipais" não matcha "uniforme"

**Impacto:** Usuário perde oportunidades reais, diminui valor percebido do produto.

---

## Solução Proposta: Arquitetura Híbrida de 4 Camadas (Bidirecional)

### Princípio de Design

Combinar **heurísticas rápidas e baratas** (90% dos casos) com **LLM ultra-barato como árbitro bidirecional** (10% dos casos duvidosos) para eliminar TANTO falsos positivos QUANTO falsos negativos.

```
┌──────────────────────────────────────────────────────────────────┐
│ FLUXO 1: ANTI-FALSO POSITIVO (Contratos Aprovados por Keywords) │
└──────────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ CAMADA 1A: Value Threshold                            │
│ • Custo: R$ 0,00                                       │
│ • Tempo: 0.1ms                                         │
│ • Lógica: valor > max_value do setor → REJEITAR       │
│ • Exemplo: R$ 47.6M "melhorias urbanas" + vestuário   │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ CAMADA 2A: Dominant Term Ratio                        │
│ • Custo: R$ 0,00                                       │
│ • Tempo: 1ms                                           │
│ • Lógica: term_density = matches / total_words        │
│   - density > 5%: ACEITAR (alta confiança)             │
│   - density < 1%: REJEITAR (baixa confiança)           │
│   - 1% ≤ density ≤ 5%: DÚVIDA → Camada 3A             │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ CAMADA 3A: LLM Arbiter - False Positive Check         │
│ • Prompt: "É PRIMARIAMENTE sobre {setor/termos}?"     │
│ • Response: "NAO" → REJEITAR (era FP!)                 │
└────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ FLUXO 2: ANTI-FALSO NEGATIVO (Contratos Rejeitados)             │
└──────────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ CAMADA 1B: Exclusion Recovery Candidates              │
│ • Custo: R$ 0,00                                       │
│ • Tempo: 0.5ms                                         │
│ • Lógica: Rejeitados por EXCLUSION + alta densidade   │
│   - Rejected by exclusion keyword                      │
│   - BUT term_density > 3% (sinal de relevância)       │
│   → Candidato a recovery → Camada 3B                   │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ CAMADA 2B: Synonym/Variant Matching                   │
│ • Custo: R$ 0,00                                       │
│ • Tempo: 2ms                                           │
│ • Lógica: Termos similares que não matcharam          │
│   - "fardamento" ≈ "uniforme"                          │
│   - "manutenção predial" ≈ "conservação"               │
│   - Semantic distance < threshold → Camada 3B          │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ CAMADA 3B: LLM Arbiter - False Negative Recovery      │
│ • Prompt: "Este contrato REJEITADO é relevante para   │
│            {setor/termos}?"                            │
│ • Response: "SIM" → RECUPERAR (era FN!)                │
│ • Custo: R$ 0,00003/contrato (~R$ 0,60/mês produção)  │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ CAMADA 4: Zero Results Relaxation                     │
│ • Se 0 resultados após todos os filtros:              │
│   1. Relaxar minimum match floor (STORY-178)          │
│   2. Pegar top 20 contratos rejeitados por densidade  │
│   3. LLM avalia cada um: "Relevante? SIM/NAO"          │
│   4. Retornar até 5 recuperados com warning ao usuário│
└────────────────────────────────────────────────────────┘
```

### Estimativa de Custo (Produção)

**Cenário:** 10.000 contratos processados/mês

**FLUXO 1 (Anti-Falso Positivo):**
- **Camada 1A:** 30% rejeitados → 7.000 restantes → **R$ 0,00**
- **Camada 2A:** 60% decididos → 2.800 restantes → **R$ 0,00**
- **Camada 3A (LLM):** 2.800 chamadas × R$ 0,00003 → **R$ 0,084/mês**

**FLUXO 2 (Anti-Falso Negativo):**
- **Camada 1B:** 5% dos rejeitados são recovery candidates → 500 contratos → **R$ 0,00**
- **Camada 2B:** 80% resolvidos por synonym matching → 100 restantes → **R$ 0,00**
- **Camada 3B (LLM):** 100 chamadas × R$ 0,00003 → **R$ 0,003/mês**
- **Camada 4:** ~2% buscas retornam 0 resultados → 200 chamadas × R$ 0,00003 → **R$ 0,006/mês**

**Total mensal:** ~**R$ 0,50/mês** (custo irrisório para eliminar falsos positivos E negativos)

---

## Acceptance Criteria

### AC1: Camada 1 — Value Threshold por Setor

- [ ] **AC1.1:** Adicionar campo `max_contract_value` em `SectorConfig` (`sectors.py`)

  ```python
  @dataclass(frozen=True)
  class SectorConfig:
      id: str
      name: str
      description: str
      keywords: Set[str]
      exclusions: Set[str] = field(default_factory=set)
      context_required_keywords: Dict[str, Set[str]] = field(default_factory=dict)
      max_contract_value: Optional[int] = None  # NEW: R$ threshold
  ```

- [ ] **AC1.2:** Configurar thresholds iniciais por setor:

  | Setor | max_contract_value | Justificativa |
  |-------|-------------------|---------------|
  | vestuario | R$ 5.000.000 | Maior contrato municipal ~R$ 3M |
  | alimentos | R$ 10.000.000 | Merenda escolar grande: R$ 5-8M |
  | informatica | R$ 20.000.000 | Datacenter grande: R$ 15M |
  | facilities | R$ 30.000.000 | Limpeza predial multi-ano: R$ 20-25M |
  | mobiliario | R$ 8.000.000 | Mobiliário escolar estadual: R$ 5-6M |
  | saude | R$ 50.000.000 | Equipamentos hospitalares: R$ 30-40M |
  | engenharia | None | Sem limite (obras podem ser bilionárias) |
  | transporte | R$ 100.000.000 | Frota de ônibus municipal: R$ 80M |
  | vigilancia | R$ 40.000.000 | Segurança predial multi-ano: R$ 30M |

- [ ] **AC1.3:** Integrar em `aplicar_todos_filtros()` antes do keyword matching:
  ```python
  if setor and setor.max_contract_value:
      if valor > setor.max_contract_value:
          stats["rejeitadas_valor_alto"] += 1
          continue
  ```

- [ ] **AC1.4:** Casos de teste:
  - R$ 47,6M "melhorias urbanas com uniformes" + setor=vestuario → REJEITADO ✓
  - R$ 3M "uniformes escolares" + setor=vestuario → APROVADO ✓
  - R$ 10M "software" + setor=informatica → APROVADO ✓

### AC2: Camada 2 — Dominant Term Ratio

- [ ] **AC2.1:** Calcular densidade de termos no objeto:
  ```python
  matched_terms = lic.get("_matched_terms", [])
  total_words = len(objeto.split())
  term_count = sum(objeto.lower().count(t.lower()) for t in matched_terms)
  term_density = term_count / total_words if total_words > 0 else 0
  ```

- [ ] **AC2.2:** Aplicar thresholds de decisão:
  - **density > 5%:** ACEITAR (alta confiança, termo dominante)
  - **density < 1%:** REJEITAR (baixa confiança, termo periférico)
  - **1% ≤ density ≤ 5%:** DÚVIDA → prosseguir para Camada 3

- [ ] **AC2.3:** Adicionar stats:
  ```python
  stats["aprovadas_alta_densidade"] = 0  # density > 5%
  stats["rejeitadas_baixa_densidade"] = 0  # density < 1%
  stats["duvidosas_llm_arbiter"] = 0  # 1% ≤ density ≤ 5%
  ```

- [ ] **AC2.4:** Casos de teste:
  - "Uniformes escolares diversos para rede municipal" (20 palavras)
    - Matches: "uniformes" (aparece 3×)
    - Density: 3/20 = 15% > 5% → ACEITAR sem LLM ✓
  - "Melhorias urbanas [...100 palavras...] incluindo uniformes"
    - Matches: "uniformes" (aparece 1×)
    - Density: 1/100 = 1% → LIMIAR → LLM arbiter ✓

### AC3: Camada 3 — LLM Arbiter (GPT-4o-mini)

- [ ] **AC3.1:** Criar módulo `backend/llm_arbiter.py`:
  ```python
  def classify_contract_primary_match(
      objeto: str,
      valor: float,
      setor_name: Optional[str] = None,
      termos_busca: Optional[list[str]] = None,
  ) -> bool:
      """
      Use GPT-4o-mini to determine if contract is PRIMARILY about criteria.

      Two modes:
      1. With sector: Check if primarily about SECTOR
      2. Without sector: Check if primarily about CUSTOM TERMS
      """
  ```

- [ ] **AC3.2:** Prompt para modo SETOR (user selecionou setor):
  ```
  Setor: {setor_name}
  Valor: R$ {valor:,.2f}
  Objeto: {objeto[:500]}

  Este contrato é PRIMARIAMENTE sobre {setor_name}?
  Responda APENAS: SIM ou NAO
  ```

- [ ] **AC3.3:** Prompt para modo TERMOS CUSTOM (user NÃO selecionou setor):
  ```
  Termos buscados: {termos_busca}
  Valor: R$ {valor:,.2f}
  Objeto: {objeto[:500]}

  Os termos buscados descrevem o OBJETO PRINCIPAL deste contrato (não itens secundários)?
  Responda APENAS: SIM ou NAO
  ```

- [ ] **AC3.4:** Configuração GPT-4o-mini:
  - Model: `gpt-4o-mini`
  - Max tokens: `1` (força resposta "SIM" ou "NAO")
  - Temperature: `0` (determinístico)
  - System prompt: "Você é um classificador de licitações. Responda APENAS 'SIM' ou 'NAO'."

- [ ] **AC3.5:** Cache de decisões (in-memory):
  ```python
  _arbiter_cache: dict[str, bool] = {}
  cache_key = hashlib.md5(f"{mode}:{context}:{valor}:{objeto}".encode()).hexdigest()
  ```

- [ ] **AC3.6:** Fallback se LLM falhar:
  ```python
  except Exception as e:
      logger.error(f"LLM arbiter failed: {e}. Defaulting to REJECT.")
      return False  # Conservador: rejeita se incerto
  ```

- [ ] **AC3.7:** Truncar objeto para 500 chars (economizar tokens):
  ```python
  objeto_truncated = objeto[:500]
  ```

- [ ] **AC3.8:** Casos de teste:

  **Teste 1: Setor vestuário + contrato misto**
  ```
  Input:
    setor_name = "Vestuário e Uniformes"
    valor = 47_600_000
    objeto = "MELHORIAS URBANAS [...] incluindo uniformes para agentes"

  Expected LLM response: "NAO"
  Expected result: REJEITADO ✓
  ```

  **Teste 2: Termos custom engenharia + contrato relevante**
  ```
  Input:
    termos_busca = ["pavimentação", "drenagem", "terraplenagem"]
    valor = 5_000_000
    objeto = "Execução de pavimentação e drenagem na Rodovia X"

  Expected LLM response: "SIM"
  Expected result: APROVADO ✓
  ```

  **Teste 3: Termos custom + contrato irrelevante**
  ```
  Input:
    termos_busca = ["pavimentação", "drenagem"]
    valor = 10_000_000
    objeto = "Auditoria externa de processos administrativos"

  Expected LLM response: "NAO"
  Expected result: REJEITADO ✓
  ```

### AC4: Integração em `aplicar_todos_filtros()`

- [ ] **AC4.1:** Ordem de aplicação das camadas:
  ```python
  # 1. UF, status, esfera, modalidade, município, órgão (filtros existentes)
  # 2. Keyword matching (existente)
  # 3. CAMADA 1: Value threshold (NOVO)
  # 4. CAMADA 2: Term density (NOVO)
  # 5. CAMADA 3: LLM arbiter (NOVO)
  ```

- [ ] **AC4.2:** Passar `termos_busca` para o filter pipeline:
  ```python
  def aplicar_todos_filtros(
      licitacoes: List[dict],
      ufs_selecionadas: Set[str],
      termos_busca: Optional[List[str]] = None,  # NEW
      # ... outros params existentes ...
  ) -> Tuple[List[dict], Dict[str, int]]:
  ```

- [ ] **AC4.3:** Lógica de decisão da Camada 3:
  ```python
  if term_density >= 0.01 and term_density <= 0.05:  # Zona duvidosa
      if setor:
          is_primary = classify_contract_primary_match(
              objeto=objeto,
              valor=valor,
              setor_name=setor.name,
          )
      elif termos_busca:
          is_primary = classify_contract_primary_match(
              objeto=objeto,
              valor=valor,
              termos_busca=termos_busca,
          )
      else:
          is_primary = True  # Sem setor nem termos, aceita

      if is_primary:
          resultado_final.append(lic)
          stats["aprovadas_llm_arbiter"] += 1
      else:
          stats["rejeitadas_llm_arbiter"] += 1
  ```

### AC5: Estatísticas e Observabilidade

- [ ] **AC5.1:** Novos campos em response stats:
  ```python
  {
      "total": int,
      "aprovadas": int,

      # FLUXO 1 (Anti-Falso Positivo)
      "aprovadas_alta_densidade": int,      # Camada 2A (density > 5%)
      "aprovadas_llm_fp_check": int,        # Camada 3A (LLM=SIM, não é FP)
      "rejeitadas_valor_alto": int,         # Camada 1A (valor > max_value)
      "rejeitadas_baixa_densidade": int,    # Camada 2A (density < 1%)
      "rejeitadas_llm_fp": int,             # Camada 3A (LLM=NAO, era FP!)

      # FLUXO 2 (Anti-Falso Negativo)
      "recuperadas_exclusion_recovery": int,  # Camada 1B → 3B (LLM recovery)
      "aprovadas_synonym_match": int,         # Camada 2B (synonym sem LLM)
      "recuperadas_llm_fn": int,              # Camada 3B (LLM=SIM, FN recuperado)
      "recuperadas_zero_results": int,        # Camada 4 (relaxamento)
      "rejeitadas_llm_fn_confirmed": int,     # Camada 3B (LLM=NAO, rejeição válida)

      # Agregados
      "llm_arbiter_calls_total": int,       # Total de chamadas LLM (FP + FN)
      "llm_arbiter_calls_fp_flow": int,     # Chamadas FLUXO 1
      "llm_arbiter_calls_fn_flow": int,     # Chamadas FLUXO 2
      "llm_arbiter_cache_hits": int,        # Cache hits total
      "zero_results_relaxation_triggered": bool,  # Se houve relaxamento

      # ... campos existentes (UF, keyword, status, etc.) ...
  }
  ```

- [ ] **AC5.2:** Logging estruturado:
  ```python
  logger.info(
      f"Camada 1 (value threshold): {rejeitadas_valor_alto} rejeitadas"
  )
  logger.info(
      f"Camada 2 (term density): {aprovadas_alta_densidade} aceitas, "
      f"{rejeitadas_baixa_densidade} rejeitadas"
  )
  logger.info(
      f"Camada 3 (LLM arbiter): {llm_calls} chamadas, "
      f"{cache_hits} cache hits, {aprovadas_llm} aceitas"
  )
  ```

- [ ] **AC5.3:** Métrica de custo em logs:
  ```python
  custo_estimado = llm_calls * 0.00003  # R$ por chamada
  logger.info(f"Custo LLM arbiter nesta busca: R$ {custo_estimado:.5f}")
  ```

### AC6: Variáveis de Ambiente

- [ ] **AC6.1:** Adicionar em `.env.example`:
  ```bash
  # LLM Arbiter Configuration
  OPENAI_API_KEY=sk-...  # Já existe
  LLM_ARBITER_ENABLED=true  # Feature flag
  LLM_ARBITER_MODEL=gpt-4o-mini  # Model name
  LLM_ARBITER_MAX_TOKENS=1  # Output limit
  LLM_ARBITER_TEMPERATURE=0  # Deterministic

  # Thresholds (podem ser ajustados sem código)
  TERM_DENSITY_HIGH_THRESHOLD=0.05  # 5% = alta confiança
  TERM_DENSITY_LOW_THRESHOLD=0.01   # 1% = baixa confiança
  ```

- [ ] **AC6.2:** Carregar em `config.py`:
  ```python
  LLM_ARBITER_ENABLED = os.getenv("LLM_ARBITER_ENABLED", "true").lower() == "true"
  LLM_ARBITER_MODEL = os.getenv("LLM_ARBITER_MODEL", "gpt-4o-mini")
  TERM_DENSITY_HIGH = float(os.getenv("TERM_DENSITY_HIGH_THRESHOLD", "0.05"))
  TERM_DENSITY_LOW = float(os.getenv("TERM_DENSITY_LOW_THRESHOLD", "0.01"))
  ```

- [ ] **AC6.3:** Feature flag bypass:
  ```python
  if not LLM_ARBITER_ENABLED:
      # Fallback: aceita contratos duvidosos (comportamento antigo)
      logger.warning("LLM arbiter disabled, accepting ambiguous contracts")
      is_primary = True
  ```

### AC7: Testes

- [ ] **AC7.1:** Testes unitários — `backend/tests/test_llm_arbiter.py`:
  - Mock OpenAI API responses
  - Test cache hit/miss
  - Test fallback on API error
  - Test prompt construction (setor vs termos)
  - Test token counting (max 1 token output)

- [ ] **AC7.2:** Testes de integração — `backend/tests/test_filter_llm.py`:
  - Caso real: R$ 47.6M melhorias urbanas + vestuário → REJEITADO
  - Caso legítimo: R$ 3M uniformes escolares + vestuário → APROVADO
  - Casos limítrofes (density 1%-5%) → LLM chamado
  - Casos sem LLM (density > 5% ou < 1%) → LLM NÃO chamado

- [ ] **AC7.3:** Testes de custo:
  - Simular 1000 contratos
  - Verificar que < 15% resultam em chamadas LLM
  - Verificar custo total < R$ 0,01 para 1000 contratos

- [ ] **AC7.4:** Coverage ≥ 85%** para `llm_arbiter.py` e alterações em `filter.py`

### AC8: Documentação

- [ ] **AC8.1:** Atualizar `PRD.md` com nova arquitetura de 3 camadas

- [ ] **AC8.2:** Criar `docs/architecture/llm-arbiter.md` com:
  - Diagrama de fluxo das 3 camadas
  - Análise de custo detalhada
  - Guia de calibração de thresholds
  - FAQ para troubleshooting

- [ ] **AC8.3:** Atualizar API docs (OpenAPI/Swagger) com novos campos de stats

- [ ] **AC8.4:** Adicionar comentários no código explicando a lógica de cada camada

### AC9: Performance

- [ ] **AC9.1:** Latência P95 de busca aumenta < 100ms (vs baseline sem LLM)
  - 90% dos contratos decididos em Camadas 1-2 (< 2ms)
  - 10% com LLM: ~50ms cada

- [ ] **AC9.2:** Cache de LLM arbiter:
  - Hit rate > 80% em buscas repetidas
  - Considerar migração para Redis em produção (não nesta story)

- [ ] **AC9.3:** Benchmark com 10.000 contratos:
  - Tempo total < 5 segundos (vs ~3s baseline)
  - Chamadas LLM < 1.500 (15%)

### AC10: Migração de Dados

- [ ] **AC10.1:** Nenhuma migração de banco necessária (apenas código)

- [ ] **AC10.2:** Seeded initial `max_contract_value` para setores existentes (AC1.2)

- [ ] **AC10.3:** Documentar processo de ajuste de thresholds pós-deploy baseado em métricas reais

### AC11: FLUXO 2 — Camada 1B: Exclusion Recovery Candidates

- [ ] **AC11.1:** Identificar contratos rejeitados por keyword de EXCLUSÃO:
  ```python
  # Durante keyword matching, track rejection reason
  match, matched_terms, rejection_reason = match_keywords_extended(...)

  if not match and rejection_reason == "exclusion":
      lic["_rejection_reason"] = "exclusion"
      lic["_matched_before_exclusion"] = matched_terms_before_exclusion
      rejeitados_por_exclusao.append(lic)
  ```

- [ ] **AC11.2:** Calcular densidade de termos matchados ANTES da exclusão:
  ```python
  for lic in rejeitados_por_exclusao:
      matched_terms = lic.get("_matched_before_exclusion", [])
      total_words = len(objeto.split())
      term_count = sum(objeto.lower().count(t.lower()) for t in matched_terms)
      density = term_count / total_words if total_words > 0 else 0
      lic["_term_density_pre_exclusion"] = density
  ```

- [ ] **AC11.3:** Selecionar candidatos a recovery:
  ```python
  recovery_candidates = []
  for lic in rejeitados_por_exclusao:
      # High density DESPITE exclusion = might be false negative
      if lic.get("_term_density_pre_exclusion", 0) > 0.03:  # 3% threshold
          recovery_candidates.append(lic)
  ```

- [ ] **AC11.4:** Passar candidatos para LLM Arbiter (Camada 3B):
  ```python
  recovered = []
  for lic in recovery_candidates:
      is_relevant = classify_contract_recovery(
          objeto=lic.get("objetoCompra"),
          valor=lic.get("valorTotalEstimado"),
          setor_name=setor.name if setor else None,
          termos_busca=termos_busca,
          rejection_reason=lic.get("_rejection_reason"),
      )
      if is_relevant:
          recovered.append(lic)
          stats["recuperadas_exclusion_recovery"] += 1
  ```

- [ ] **AC11.5:** Casos de teste:
  - "Obra de manutenção predial preventiva" + facilities → Rejeitado por "obra" exclusion
    - Density antes exclusão: 15% ("manutenção", "predial" matcham)
    - LLM: "Manutenção predial é relevante para facilities? SIM"
    - → RECUPERADO ✓

### AC12: FLUXO 2 — Camada 2B: Synonym/Variant Matching

- [ ] **AC12.1:** Criar dicionário de sinônimos por setor:
  ```python
  # backend/synonyms.py (NOVO)
  SECTOR_SYNONYMS = {
      "vestuario": {
          "uniforme": ["fardamento", "farda", "indumentária"],
          "jaleco": ["guarda-pó", "avental hospitalar"],
          "camisa": ["camisa polo", "camiseta", "blusa"],
      },
      "facilities": {
          "limpeza": ["asseio", "higienização", "zeladoria"],
          "conservação": ["manutenção predial", "preservação"],
      },
      # ... outros setores ...
  }
  ```

- [ ] **AC12.2:** Detectar near-misses (termos similares que não matcharam):
  ```python
  from difflib import SequenceMatcher

  def find_synonym_matches(objeto, setor_keywords, setor_synonyms):
      objeto_norm = normalize_text(objeto)
      near_misses = []

      for keyword in setor_keywords:
          if keyword not in objeto_norm:
              # Check synonyms
              for synonym in setor_synonyms.get(keyword, []):
                  if normalize_text(synonym) in objeto_norm:
                      near_misses.append((keyword, synonym))

      return near_misses
  ```

- [ ] **AC12.3:** Auto-aprovar se synonym match + alta densidade:
  ```python
  near_misses = find_synonym_matches(objeto, setor.keywords, SECTOR_SYNONYMS[setor.id])

  if len(near_misses) >= 2:  # 2+ synonyms matched
      # Add to approved without LLM (high confidence)
      stats["aprovadas_synonym_match"] += 1
      resultado_final.append(lic)
  elif len(near_misses) == 1:
      # Ambiguous, send to LLM for validation
      → Camada 3B
  ```

- [ ] **AC12.4:** Casos de teste:
  - "Fardamento para guardas municipais" + vestuario (keyword: "uniforme")
    - Direct match: NO
    - Synonym match: "fardamento" ≈ "uniforme" → YES
    - → APROVADO sem LLM ✓

### AC13: FLUXO 2 — Camada 3B: LLM Arbiter Recovery

- [ ] **AC13.1:** Prompt para avaliação de contratos rejeitados:
  ```
  Este contrato foi REJEITADO automaticamente por: {rejection_reason}

  Setor: {setor_name}
  Valor: R$ {valor}
  Objeto: {objeto}

  Apesar da rejeição automática, este contrato é RELEVANTE para {setor_name}?
  Responda APENAS: SIM ou NAO
  ```

- [ ] **AC13.2:** Prompt para near-miss synonym validation:
  ```
  Termos buscados: {termos_busca}
  Objeto: {objeto}
  Sinônimos encontrados: {near_miss_synonyms}

  Os sinônimos indicam que este contrato é relevante para a busca?
  Responda APENAS: SIM ou NAO
  ```

- [ ] **AC13.3:** Integrar em `llm_arbiter.py`:
  ```python
  def classify_contract_recovery(
      objeto: str,
      valor: float,
      rejection_reason: str,
      setor_name: Optional[str] = None,
      termos_busca: Optional[list[str]] = None,
      near_miss_info: Optional[str] = None,
  ) -> bool:
      """
      Use LLM to determine if a REJECTED contract should be RECOVERED.
      """
  ```

- [ ] **AC13.4:** Casos de teste:
  - Contrato rejeitado: "Servidor de rede para secretaria" + informatica
    - Rejection: "servidor público" exclusion
    - LLM: "Servidor de rede é TI? SIM"
    - → RECUPERADO ✓

### AC14: FLUXO 2 — Camada 4: Zero Results Relaxation

- [ ] **AC14.1:** Detectar busca com 0 resultados após todos os filtros:
  ```python
  if len(resultado_final) == 0:
      logger.warning(
          f"Zero results after all filters. Attempting relaxation..."
      )
      stats["zero_results_relaxation_triggered"] = True
  ```

- [ ] **AC14.2:** Relaxamento progressivo:
  ```python
  # Step 1: Relaxar minimum match floor (STORY-178)
  if min_match_floor and min_match_floor > 1:
      min_match_floor_relaxed = 1
      resultado_relaxed, _ = aplicar_filtros_com_floor(
          licitacoes, min_match_floor=1
      )
      if len(resultado_relaxed) > 0:
          logger.info(f"Relaxation recovered {len(resultado_relaxed)} results")

  # Step 2: Se ainda 0, pegar rejeitados por baixa densidade
  if len(resultado_relaxed) == 0:
      candidatos = sorted(
          rejeitados_baixa_densidade,
          key=lambda x: x.get("_term_density", 0),
          reverse=True
      )[:20]  # Top 20 por densidade
  ```

- [ ] **AC14.3:** LLM avalia candidatos de relaxamento:
  ```python
  recovered_from_zero = []
  for lic in candidatos[:20]:  # Max 20 para não explodir custo
      is_relevant = classify_contract_primary_match(...)
      if is_relevant:
          recovered_from_zero.append(lic)
          if len(recovered_from_zero) >= 5:
              break  # Retornar max 5 recuperados
  ```

- [ ] **AC14.4:** Warning ao usuário:
  ```python
  if stats.get("zero_results_relaxation_triggered"):
      response["warning"] = (
          "Sua busca retornou 0 resultados com filtros estritos. "
          "Mostrando resultados relaxados (menor correspondência)."
      )
      response["relaxed_results"] = True
  ```

- [ ] **AC14.5:** Casos de teste:
  - Busca muito específica: "projeto executivo de sondagem geotécnica SPT"
    - Resultado com filtros estritos: 0
    - Relaxamento: pega contratos com "projeto" + "sondagem"
    - LLM valida: 2 de 20 são relevantes
    - → Retorna 2 com warning ✓

---

## Arquivos Impactados

| Arquivo | Mudança | Risco | Blast Radius |
|---------|---------|-------|-------------|
| `backend/llm_arbiter.py` | **NOVO** — LLM classification (FP + FN) | Baixo | Isolado, feature flag |
| `backend/synonyms.py` | **NOVO** — Synonym dictionaries per sector | Baixo | Isolado |
| `backend/sectors.py` | Adicionar `max_contract_value` em `SectorConfig` | Baixo | Additive only |
| `backend/filter.py` | Integrar 4 camadas (anti-FP + anti-FN) | Médio-Alto | Core filtering logic |
| `backend/main.py` | Passar `termos_busca`, tracking rejections | Médio | Additive param + logic |
| `backend/config.py` | Novas env vars (thresholds, feature flags) | Baixo | Config only |
| `.env.example` | Documentar novas vars | Baixo | Documentation |
| `backend/tests/test_llm_arbiter.py` | **NOVO** — Unit tests (FP + FN flows) | — | — |
| `backend/tests/test_filter_llm.py` | **NOVO** — Integration tests | — | — |
| `backend/tests/test_synonyms.py` | **NOVO** — Synonym matching tests | — | — |
| `docs/architecture/llm-arbiter.md` | **NOVO** — Arquitetura 4 camadas | — | — |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **FLUXO 1 (Anti-FP)** | | | |
| LLM rejeita contratos legítimos | Média | Alto | Feature flag para desabilitar; logging detalhado; FLUXO 2 recovery |
| Value threshold muito conservador | Média | Médio | Iteração pós-deploy; ajustar max_value por setor |
| **FLUXO 2 (Anti-FN)** | | | |
| Recovery recupera falsos positivos | Baixa | Médio | LLM prompt enfatiza "APESAR da rejeição"; logging para análise |
| Synonym dictionary incompleto | Alta | Baixo | Manutenção incremental; usuários reportam near-misses |
| Zero results relaxation muito agressivo | Média | Médio | Limitar a 5 recuperados; clear warning ao usuário |
| **GERAL** | | | |
| Custo LLM > estimado | Baixa | Baixo | Monitorar CloudWatch; FLUXO 2 usa < 20% calls vs FLUXO 1 |
| Latência aumenta > 100ms | Baixa | Médio | Cache agressivo; batch processing futuro |
| OpenAI API instável | Baixa | Médio | Fallback: FP → rejeita, FN → não recupera |
| Thresholds iniciais incorretos | Alta | Médio | Iteração pós-deploy com métricas reais |

---

## Definição de Pronto (DoD)

- [ ] Todos os ACs (1-14) marcados como ✅
- [ ] Testes passando (backend) — incluindo FP + FN flows
- [ ] Coverage dos novos módulos ≥ 85% (`llm_arbiter.py`, `synonyms.py`, alterações em `filter.py`)
- [ ] Testes existentes não regridem (0 novos failures vs baseline)
- [ ] Code review aprovado por @architect e @dev
- [ ] **Testado manualmente — FLUXO 1 (Anti-FP):**
  - [ ] Caso real: R$ 47.6M "melhorias urbanas" + vestuário → REJEITADO ✓
  - [ ] Caso legítimo: R$ 3M "uniformes escolares" + vestuário → APROVADO ✓
- [ ] **Testado manualmente — FLUXO 2 (Anti-FN):**
  - [ ] Exclusion recovery: "Manutenção predial" + facilities (rejeitado por "obra") → RECUPERADO ✓
  - [ ] Synonym match: "Fardamento militar" + vestuário (keyword "uniforme") → APROVADO ✓
  - [ ] Zero results: Busca muito específica sem resultados → Relaxamento funciona ✓
- [ ] Documentação de API atualizada (novos campos: `recuperadas_*`, `synonym_matches`, etc.)
- [ ] Feature flags testadas:
  - [ ] `LLM_ARBITER_ENABLED=false` → Fallback funciona
  - [ ] `SYNONYM_MATCHING_ENABLED=false` → Bypass funciona
  - [ ] `ZERO_RESULTS_RELAXATION=false` → Retorna 0 sem relaxar
- [ ] Monitoramento configurado:
  - [ ] Custo LLM (FP + FN separados)
  - [ ] Latência P95 (< 150ms aumento total)
  - [ ] Taxa de recovery (FN recuperados / total rejeitados)
  - [ ] False negative rate (contratos relevantes ainda rejeitados)

---

## Ordem de Execução Sugerida

### Fase 1: FLUXO 1 (Anti-Falso Positivo) — Sprint Week 1

1. **AC1** — Value Threshold (fundação, sem LLM)
2. **AC2** — Term Density (segunda camada, sem LLM)
3. **AC7** — Testes unitários de mock (prepara estrutura)
4. **AC3** — LLM Arbiter FP Check (Camada 3A)
5. **AC6** — Env vars e feature flags
6. **AC5** — Stats e observabilidade (parcial)

### Fase 2: FLUXO 2 (Anti-Falso Negativo) — Sprint Week 2

7. **AC12** — Synonym Matching (Camada 2B, sem LLM)
8. **AC11** — Exclusion Recovery (Camada 1B)
9. **AC13** — LLM Recovery (Camada 3B)
10. **AC14** — Zero Results Relaxation (Camada 4)
11. **AC4** — Integração completa (FP + FN pipelines)
12. **AC5** — Stats completas (incluindo FN metrics)

### Fase 3: Finalização — Sprint Week 2-3

13. **AC7.2-AC7.4** — Testes de integração e custo
14. **AC8** — Documentação completa
15. **AC9** — Performance benchmarks (FP + FN flows)
16. **AC10** — Migração (seed thresholds)

---

## Configuração

Variáveis de ambiente (ver AC6):

```bash
# Feature flag
LLM_ARBITER_ENABLED=true

# OpenAI
OPENAI_API_KEY=sk-...
LLM_ARBITER_MODEL=gpt-4o-mini
LLM_ARBITER_MAX_TOKENS=1
LLM_ARBITER_TEMPERATURE=0

# Thresholds (ajustáveis)
TERM_DENSITY_HIGH_THRESHOLD=0.05  # 5%
TERM_DENSITY_LOW_THRESHOLD=0.01   # 1%
```

---

## Notas de Implementação

### NI-1: Calibração de Thresholds

Os valores iniciais (R$ 5M vestuário, R$ 10M alimentos, etc.) são ESTIMATIVAS baseadas em conhecimento de mercado. Após deploy em produção:

1. Coletar métricas por 1 semana
2. Analisar distribuição de valores por setor
3. Identificar falsos positivos residuais
4. Ajustar `max_contract_value` se necessário

**Processo:**
```sql
-- Query para análise (pseudo-SQL)
SELECT setor,
       PERCENTILE(valor, 0.95) as p95,
       PERCENTILE(valor, 0.99) as p99,
       MAX(valor) as max
FROM contratos_aprovados
GROUP BY setor
```

### NI-2: Cache Strategy

**Fase 1 (esta story):** In-memory dict (suficiente para MVP)

**Fase 2 (futuro):** Migrar para Redis quando:
- Volume > 10.000 contratos/dia
- Múltiplas instâncias de backend (horizontal scaling)
- Cache hit rate < 70%

### NI-3: Prompt Engineering

O prompt atual é MINIMALISTA para economizar tokens. Se precisão < 90%, considerar versões mais elaboradas:

**Versão atual (1-shot, zero context):**
```
Este contrato é PRIMARIAMENTE sobre {setor}?
Responda APENAS: SIM ou NAO
```

**Versão melhorada (few-shot, com contexto):**
```
Você classifica licitações. Responda SIM se o contrato é PRIMARIAMENTE sobre o setor (>80% do valor), NAO se é item secundário.

Exemplo 1:
Objeto: Uniformes escolares diversos
Setor: Vestuário
Resposta: SIM

Exemplo 2:
Objeto: Obra de pavimentação incluindo uniformes para agentes
Setor: Vestuário
Resposta: NAO

Agora classifique:
Objeto: {objeto}
Setor: {setor}
Resposta:
```

**Trade-off:** Few-shot aumenta tokens (custo 3×), mas pode aumentar precisão.

### NI-4: Fallback em Caso de Falha do LLM

Se OpenAI API falhar (timeout, rate limit, etc.):

```python
except Exception as e:
    logger.error(f"LLM arbiter failed: {e}")
    return False  # REJEITA (conservador)
```

**Justificativa:** É melhor REJEITAR 1 contrato duvidoso do que APROVAR 1 falso positivo catastrófico (R$ 47.6M).

**Alternativa (se muito conservador):** Aceitar e logar para análise manual posterior.

### NI-5: Multi-Sector Contracts

Alguns contratos são LEGITIMAMENTE multi-setor:

**Exemplo:**
```
"Aquisição de uniformes, material de limpeza e mobiliário escolar"
Valor: R$ 2.000.000
```

**Decisão atual:** Mostrar no PRIMEIRO setor que matchou (vestuário).

**Melhoria futura (não nesta story):** Calcular score para TODOS os setores, mostrar nos TOP 2 se score é similar.

---

## Changelog da Story

| Data | Versão | Mudanças |
|------|--------|----------|
| 2026-02-09 | v1.0 | Criação inicial — foco em falsos positivos |
| 2026-02-09 | v2.0 | **Escopo expandido:** Falsos Positivos + Falsos Negativos<br>- Adicionado FLUXO 2 (Anti-FN) com 4 camadas<br>- AC11: Exclusion Recovery<br>- AC12: Synonym Matching<br>- AC13: LLM Recovery<br>- AC14: Zero Results Relaxation<br>- Estimativa: 5 → 8 story points |

---

## Aprovações

- [x] **@po (Product Owner):** Aprovado — "Na condição de business owner aprovo a solução"
- [x] **@data-engineer (Dara):** Aprovado — Propôs solução escalável
- [ ] **@architect (Aria):** Aguardando aprovação
- [ ] **@dev:** Aguardando aprovação
- [ ] **@qa:** Aguardando aprovação
- [ ] **@analyst:** Aguardando aprovação
- [ ] **@sm:** Aguardando aprovação

**Status:** APROVADO pelo PO, aguardando consenso técnico do squad.
