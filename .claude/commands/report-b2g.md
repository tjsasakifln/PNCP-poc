# /report-b2g — Relatório Executivo de Oportunidades B2G (Orchestrator)

## Purpose

Orquestra a geração de um relatório B2G completo delegando análise e auditoria a agentes isolados.

**Output:** `docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.pdf`

---

## Execution

### Step 1 — Parse CNPJ

Extrair CNPJ dos argumentos. Aceita `12.345.678/0001-90` ou `12345678000190`. Definir:
- `DATA_JSON=docs/reports/data-{CNPJ}-{YYYY-MM-DD}.json`
- `REPORT_PDF=docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.pdf`
- `REPORT_MD=docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.md`

### Step 2 — Phase 1: Coleta Determinística

**IMPORTANTE:** O script inicia pelo SICAF (captcha do navegador). Assim que o captcha for resolvido, o restante da coleta roda automaticamente sem interação.

```bash
cd D:/pncp-poc
python scripts/collect-report-data.py --cnpj {CNPJ} --dias 30 --output {DATA_JSON}
```

**NÃO passar `--ufs` manualmente.** O script deriva UFs do histórico de contratos.

Verificar output: quantos editais abertos? Alguma API falhou (`_metadata.sources`)?

### Step 2.5 — Investigação e Correção de Falhas de API (OBRIGATÓRIO)

**Ler `_metadata.sources` no JSON.** Para CADA fonte com `status != "API"`:

**NÃO ACEITAR API_FAILED.** O relatório DEVE ter dados completos. Se uma API falhou:

1. **Investigar a causa** usando WebSearch:
   - Buscar: `"{nome_da_api}" status 2026` ou `"{endpoint}" documentation`
   - Verificar se a API mudou URL, autenticação, formato ou rate limit
   - Ler documentação oficial da API

2. **Diagnosticar** — Executar a chamada manualmente via curl/httpx:
   ```bash
   curl -s "https://api.endpoint/..." | head -c 500
   ```
   Verificar: resposta vazia? JSON inválido? Mudou o schema? Rate limited?

3. **Corrigir** — Se a chamada está errada no script:
   - Corrigir `collect-report-data.py` (URL, headers, parâmetros)
   - Se API mudou autenticação, atualizar

4. **Re-executar coleta** da fonte específica ou completa:
   ```bash
   python scripts/collect-report-data.py --cnpj {CNPJ} --dias 30 --output {DATA_JSON}
   ```

5. **Se API genuinamente offline** (confirmado que não é erro nosso):
   - Buscar fonte alternativa para o mesmo dado
   - OpenCNPJ offline → usar BrasilAPI (já implementado como fallback)
   - Portal Transparência offline → consultar via browser Playwright no portal web
   - PNCP offline → usar PCP v2 como fonte primária
   - **SÓ APÓS esgotar TODAS alternativas**, registrar e informar ao usuário

**Filosofia:** O relatório é um produto premium. "Indisponível" NÃO EXISTE no vocabulário. Dados faltantes são BUGS a serem corrigidos, não estados aceitáveis.

### Step 3 — Phase 1.5: Gate Determinístico

```bash
python scripts/validate-report-data.py {DATA_JSON}
```

- **Exit 0 (OK):** Prosseguir.
- **Exit 2 (WARNINGS):** Anotar os alertas — o Analyst deve endereçar CADA UM.
- **Exit 1 (BLOCKED):** Executar Step 2.5 (investigar e corrigir). Re-executar validação. NÃO prosseguir enquanto houver BLOCK.

### Step 4 — Launch ANALYST Agent (Phases 2-5)

Criar subagente isolado para análise documental e estratégica:

```
TaskCreate(subagent_type="claude-router:deep-executor")
Prompt: Conteúdo de .claude/commands/report-b2g-analyst.md
Argumentos: DATA_JSON path + lista de WARNINGS (se houver)
```

O Analyst enriquece o JSON com: `analise_documental`, `analise_detalhada`, `recomendacao`, `justificativa`, `inteligencia_mercado`, `proximos_passos`, `resumo_executivo`.

O Analyst recebe os seguintes campos pré-computados pelo script (somente referência — não modificar):
- `editais[].acervo_status`, `acervo_detalhes` — Classificação do acervo técnico (CONFIRMADO/PARCIAL/NAO_VERIFICADO)
- `editais[].alertas_criticos` — Alertas críticos por edital com severidade e ações requeridas
- `editais[].price_benchmark` — Benchmarking histórico de preços (min/mediana/max/faixa sugerida)
- `editais[].habilitacao_checklist_25` — Checklist de habilitação de 25 itens em 5 categorias
- `editais[].win_probability.prob_min/prob_max` — Banda de confiança da probabilidade calibrada

**Após retorno:** Verificar que o JSON foi salvo e contém os campos obrigatórios.

**Se Analyst FALHAR** (timeout, context overflow, ou erro irrecuperável):
1. Tentar 1 re-lançamento com contexto reduzido.
2. Se falhar novamente → **Fallback Determinístico (GAP-H):**
   - Pular Steps 4.5, 5, 6 — ir direto ao Step 7 com flag `--deterministic-only`
   - PDF será gerado usando apenas scores determinísticos (risk_score, roi_potential, cronograma)
   - Banner "RELATÓRIO DETERMINÍSTICO" será incluído automaticamente
   - Informar usuário que análise qualitativa não foi possível

### Step 4.5 — Gate Pós-Enriquecimento (Programático)

**NOVO:** Validação programática entre Analyst e Auditor. Roda checks determinísticos + schema Pydantic automaticamente.

```bash
cd D:/pncp-poc
python scripts/validate-report-data.py {DATA_JSON} --post-enrichment
```

- **Exit 0 (OK):** Prosseguir para Step 5.
- **Exit 2 (WARNINGS):** Anotar os alertas. Se houver falhas em checks determinísticos (C6/C9), executar auto-fix:
  ```bash
  python scripts/auditor_deterministic_checks.py {DATA_JSON} --fix
  ```
- **Exit 1 (BLOCKED):** Re-lançar ANALYST com feedback: "O gate pós-enriquecimento bloqueou. Motivos: {blocks}. Corrigir e re-salvar JSON."

**Valor:** Captura erros óbvios (veto ignorado, MEI com valor alto, schema inválido) sem gastar tempo no Auditor LLM. ~2s vs ~60s.

### Step 5 — Launch AUDITOR Agent (Phase 7)

Criar subagente isolado para auditoria adversarial (NUNCA viu o processo do Analyst):

```
TaskCreate(subagent_type="claude-router:deep-executor")
Prompt: Conteúdo de .claude/commands/report-b2g-auditor.md
Argumentos: DATA_JSON path (já enriquecido pelo Analyst)
```

O Auditor executa checklist binário e escreve `delivery_validation` no JSON.

**Nota:** O Auditor agora valida 16 checks (eram 11) — inclui verificação de acervo, benchmarking de preços, cobertura de habilitação, menção de alertas críticos na narrativa, e sensibilidade da banda de probabilidade.

### Step 6 — Handle Auditor Result

Ler `delivery_validation.gate_adversarial` do JSON:

- **"PASSED":** Prosseguir para Step 7.
- **"REVISED":** Prosseguir (Auditor já aplicou rebaixamentos no JSON).
- **"BLOCKED":** Executar retry loop:
  1. Extrair `delivery_validation.block_reasons` do JSON.
  2. Re-lançar ANALYST com feedback: "O Auditor bloqueou o relatório. Motivos: {block_reasons}. Corrigir e re-enriquecer o JSON."
  3. Re-lançar AUDITOR no JSON corrigido.
  4. Se AINDA BLOCKED: prosseguir para Step 7 com flag `--partial-banner` (PDF incluirá banner "ANÁLISE PARCIAL — cobertura documental incompleta").

### Step 7 — Phase 6: Gerar PDF

```bash
cd D:/pncp-poc
python scripts/generate-report-b2g.py \
  --input {DATA_JSON} \
  --output {REPORT_PDF} \
  --save-json
```

Se flag `--partial-banner` ativo, adicionar: `--partial-banner`
Se flag `--deterministic-only` ativo (fallback do Step 4), adicionar: `--deterministic-only`

**Métricas:** O gerador grava automaticamente em `data/report_metrics.jsonl` (GAP-E).

### Step 8 — Gerar Markdown

Salvar versão markdown em `{REPORT_MD}` com resumo executivo + tabela de editais + recomendações.

### Step 9 — Report Results

Informar ao usuário:
- PDF gerado: `{REPORT_PDF}`
- JSON final: `{DATA_JSON}`
- Markdown: `{REPORT_MD}`
- Resultado do gate adversarial (PASSED/REVISED/BLOCKED+retry)
- Contagem: X PARTICIPAR, Y AVALIAR, Z NÃO RECOMENDADO

---

## GUARDRAILS — Regras do Orchestrator

1. O orchestrator NÃO realiza análise. Delega para agentes isolados.
2. NUNCA contornar um BLOCK do Gate Determinístico (Step 3).
3. Máximo 1 retry após BLOCK do Auditor. Após isso, gerar PDF parcial.
4. Verificar JSON entre steps — campos obrigatórios devem estar preenchidos.
5. Se o Analyst retornar JSON sem `recomendacao` ou `justificativa` em algum edital, rejeitar e re-executar.

## Params

$ARGUMENTS
