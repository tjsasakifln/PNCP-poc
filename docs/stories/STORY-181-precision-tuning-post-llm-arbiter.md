# STORY-181: Ajuste Fino de Precisão Pós-LLM Arbiter

**Status:** Rascunho
**Prioridade:** P0 - Crítica (impacta valor percebido do produto)
**Estimativa:** 5 story points (1 sprint)
**Tipo:** Enhancement (Brownfield)
**Épico:** Qualidade de Busca & Relevância
**Dependências:** STORY-179 (LLM Arbiter implementado)
**Criado por:** @pm (Morgan) baseado em teste manual em produção
**Data:** 2026-02-10

---

## Contexto

### Problema Identificado em Produção

**Teste manual realizado em 2026-02-10** revelou que, apesar da implementação do STORY-179 (LLM Arbiter com 4 camadas), **ainda ocorrem muitos resultados incoerentes com a busca**.

#### Dados do Teste Real

**Busca executada:**
- **Setor:** Vestuário e Uniformes
- **Estados:** PR, RS, SC (região Sul)
- **Período:** 03/02/2026 a 10/02/2026 (7 dias)
- **Resultados:** 58 licitações encontradas
- **Valor total:** R$ 55.412.850,11

#### Resultados Incoerentes Observados

Exemplos de contratos aprovados que NÃO são primariamente sobre vestuário/uniformes:

1. **"CONTRATAÇÃO DE EMPRESA ESPECIALIZADA PRESTADORA DE SERVIÇOS DE ORGANIZAÇÃO, PLANEJAMENTO E REALIZAÇÃO DE PROCESSO SELETIVO A SER..."**
   - Valor: R$ 35.260
   - **Problema:** Processo seletivo de RH, não tem relação com uniformes
   - **Provável causa:** Palavra "seletivo" matchou alguma variante ou foi mal classificado pelo LLM

2. **"Registro de Preços para a aquisição de Produtos para Saúde - Materiais de Assistência ao Paciente - Equip. de EPI: Luvas, Máscaras, Aventais, Macacões..."**
   - Valor: R$ 0 (registro de preços)
   - **Problema:** É prioritariamente material de saúde (EPIs hospitalares), não uniformes profissionais
   - **Provável causa:** Match em "Aventais" (que está em KEYWORDS_UNIFORMES), mas contexto é médico-hospitalar

3. **"Registro de preços para aquisição de Uniformes Personalizados para os servidores da Manutenção e Higienização da Secretaria Municipal da Saúde de Lages/SC"**
   - Valor: R$ 55.050
   - **Status:** ✅ RELEVANTE (este é um caso correto, baseline para comparação)

### Análise da Causa Raiz

**Por que o LLM Arbiter não está funcionando como esperado?**

| Hipótese | Evidência | Probabilidade |
|----------|-----------|---------------|
| **H1: Thresholds de densidade muito lenientes** | Contratos com 1-2 matches passam direto | Alta |
| **H2: LLM Arbiter não está sendo chamado** | Logs não mostram chamadas LLM na produção | Média |
| **H3: Prompt do LLM é ambíguo** | "Aventais hospitalares" pode ser interpretado como uniforme | Alta |
| **H4: Exclusões insuficientes** | Faltam exclusões para contextos médicos, RH, administrativos | Média |
| **H5: max_contract_value não configurado** | Contratos de baixo valor passam sem validação rigorosa | Baixa |
| **H6: Feature flag desabilitada** | `LLM_ARBITER_ENABLED=false` em produção | Baixa |

### Impacto no Negócio

**Score de qualidade percebida:**
- **Esperado:** 95% de precisão (promessa de marketing)
- **Real (teste manual):** ~70-75% de precisão (estimativa baseada em 58 resultados)
- **Delta:** -20-25 pontos percentuais

**Consequências:**
- 🔴 Usuários perdem confiança no sistema
- 🔴 Taxa de conversão de trial para pago cai
- 🔴 Churn aumenta ("se não filtra direito, não vale a pena")
- 🔴 Comparação com concorrentes fica negativa
- 🔴 NPS provavelmente < 5 se não corrigir

---

## Solução Proposta: Auditoria + Calibração + Melhorias Incrementais

### Princípio de Design

Não adicionar mais complexidade. Primeiro **diagnosticar por que STORY-179 não está funcionando como esperado**, depois **calibrar os controles existentes**, e apenas então **adicionar novas camadas se necessário**.

### Arquitetura de Solução (Faseada)

```
┌────────────────────────────────────────────────────────────┐
│ FASE 1: DIAGNÓSTICO (2 dias)                               │
│ • Adicionar logging detalhado em todas as camadas          │
│ • Instrumentar com trace_id para cada contrato             │
│ • Capturar decisões do LLM (prompt + response)             │
│ • Analisar logs de produção da busca real                  │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ FASE 2: CALIBRAÇÃO (3 dias)                                │
│ • Ajustar thresholds (term density, max_contract_value)    │
│ • Refinar prompt do LLM (mais específico sobre contexto)   │
│ • Adicionar exclusões contextuais (médico, RH, admin)      │
│ • Re-testar com dataset real (58 contratos)                │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ FASE 3: MELHORIAS (2-3 dias)                               │
│ • Implementar context-aware exclusions (STORY-179 AC1.2)   │
│ • Adicionar secondary keyword validation                   │
│ • Criar modo de auditoria (flag 10% das decisões para QA)  │
└────────────────────────────────────────────────────────────┘
```

---

## Acceptance Criteria

### AC1: Diagnóstico — Adicionar Logging Estruturado

**Objetivo:** Instrumentar o pipeline de filtros para entender por que contratos incoerentes estão passando.

- [ ] **AC1.1:** Adicionar `trace_id` único para cada contrato processado:
  ```python
  import uuid

  for lic in licitacoes:
      lic["_trace_id"] = str(uuid.uuid4())[:8]
      logger.debug(f"[{lic['_trace_id']}] Processando: {lic.get('objetoCompra', '')[:100]}")
  ```

- [ ] **AC1.2:** Logar decisões de cada camada do LLM Arbiter:
  ```python
  logger.info(
      f"[{trace_id}] Camada 1 (Value Threshold): "
      f"valor={valor:,.0f}, max={max_value:,.0f}, "
      f"decision={'REJECT' if rejected else 'PASS'}"
  )

  logger.info(
      f"[{trace_id}] Camada 2 (Term Density): "
      f"density={density:.2%}, matched_terms={matched_terms}, "
      f"decision={'ACCEPT' if density > HIGH else 'REJECT' if density < LOW else 'LLM_ARBITER'}"
  )

  logger.info(
      f"[{trace_id}] Camada 3 (LLM Arbiter): "
      f"prompt='{prompt[:200]}...', response='{response}', "
      f"decision={'ACCEPT' if response=='SIM' else 'REJECT'}, "
      f"cached={cached}"
  )
  ```

- [ ] **AC1.3:** Criar modo de debug detalhado via env var:
  ```bash
  FILTER_DEBUG_MODE=true  # Log TODOS os contratos, incluindo aprovados
  FILTER_DEBUG_SAMPLE=58  # Log apenas os primeiros N contratos
  ```

- [ ] **AC1.4:** Adicionar endpoint `/api/debug/filter-decision/<trace_id>`:
  - Retorna histórico de decisões de filtro para um contrato específico
  - Útil para investigar casos individuais em produção
  - Disponível apenas em modo dev/staging

- [ ] **AC1.5:** Coletar métricas por camada:
  ```python
  metrics = {
      "camada_1_value_threshold": {
          "chamadas": 58,
          "rejeitados": 5,
          "percentual_rejeicao": 8.6
      },
      "camada_2_term_density": {
          "alta_confianca": 40,  # density > 5%, aprovados sem LLM
          "baixa_confianca": 10,  # density < 1%, rejeitados sem LLM
          "duvidosos_llm": 8      # 1% <= density <= 5%, enviados ao LLM
      },
      "camada_3_llm_arbiter": {
          "chamadas": 8,
          "aprovados": 6,
          "rejeitados": 2,
          "cache_hits": 3,
          "custo_total": 0.00024  # R$
      }
  }
  ```

- [ ] **AC1.6:** Executar busca real em produção com logging ativado:
  - Setor: Vestuário e Uniformes
  - Estados: PR, RS, SC
  - Período: últimos 7 dias
  - Capturar logs completos
  - Analisar os 58 contratos retornados

- [ ] **AC1.7:** Identificar contratos problemáticos:
  - Listar todos os contratos aprovados que NÃO são primariamente sobre o setor
  - Para cada contrato problemático, identificar em qual camada passou
  - Classificar causas raiz (threshold leniente, LLM errou, exclusão faltando, etc.)

### AC2: Calibração — Ajustar Thresholds de Term Density

**Objetivo:** Tornar os thresholds de densidade de termos mais conservadores para reduzir falsos positivos.

- [ ] **AC2.1:** Analisar distribuição de densidades nos 58 contratos retornados:
  ```python
  # Pseudo-código de análise
  densities = [lic["_term_density"] for lic in results]
  print(f"P10: {percentile(densities, 0.10):.2%}")
  print(f"P50: {percentile(densities, 0.50):.2%}")
  print(f"P90: {percentile(densities, 0.90):.2%}")

  # Classificar contratos por densidade e relevância manual
  for lic in sorted(results, key=lambda x: x["_term_density"]):
      relevant = input(f"Densidade {lic['_term_density']:.2%} - Relevante? (s/n): ")
      # Encontrar threshold ótimo
  ```

- [ ] **AC2.2:** Propor novos thresholds baseados em dados reais:

  **Thresholds atuais (STORY-179):**
  - `TERM_DENSITY_HIGH_THRESHOLD = 0.05` (5%)
  - `TERM_DENSITY_LOW_THRESHOLD = 0.01` (1%)

  **Thresholds propostos (ajustados):**
  - `TERM_DENSITY_HIGH_THRESHOLD = 0.08` (8%) — mais conservador, reduz auto-aprovações
  - `TERM_DENSITY_LOW_THRESHOLD = 0.02` (2%) — mais conservador, mais casos vão para LLM

  **Justificativa:** Aumentar o limiar de "alta confiança" força mais contratos a passarem pelo LLM, reduzindo falsos positivos.

- [ ] **AC2.3:** Adicionar threshold intermediário para "média confiança":
  ```python
  TERM_DENSITY_HIGH = 0.08      # > 8%: aceitar sem LLM
  TERM_DENSITY_MEDIUM = 0.03    # 3-8%: LLM com prompt standard
  TERM_DENSITY_LOW = 0.01       # < 1%: rejeitar sem LLM
  # 1-3%: LLM com prompt CONSERVADOR (ver AC3.2)
  ```

- [ ] **AC2.4:** Casos de teste com novos thresholds:
  - Densidade 10% → ACEITAR sem LLM ✓
  - Densidade 5% → LLM com prompt standard ✓
  - Densidade 1.5% → LLM com prompt conservador ✓
  - Densidade 0.5% → REJEITAR sem LLM ✓

### AC3: Calibração — Refinar Prompt do LLM Arbiter

**Objetivo:** Tornar o prompt mais específico e menos ambíguo para reduzir erros de classificação.

- [ ] **AC3.1:** Prompt atual (STORY-179) — MUITO GENÉRICO:
  ```
  Setor: Vestuário e Uniformes
  Valor: R$ {valor}
  Objeto: {objeto}

  Este contrato é PRIMARIAMENTE sobre Vestuário e Uniformes?
  Responda APENAS: SIM ou NAO
  ```

- [ ] **AC3.2:** Novo prompt — CONSERVADOR com contexto e exemplos:
  ```
  Você é um classificador de licitações públicas. Analise se o contrato é PRIMARIAMENTE sobre o setor especificado (> 80% do valor e escopo).

  SETOR: Vestuário e Uniformes
  DESCRIÇÃO DO SETOR: Aquisição de uniformes, fardas, roupas profissionais para servidores, estudantes, agentes públicos. NÃO inclui EPIs médicos (aventais hospitalares, luvas, máscaras).

  CONTRATO:
  Valor: R$ {valor:,.2f}
  Objeto: {objeto[:500]}

  EXEMPLOS DE CLASSIFICAÇÃO:

  ✅ SIM:
  - "Uniformes escolares para rede municipal"
  - "Fardamento para guardas municipais"
  - "Camisas polo e calças para agentes de trânsito"

  ❌ NAO:
  - "Material de saúde incluindo aventais hospitalares e luvas"
  - "Processo seletivo para contratação de servidores"
  - "Obra de infraestrutura com fornecimento de uniformes para operários"

  Este contrato é PRIMARIAMENTE sobre Vestuário e Uniformes?
  Responda APENAS: SIM ou NAO
  ```

- [ ] **AC3.3:** Criar dois níveis de prompt (baseado em densidade):

  **Prompt STANDARD (densidade 3-8%):**
  - Versão atual, resumida
  - Custo: 1 token

  **Prompt CONSERVADOR (densidade 1-3%):**
  - Versão expandida com exemplos (AC3.2)
  - Custo: 3-5 tokens
  - Usado apenas para casos limítrofes

- [ ] **AC3.4:** A/B test com 20 contratos ambíguos:
  - 10 contratos com prompt atual
  - 10 contratos com prompt refinado
  - Comparar precisão (classificação manual como ground truth)
  - Escolher prompt com maior F1-score

- [ ] **AC3.5:** Adicionar system message mais restritivo:
  ```python
  system_message = (
      "Você é um classificador conservador de licitações. "
      "Em caso de dúvida, responda NAO. "
      "Apenas responda SIM se o contrato é CLARAMENTE e PRIMARIAMENTE sobre o setor."
  )
  ```

### AC4: Melhorias — Context-Required Keywords (Exclusões Contextuais)

**Objetivo:** Implementar exclusões contextuais já previstas no STORY-179 AC1.2 mas não completamente implementadas.

- [ ] **AC4.1:** Adicionar exclusões contextuais para setor "Vestuário e Uniformes":
  ```python
  # backend/sectors.py
  SectorConfig(
      id="vestuario",
      name="Vestuário e Uniformes",
      keywords=KEYWORDS_UNIFORMES,
      exclusions=KEYWORDS_EXCLUSAO,
      context_required_keywords={
          # Se "avental" aparece, exigir pelo menos UM destes:
          "avental": {"uniforme", "fardamento", "vestuário", "escolar", "profissional"},
          "jaleco": {"uniforme", "escolar", "profissional", "vestuário"},
          # Se "processo" aparece, rejeitar se também tem "seletivo" ou "licitatorio"
          "processo": set(),  # Empty = auto-reject if no positive context
      },
      # ...
  )
  ```

- [ ] **AC4.2:** Implementar lógica de validação contextual em `filter.py`:
  ```python
  def validate_context_required(
      objeto_norm: str,
      matched_terms: Set[str],
      context_required: Dict[str, Set[str]]
  ) -> Tuple[bool, Optional[str]]:
      """
      Validate that matched terms appear in valid context.

      Returns:
          (is_valid, rejection_reason)
      """
      for term, required_context in context_required.items():
          if term in matched_terms:
              if not required_context:  # Empty set = auto-reject
                  return False, f"termo '{term}' sem contexto válido"

              # Check if at least ONE required context term is present
              has_context = any(ctx in objeto_norm for ctx in required_context)
              if not has_context:
                  return False, f"termo '{term}' sem contexto requerido: {required_context}"

      return True, None
  ```

- [ ] **AC4.3:** Casos de teste:
  - "Aventais hospitalares para UTI" + vestuario → REJEITADO (sem contexto "uniforme") ✓
  - "Aventais escolares uniformes" + vestuario → APROVADO (tem contexto "escolar"+"uniformes") ✓
  - "Processo seletivo RH" + vestuario → REJEITADO (termo "processo" sem contexto positivo) ✓

### AC5: Melhorias — Adicionar Exclusões Específicas

**Objetivo:** Expandir `KEYWORDS_EXCLUSAO` com termos identificados no teste manual.

- [ ] **AC5.1:** Adicionar exclusões para contextos médicos/saúde:
  ```python
  # backend/filter.py — KEYWORDS_EXCLUSAO

  # Contexto médico-hospitalar (EPI != uniforme profissional)
  "epi",
  "epis",
  "equipamento de protecao individual",
  "assistencia ao paciente",
  "material hospitalar",
  "material de saude",
  "uti",
  "unidade de terapia intensiva",
  "centro cirurgico",
  "ambulatorio",
  "pronto-socorro",
  ```

- [ ] **AC5.2:** Adicionar exclusões para contextos administrativos/RH:
  ```python
  # Contexto RH/Administrativo
  "processo seletivo",
  "selecao de pessoal",
  "recrutamento",
  "contratacao de pessoal",
  "concurso publico",
  "teste seletivo",
  "avaliacao de candidatos",
  ```

- [ ] **AC5.3:** Adicionar exclusões para contextos de obras/engenharia:
  ```python
  # Contexto obras (uniformes de operários são secundários)
  "obra de infraestrutura",
  "obra de pavimentacao",
  "obra de drenagem",
  "obra de saneamento",
  "execucao de obra",
  "servicos de engenharia",
  ```

- [ ] **AC5.4:** Casos de teste:
  - "Material de saúde EPI aventais luvas" + vestuario → REJEITADO por "epi" exclusion ✓
  - "Processo seletivo para contratação" + vestuario → REJEITADO por "processo seletivo" exclusion ✓

### AC6: Melhorias — Secondary Keyword Validation

**Objetivo:** Para contratos que passaram na primeira validação, verificar se termos secundários invalidam a classificação.

- [ ] **AC6.1:** Após aprovação por keyword matching, verificar "red flags":
  ```python
  RED_FLAGS_MEDICAL = {
      "paciente", "hospitalar", "ambulatorial", "medicamento",
      "cirurgico", "diagnóstico", "tratamento", "terapia"
  }

  RED_FLAGS_ADMINISTRATIVE = {
      "processo licitatorio", "processo administrativo",
      "auditoria", "consultoria", "assessoria", "capacitacao"
  }

  def has_red_flags(objeto_norm: str, red_flag_sets: List[Set[str]]) -> bool:
      for red_flags in red_flag_sets:
          matches = sum(1 for flag in red_flags if flag in objeto_norm)
          if matches >= 2:  # 2+ red flags = provável falso positivo
              return True
      return False
  ```

- [ ] **AC6.2:** Integrar após Camada 2 (antes do LLM):
  ```python
  if term_density >= LOW and term_density <= HIGH:
      # Check red flags before sending to expensive LLM
      if has_red_flags(objeto_norm, [RED_FLAGS_MEDICAL, RED_FLAGS_ADMINISTRATIVE]):
          logger.info(f"[{trace_id}] REJECTED by red flags before LLM")
          stats["rejeitadas_red_flags"] += 1
          continue

      # Proceed to LLM arbiter...
  ```

- [ ] **AC6.3:** Casos de teste:
  - "Uniformes e material hospitalar para pacientes" → RED FLAGS: "hospitalar", "pacientes" → REJEITADO ✓
  - "Uniformes escolares" → Sem red flags → Prossegue normalmente ✓

### AC7: Auditoria — Modo de Amostragem para QA Manual

**Objetivo:** Flaggar 10% das decisões do LLM para revisão manual e calibração contínua.

- [ ] **AC7.1:** Adicionar flag `_qa_audit` em X% dos contratos:
  ```python
  import random

  QA_AUDIT_SAMPLE_RATE = float(os.getenv("QA_AUDIT_SAMPLE_RATE", "0.10"))  # 10%

  if random.random() < QA_AUDIT_SAMPLE_RATE:
      lic["_qa_audit"] = True
      lic["_qa_audit_decision"] = {
          "trace_id": trace_id,
          "llm_response": llm_response,
          "density": term_density,
          "matched_terms": matched_terms,
          "timestamp": datetime.utcnow().isoformat(),
      }
  ```

- [ ] **AC7.2:** Endpoint para QA revisar decisões auditadas:
  ```
  GET /api/admin/qa-audit?status=pending

  Response:
  [
      {
          "trace_id": "a3f5b2c8",
          "objeto": "...",
          "valor": 35260,
          "llm_decision": "SIM",
          "density": 0.035,
          "timestamp": "2026-02-10T15:30:00Z",
          "qa_review": null  // Pending review
      }
  ]
  ```

- [ ] **AC7.3:** Interface de revisão (admin panel):
  - [ ] Mostrar contrato completo
  - [ ] Mostrar decisão do LLM
  - [ ] Botões: "Correto" / "Incorreto (Falso Positivo)" / "Incorreto (Falso Negativo)"
  - [ ] Campo de comentários
  - [ ] Salvar em `qa_audits` table

- [ ] **AC7.4:** Métricas de qualidade:
  ```python
  qa_metrics = {
      "total_auditados": 50,
      "corretos": 42,
      "falsos_positivos": 6,
      "falsos_negativos": 2,
      "precisao_llm": 84.0,  # 42/50
      "taxa_falso_positivo": 12.0,  # 6/50
  }
  ```

### AC8: Testes de Regressão com Dataset Real

**Objetivo:** Garantir que as calibrações melhoram a precisão sem quebrar casos que já funcionavam.

- [ ] **AC8.1:** Criar dataset de teste com os 58 contratos reais:
  - [ ] Classificação manual: RELEVANTE / IRRELEVANTE
  - [ ] Ground truth salvo em `backend/tests/fixtures/dataset_story181.json`

- [ ] **AC8.2:** Teste de regressão:
  ```python
  def test_precision_with_real_dataset():
      # Load 58 real contracts
      contracts = load_fixture("dataset_story181.json")

      # Run filter pipeline
      results, stats = aplicar_todos_filtros(...)

      # Calculate metrics
      tp = sum(1 for c in results if c["_ground_truth"] == "RELEVANTE")
      fp = sum(1 for c in results if c["_ground_truth"] == "IRRELEVANTE")
      fn = sum(1 for c in contracts if c["_ground_truth"] == "RELEVANTE" and c not in results)

      precision = tp / (tp + fp)
      recall = tp / (tp + fn)
      f1 = 2 * precision * recall / (precision + recall)

      # Thresholds
      assert precision >= 0.90, f"Precisão {precision:.2%} abaixo de 90%"
      assert recall >= 0.85, f"Recall {recall:.2%} abaixo de 85%"
      assert f1 >= 0.87, f"F1 {f1:.2%} abaixo de 87%"
  ```

- [ ] **AC8.3:** Comparar métricas ANTES vs DEPOIS das calibrações:

  | Métrica | Baseline (STORY-179) | Target (STORY-181) |
  |---------|---------------------|-------------------|
  | Precisão | ~75% (estimado) | ≥ 90% |
  | Recall | ~85% (estimado) | ≥ 85% |
  | F1-Score | ~80% (estimado) | ≥ 87% |

### AC9: Documentação e Rollout

- [ ] **AC9.1:** Documentar processo de calibração:
  - [ ] Como executar diagnóstico em produção
  - [ ] Como ajustar thresholds baseado em métricas
  - [ ] Como adicionar novas exclusões contextuais

- [ ] **AC9.2:** Criar runbook para análise de qualidade:
  ```markdown
  # Runbook: Análise de Qualidade de Busca

  ## Quando executar:
  - Mensalmente (manutenção preventiva)
  - Após reclamações de usuários sobre resultados incoerentes
  - Após adicionar novo setor

  ## Passos:
  1. Habilitar `FILTER_DEBUG_MODE=true` em staging
  2. Executar busca representativa (setor + UFs + 7 dias)
  3. Coletar logs e analisar decisões
  4. Identificar contratos problemáticos
  5. Ajustar thresholds/exclusões conforme AC2-AC5
  6. Re-testar com dataset de regressão (AC8)
  7. Deploy em produção se métricas > 90% precisão
  ```

- [ ] **AC9.3:** Atualizar `.env.example` com novas variáveis:
  ```bash
  # Filter Debugging & QA
  FILTER_DEBUG_MODE=false
  FILTER_DEBUG_SAMPLE=0  # 0 = disabled
  QA_AUDIT_SAMPLE_RATE=0.10  # 10% das decisões para QA

  # Term Density Thresholds (calibrated)
  TERM_DENSITY_HIGH_THRESHOLD=0.08  # 8%
  TERM_DENSITY_MEDIUM_THRESHOLD=0.03  # 3%
  TERM_DENSITY_LOW_THRESHOLD=0.01  # 1%
  ```

---

## Arquivos Impactados

| Arquivo | Mudança | Risco | Blast Radius |
|---------|---------|-------|-------------|
| `backend/filter.py` | Logging, thresholds, context validation, red flags | Médio | Core filtering logic |
| `backend/llm_arbiter.py` | Prompt refinement, dual-level prompts | Baixo | LLM calling logic |
| `backend/sectors.py` | `context_required_keywords` config | Baixo | Sector definitions |
| `backend/config.py` | Novas env vars (thresholds, debug mode) | Baixo | Configuration |
| `backend/tests/test_filter_llm.py` | Testes com dataset real (58 contratos) | — | — |
| `backend/tests/fixtures/dataset_story181.json` | **NOVO** — Ground truth dataset | — | — |
| `backend/main.py` | Endpoint `/api/debug/filter-decision` | Baixo | Admin endpoints |
| `docs/runbooks/qualidade-busca.md` | **NOVO** — Runbook de calibração | — | — |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Thresholds mais conservadores aumentam falsos negativos | Média | Médio | Monitorar recall, ajustar se cair < 85% |
| Prompt mais longo aumenta custo LLM | Baixa | Baixo | Usar prompt conservador apenas para 1-3% (minority) |
| Exclusões contextuais muito agressivas | Média | Médio | Testar com dataset de regressão, rollback se recall cai |
| Red flags rejeitam contratos legítimos | Baixa | Médio | Threshold de 2+ matches, não 1 |
| QA audit 10% sobrecarrega equipe | Média | Baixo | Automatizar dashboard, revisar apenas casos duvidosos |

---

## Definição de Pronto (DoD)

- [ ] Todos os ACs (1-9) marcados como ✅
- [ ] **Diagnóstico executado** com logging detalhado em produção
- [ ] **Thresholds calibrados** baseados em dados reais (AC2)
- [ ] **Prompt refinado** com A/B test mostrando melhoria (AC3)
- [ ] **Exclusões contextuais** implementadas e testadas (AC4-AC5)
- [ ] **Red flags** implementados e validados (AC6)
- [ ] **QA audit mode** funcional com endpoint admin (AC7)
- [ ] **Teste de regressão** com 58 contratos reais passando:
  - [ ] Precisão ≥ 90%
  - [ ] Recall ≥ 85%
  - [ ] F1-Score ≥ 87%
- [ ] **Testes existentes** não regridem (backend + frontend)
- [ ] **Code review** aprovado por @architect + @dev
- [ ] **Teste manual em produção:**
  - [ ] Busca vestuário + Sul + 7 dias retorna < 5 contratos irrelevantes
  - [ ] Contratos problemáticos identificados no teste inicial NÃO aparecem
- [ ] **Documentação** atualizada (runbook, .env.example)
- [ ] **Monitoramento** configurado:
  - [ ] Taxa de precisão (TP / TP+FP)
  - [ ] Taxa de recall (TP / TP+FN)
  - [ ] Distribuição de densidades
  - [ ] Taxa de chamadas LLM por camada

---

## Ordem de Execução Sugerida

### Sprint Week 1

**Dias 1-2: Diagnóstico**
1. AC1 — Logging estruturado e diagnóstico
2. Executar busca real em produção com logs
3. Análise dos 58 contratos (classificação manual)

**Dias 3-4: Calibração**
4. AC2 — Ajustar thresholds de densidade
5. AC3 — Refinar prompt do LLM
6. AC8 — Criar dataset de regressão

**Dia 5: Melhorias**
7. AC4 — Context-required keywords
8. AC5 — Adicionar exclusões específicas

### Sprint Week 2 (opcional, se necessário)

**Dias 1-2: Melhorias Avançadas**
9. AC6 — Secondary keyword validation (red flags)
10. AC7 — QA audit mode

**Dias 3-4: Validação**
11. AC8 — Testes de regressão completos
12. Teste manual em produção (E2E)

**Dia 5: Documentação**
13. AC9 — Runbook e rollout

---

## Métricas de Sucesso

### Métricas Primárias

| Métrica | Baseline | Target | Como Medir |
|---------|----------|--------|------------|
| **Precisão** | 75% | ≥ 90% | TP / (TP + FP) |
| **Recall** | 85% | ≥ 85% | TP / (TP + FN) |
| **F1-Score** | 80% | ≥ 87% | 2 × (P × R) / (P + R) |

### Métricas Secundárias

| Métrica | Baseline | Target | Como Medir |
|---------|----------|--------|------------|
| Taxa de chamadas LLM | ~15% | 10-20% | `llm_calls / total_contracts` |
| Custo LLM por busca | ~R$ 0,001 | < R$ 0,003 | `llm_calls × cost_per_call` |
| Latência P95 de busca | ~2min | < 2.5min | CloudWatch P95 |

### Métricas de Negócio (Impacto)

| Métrica | Baseline | Target (3 meses) | Como Medir |
|---------|----------|-----------------|------------|
| NPS | ? | > 8 | Survey pós-busca |
| Taxa de conversão trial → pago | ? | +15% | Analytics |
| Churn rate | ? | -20% | Billing data |
| Reclamações de "resultados irrelevantes" | 10/mês (est.) | < 2/mês | Support tickets |

---

## Notas de Implementação

### NI-1: Por que Diagnóstico é Prioridade P0?

Não adianta adicionar mais camadas de complexidade se não sabemos POR QUE as camadas existentes estão falhando. O diagnóstico (AC1) é **bloqueador** para as demais melhorias.

Possíveis descobertas:
- LLM não está sendo chamado (bug ou feature flag off)
- Thresholds lenientes demais
- Prompt ambíguo
- Exclusões insuficientes

Sem diagnóstico, estamos atirando no escuro.

### NI-2: Trade-off Precisão vs Recall

Ao tornar os thresholds mais conservadores (AC2), corremos o risco de aumentar falsos negativos (reduzir recall). Monitorar ambas as métricas é crítico.

**Estratégia de mitigação:**
- Se recall cair < 80% após calibração → rollback thresholds
- Se precisão ainda < 85% → investigar outras causas (prompt, exclusões)

### NI-3: Prompt Conservador vs Custo

O prompt conservador (AC3.2) com exemplos aumenta custo de 1 token para 3-5 tokens (5× mais caro). Por isso, usar apenas para casos limítrofes (densidade 1-3%).

**Estimativa de impacto:**
- 80% dos contratos: sem LLM (densidade fora de 1-8%)
- 15% dos contratos: LLM com prompt standard (densidade 3-8%)
- 5% dos contratos: LLM com prompt conservador (densidade 1-3%)

Custo mensal (10.000 contratos):
- Baseline: R$ 0,50
- Com prompt conservador: R$ 0,65 (+30%)
- Ainda irrisório comparado ao valor do produto

### NI-4: QA Audit como Feedback Loop

O modo de auditoria (AC7) não é apenas para encontrar bugs, mas para **calibrar continuamente** o sistema. Cada revisão manual alimenta:
- Novos casos de teste
- Ajustes de thresholds
- Novas exclusões
- Refinamento de prompts

**Processo recomendado:**
1. Revisar 10% das decisões semanalmente
2. Se precisão LLM < 85% → refinar prompt
3. Se 3+ falsos positivos do mesmo tipo → adicionar exclusão
4. Iterar mensalmente

---

## Aprovações

- [x] **@pm (Morgan):** Aprovado — Story criada baseada em teste manual
- [ ] **@po (Product Owner):** Aguardando aprovação
- [ ] **@architect (Aria):** Aguardando aprovação
- [ ] **@dev:** Aguardando aprovação
- [ ] **@qa:** Aguardando aprovação
- [ ] **@analyst:** Aguardando aprovação

**Status:** RASCUNHO — Aguardando revisão do squad.

---

## Anexos

### Anexo A: Dados do Teste Manual (2026-02-10)

**Busca executada:**
- Setor: Vestuário e Uniformes
- Estados: PR, RS, SC
- Período: 03/02 a 10/02/2026
- Resultados: 58 licitações
- Valor total: R$ 55.412.850,11

**Contratos problemáticos identificados:**

1. **Processo seletivo RH** (R$ 35.260)
   - Objeto: "CONTRATAÇÃO DE EMPRESA ESPECIALIZADA PRESTADORA DE SERVIÇOS DE ORGANIZAÇÃO, PLANEJAMENTO E REALIZAÇÃO DE PROCESSO SELETIVO A SER..."
   - **Causa provável:** Match em alguma palavra genérica, LLM não detectou contexto de RH

2. **Material de saúde/EPI** (R$ 0)
   - Objeto: "Registro de Preços para a aquisição de Produtos para Saúde - Materiais de Assistência ao Paciente - Equip. de EPI: Luvas, Máscaras, Aventais, Macacões..."
   - **Causa provável:** Match em "Aventais", mas contexto é claramente médico

3. **[Adicionar mais casos conforme análise dos logs]**

### Anexo B: Prompt Atual vs Proposto

**ATUAL (STORY-179):**
```
Setor: Vestuário e Uniformes
Valor: R$ {valor}
Objeto: {objeto}

Este contrato é PRIMARIAMENTE sobre Vestuário e Uniformes?
Responda APENAS: SIM ou NAO
```
- Tokens: ~80 input, 1 output
- Custo: R$ 0,00003

**PROPOSTO (STORY-181 — Conservador):**
```
Você é um classificador de licitações públicas. Analise se o contrato é PRIMARIAMENTE sobre o setor especificado (> 80% do valor e escopo).

SETOR: Vestuário e Uniformes
DESCRIÇÃO DO SETOR: Aquisição de uniformes, fardas, roupas profissionais para servidores, estudantes, agentes públicos. NÃO inclui EPIs médicos (aventais hospitalares, luvas, máscaras).

CONTRATO:
Valor: R$ {valor:,.2f}
Objeto: {objeto[:500]}

EXEMPLOS DE CLASSIFICAÇÃO:

✅ SIM:
- "Uniformes escolares para rede municipal"
- "Fardamento para guardas municipais"
- "Camisas polo e calças para agentes de trânsito"

❌ NAO:
- "Material de saúde incluindo aventais hospitalares e luvas"
- "Processo seletivo para contratação de servidores"
- "Obra de infraestrutura com fornecimento de uniformes para operários"

Este contrato é PRIMARIAMENTE sobre Vestuário e Uniformes?
Responda APENAS: SIM ou NAO
```
- Tokens: ~350 input, 1 output
- Custo: R$ 0,00015 (5× mais caro)
- **Usado apenas para 5% dos contratos (densidade 1-3%)**

---

**Fim da Story 181**
