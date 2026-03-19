# /intel-busca — Inteligencia Estrategica de Editais por CNPJ

## Purpose

Busca exaustiva e analise profunda de editais abertos no PNCP para um CNPJ especifico.
Zero ruido. Zero perda de oportunidades. Zero incerteza no relatorio.
Utiliza TODOS os CNAEs da empresa (principal + secundarios) para maxima cobertura.

**Entregaveis:**
1. `docs/intel/intel-{CNPJ}-{razao-slug}-{YYYY-MM-DD}.xlsx` — Planilha completa com TODOS os editais (inclui distancia, custo, ROI)
2. `docs/intel/intel-{CNPJ}-{razao-slug}-{YYYY-MM-DD}.pdf` — Relatorio estrategico dos top 20 RECOMENDADOS (max 15 paginas)

**Principio:** O relatorio e fonte de CLAREZA, nunca de duvida. Cada gate tem autonomia para demandar reexecucao de etapas anteriores.

---

## Execution

### Step 1 — Parse Input

Extrair CNPJ e UFs dos argumentos ($ARGUMENTS).
Aceita formatos:
- `12.345.678/0001-90 SC,PR,RS`
- `12345678000190 SC PR RS`
- `--cnpj 12345678000190 --ufs SC,PR,RS`

Definir variaveis:
- `CNPJ` = 14 digitos limpos
- `UFS` = lista de UF siglas (uppercase)
- `DATA_JSON = docs/intel/intel-{CNPJ}-{razao-social-slug}-{YYYY-MM-DD}.json`
- `EXCEL_FILE = docs/intel/intel-{CNPJ}-{razao-social-slug}-{YYYY-MM-DD}.xlsx`
- `PDF_FILE = docs/intel/intel-{CNPJ}-{razao-social-slug}-{YYYY-MM-DD}.pdf`

### Step 2 — Coleta Deterministica

```bash
cd D:/pncp-poc
python scripts/intel-collect.py --cnpj {CNPJ} --ufs {UFS} --output {DATA_JSON}
```

Verificar output:
- Quantos editais brutos capturados?
- Quantos compativeis com CNAE?
- Algum erro de API?
- Capital social obtido?
- Quantos EXPIRADOS foram marcados?

O script automaticamente coleta:
- **Inteligencia competitiva:** contratos dos ultimos 2 anos de cada orgao (top 15 orgaos, consultas anuais consolidadas)
- **Benchmark de preco:** desconto mediano historico do orgao + faixa de lance sugerida

Se `empresa._source.status == "API_FAILED"`: PARAR e informar que nao foi possivel obter dados da empresa.

### Step 2.5 — Enriquecimento (SICAF + Sancoes + Distancia + Custo)

**SICAF e OBRIGATORIO — NUNCA pular.** E a primeira verificacao cadastral e deve ser feita antes de qualquer analise.

```bash
python scripts/intel-enrich.py --input {DATA_JSON}
```

**NAO usar `--skip-sicaf`.** O captcha manual do SICAF e necessario 1x por execucao. Aguardar o usuario resolver o captcha.

O script automaticamente:
1. **Coleta SICAF via Playwright (CRC, restricao)** — requer captcha manual 1x
2. Consulta Portal da Transparencia (CEIS/CNEP/CEPIM/CEAF) — sancoes
3. Geocodifica sede da empresa + municipios dos editais (OSRM + Nominatim)
4. Calcula distancia sede-edital (OSRM Table API — batch)
5. Coleta IBGE (populacao/PIB) de cada municipio
6. Calcula custo estimativo de proposta (presencial vs eletronico)
7. Calcula ROI simplificado (valor_edital / custo_proposta)

Verificar output:
- Empresa sancionada? Se SIM: **ALERTA VERMELHO** — empresa impedida de licitar
- Restricao SICAF? Se SIM: **WARNING** — risco de inabilitacao
- Quantas distancias calculadas?
- Quantos custos estimados?

Se `empresa.sancionada == true`: Informar o impedimento legal e recomendar regularizacao. O relatorio sera gerado com alerta de impedimento.

---

## GATE 1 — Validacao Temporal (apos coleta)

**Objetivo:** Garantir que NENHUM edital expirado chegue ao relatorio.

O `intel-collect.py` calcula `status_temporal` para cada edital:
- `EXPIRADO` — encerramento ja passou — **excluido automaticamente** do top20
- `URGENTE` — encerramento dentro de 7 dias — flag vermelho no relatorio
- `IMINENTE` — encerramento entre 7-15 dias — flag amarelo
- `PLANEJAVEL` — encerramento > 15 dias — normal
- `SEM_DATA` — sem data de encerramento

**Acao do Gate:** Verificar na saida do collect:
- Se `total_expirados` > 0: OK, foram excluidos automaticamente
- Se >50% dos compativeis sao `SEM_DATA`: ALERTA — muitos editais sem prazo definido, mencionar no relatorio

**REGRA ABSOLUTA:** Editais `EXPIRADO` NUNCA aparecem no top20 nem no relatorio.

---

## GATE 2 — Compatibilidade Semantica (antes da selecao do top20)

**Objetivo:** Garantir que NENHUM edital incompativel chegue ao top20.

### Step 3 — Gate de Compatibilidade

**Processo em duas etapas:**

**Etapa A — Gate de Ruido (editais `needs_llm_review`):**
Ler o JSON. Para editais marcados com `needs_llm_review = true`:
- Ler o campo `objeto`
- Considerar o CNAE da empresa (codigo + descricao)
- Decidir: COMPATIVEL ou INCOMPATIVEL
- Criterio conservador: na duvida, INCOMPATIVEL (zero ruido > zero perda)
- Salvar JSON atualizado

**Etapa B — Validacao Semantica dos Top 40:**
Apos a etapa A, identificar os **top 40 editais por valor** (compativeis + dentro da capacidade + NAO EXPIRADOS).
Para cada um, validar que o `objeto` e genuinamente compativel com a atividade da empresa.

Criterios de INCOMPATIBILIDADE (rejeitar imediatamente):
- Software/TI/ERP/sistemas quando empresa e de construcao
- Alimentacao/refeicoes quando empresa e de engenharia
- Limpeza/conservacao quando empresa e de obras
- Concessoes de servico publico (Zona Azul, iluminacao, transporte) quando empresa e construtora
- Obras em UFs distantes (>1000 km) sem justificativa estrategica

Resultado: lista limpa de candidatos ao top20, sem falsos positivos.

**Autonomia do Gate:** Se >10 dos 40 candidatos forem eliminados, expandir para top 60 e revalidar.

---

### Step 4 — Gerar Planilha Excel

```bash
python scripts/intel-excel.py --input {DATA_JSON} --output {EXCEL_FILE}
```

Verificar: arquivo gerado, tamanho, contagem de linhas.

---

### Step 5 — Download e Extracao de Documentos

```bash
python scripts/intel-extract-docs.py --input {DATA_JSON} --top 20
```

O script automaticamente:
1. Filtra top 20 editais compativeis dentro da capacidade, **excluindo EXPIRADOS**
2. Prioriza documentos por relevancia (edital > TR > planilha > outros)
3. Baixa ate 3 documentos por edital (max 50MB cada)
4. Extrai texto: PDF (PyMuPDF + OCR fallback), ZIP/RAR (descompacta recursivamente), XLS/XLSX (openpyxl/xlrd)
5. Calcula `extraction_quality` por edital: COMPLETO / PARCIAL / INSUFICIENTE / VAZIO
6. Salva texto em `editais[].texto_documentos` e cria array `top20` no JSON

---

## GATE 3 — Qualidade de Extracao (apos download)

**Objetivo:** Garantir que cada edital do top20 tem texto suficiente para analise completa.

Verificar `extraction_quality` de cada edital no top20:
- `COMPLETO` (>10K chars + 3+ secoes-chave): OK, prosseguir
- `PARCIAL` (2K-10K chars ou poucas secoes): ACEITAVEL mas alertar na analise
- `INSUFICIENTE` (<2K chars): **ACIONAR FALLBACK:**
  1. Tentar baixar mais documentos (`--docs-per-edital 5`)
  2. Buscar edital no portal alternativo (BLL, BBMNET, PCP, ComprasNet)
  3. Se ainda insuficiente: analisar com texto disponivel + objeto, mas marcar como "Analise limitada — edital principal nao disponivel para download"
- `VAZIO` (0 chars): **SUBSTITUIR** pelo proximo edital elegivel da lista
  - Reexecutar: `python scripts/intel-extract-docs.py --input {DATA_JSON} --top 20 --preserve-top20`

**Autonomia do Gate:** Se >5 editais sao INSUFICIENTE/VAZIO, substituir todos e reexecutar extracao.

**REGRA:** Ao usar `--preserve-top20`, o script preserva a selecao existente e apenas processa documentos faltantes.

---

### Step 6 — Analise Estruturada (Claude inline)

**Etapa A — Preparar contexto:**
```bash
python scripts/intel-analyze.py --input {DATA_JSON} --prepare
```

O script prepara `_analysis_context` e `_analysis_rules` para cada edital no top20, sem chamar API externa.

**Etapa B — Analise por Claude (inline):**
Ler o JSON preparado. Para cada edital em `top20` (que NAO tenha `analise` preenchida):

1. Ler campos: `_analysis_context`, `_analysis_rules`, `texto_documentos`
2. Se `_analysis_limited == true`: analisar apenas com metadados, marcar `_source: "claude_limited"`
3. Aplicar as regras de extracao do Step 7 (schema de 16 campos, palavras proibidas, enums)
4. Usar `_analysis_rules` como regras mandatorias adicionais (sancoes, status temporal, distancia)
5. Produzir os 16 campos obrigatorios em JSON e escrever em `top20[N].analise`

**REGRA ABSOLUTA: A analise deve produzir CLAREZA, nao duvida.**
- NUNCA escrever "verificar", "a confirmar", "possivelmente", "nao detalhado"
- NUNCA recomendar "VERIFICAR" — a recomendacao DEVE ser PARTICIPAR ou NAO PARTICIPAR
- Se o documento foi baixado e lido, TODAS as informacoes concretas devem ser extraidas
- Se genuinamente ausente apos busca exaustiva, escrever "Nao consta no edital disponivel"

**Extracao obrigatoria do texto do edital:**
- Data e hora da sessao publica (buscar: "sessao publica", "data da disputa", "abertura")
- Prazo limite de propostas (buscar: "limite para", "encaminhamento das propostas")
- Prazo de execucao exato (buscar: "prazo de execucao", "meses", "dias corridos")
- Patrimonio liquido minimo (buscar: "patrimonio liquido", "PL minimo", "10%", "qualificacao economica")
- Acervo tecnico / CAT exigido (buscar: "acervo tecnico", "CAT", "atestado de capacidade")
- Garantia de proposta (buscar: "garantia", "caucao", "seguro-garantia")
- Visita tecnica (buscar: "visita tecnica", "vistoria")
- Consorcio (buscar: "consorcio", "vedada", "permitida")
- Plataforma eletronica (BNC, BLL, BBMNET, ComprasGov, Portal de Compras)
- Regime de execucao (empreitada global, preco unitario, parcelada)
- Exclusividade ME/EPP (buscar: "exclusiv", "LC 123", "microempresa")

**Usar dados enriquecidos** (`_analysis_context` + `_analysis_rules`) e `status_temporal`:
- Se `status_temporal == "URGENTE"`: destacar prazo curto na recomendacao
- Se `status_temporal == "IMINENTE"`: mencionar prazo moderado
- Se `distancia.km` > 500: mencionar custo logistico elevado
- Se `custo_proposta.total` > 5% do valor: alertar sobre margem
- Se `roi_proposta.classificacao` == "DESFAVORAVEL": recomendar cautela
- Se `ibge.populacao` < 5000 e valor > R$1M: alertar fragilidade logistica
- Se empresa sancionada/com restricao SICAF: todas as recomendacoes = NAO PARTICIPAR

**Schema JSON (16 campos obrigatorios):**
```json
{
  "resumo_objeto": "2-3 frases descrevendo o que esta sendo contratado",
  "requisitos_tecnicos": ["lista", "de", "requisitos"],
  "requisitos_habilitacao": ["lista", "de", "requisitos"],
  "qualificacao_economica": "Patrimonio liquido minimo de X% (R$ Y)",
  "prazo_execucao": "X meses a partir da OS / N dias corridos",
  "garantias": "X% do valor do contrato (seguro-garantia/caucao/fianca)",
  "criterio_julgamento": "Menor Preco Global / Tecnica e Preco / Maior Desconto",
  "data_sessao": "DD/MM/YYYY as HH:MM (plataforma: BNC/BLL/BBMNET/PCP)",
  "prazo_proposta": "DD/MM/YYYY as HH:MM",
  "visita_tecnica": "Obrigatoria ate DD/MM/YYYY / Facultativa / Nao consta no edital disponivel",
  "exclusividade_me_epp": "Sim/Nao/Cota reservada X%",
  "regime_execucao": "Empreitada por preco global / unitario / parcelada",
  "consorcio": "Permitido/Vedado/Nao mencionado no edital",
  "observacoes_criticas": "Riscos, gaps, alertas relevantes",
  "nivel_dificuldade": "BAIXO/MEDIO/ALTO",
  "recomendacao_acao": "PARTICIPAR ou NAO PARTICIPAR (nunca VERIFICAR)",
  "custo_logistico_nota": "Avaliacao de impacto logistico"
}
```

Processar TODOS os editais do top20 e salvar o JSON atualizado com Write tool.

**Etapa C — Validar e salvar:**
```bash
python scripts/intel-analyze.py --input {DATA_JSON} --save-analysis
```

Valida cada `analise` (normaliza enums, garante campos obrigatorios, limpa campos de preparacao).

**Modo API legado:** Se preferir usar OpenAI API: `python scripts/intel-analyze.py --input {DATA_JSON}` (requer `OPENAI_API_KEY`).

---

### Step 6.5 — Validacao Programatica (Gates 2+4+5)

```bash
python scripts/intel-validate.py --input {DATA_JSON} --fix
```

Validacoes automaticas:
1. **Gate 2:** Rejeita editais semanticamente incompativeis (software para construtora, etc.)
2. **Gate 4:** Verifica completude — nenhum campo com palavras proibidas
3. **Gate 5:** Coerencia — nenhum EXPIRADO, nenhum NAO PARTICIPAR no top20, campos_completos >= 60%

Com `--fix`: corrige automaticamente issues encontradas (remove expirados, substitui "VERIFICAR" por "NAO PARTICIPAR").

**Se `overall_passed == false` apos --fix:** Revisar manualmente os issues listados no validation report.

---

### Step 7 — Revisao Adversarial + Resumo Executivo (Claude inline)

**7.1 — Revisao adversarial:**
Para cada edital no top20 com `analise` preenchida e `texto_documentos` disponivel:
- Comparar a analise com o texto do edital
- Verificar: data_sessao confere? criterio_julgamento correto? garantias corretas? Algum campo "Nao consta" mas a info ESTA no texto?
- Corrigir campos com erro factual diretamente no JSON
- Marcar `analise._reviewed = true`

**7.2 — Resumo executivo:**
Redigir `resumo_executivo` (2-3 paragrafos): total de editais, compativeis, recomendados, destaques, alertas.
Citar numeros concretos, valores, municipios. Ser direto e acionavel.

**7.3 — Proximos passos:**
Redigir `proximos_passos` (lista de 5-8 acoes concretas).
Cada passo deve comecar com prefixo: `URGENTE:` / `PRIORITARIO:` / `AVALIAR:` / `MONITORAR:`
Citar numeros de editais (#N), valores, datas, municipios. NUNCA usar "verificar".

Salvar `resumo_executivo` e `proximos_passos` no JSON.

---

## GATE 4 — Completude da Analise (apos analise profunda)

**Objetivo:** Garantir que NENHUM campo obrigatorio contem linguagem de incerteza.

**Campos obrigatorios com valor concreto:**
- `data_sessao` — data exata OU "Nao consta no edital disponivel"
- `criterio_julgamento` — valor do enum: Menor Preco / Tecnica e Preco / Maior Desconto
- `regime_execucao` — valor do enum: Empreitada Global / Preco Unitario / Semi-Integrada
- `consorcio` — Permitido / Vedado / Nao mencionado no edital
- `recomendacao_acao` — PARTICIPAR ou NAO PARTICIPAR (NUNCA "VERIFICAR")

**Palavras proibidas em qualquer campo da analise:**
- "verificar" (qualquer forma)
- "possivelmente"
- "buscar edital"
- "nao detalhado"
- "a confirmar"

**Acao do Gate:**
1. Para cada edital, verificar todos os campos obrigatorios
2. Se algum campo contem palavra proibida:
   a. Se `extraction_quality == "COMPLETO"`: reanalisar o texto com prompt focado no campo faltante
   b. Se `extraction_quality == "PARCIAL/INSUFICIENTE"`: voltar ao Gate 3 para buscar mais documentos
   c. Apos 2 tentativas sem sucesso: aceitar "Nao consta no edital disponivel" (genuinamente ausente)
3. Se `recomendacao_acao` contem "VERIFICAR": substituir por:
   - `status_temporal == "EXPIRADO"` — "NAO PARTICIPAR — edital encerrado"
   - `status_temporal == "SEM_DATA"` — "PARTICIPAR" (com observacao em `observacoes_criticas`: "Sem data de encerramento publicada — confirmar prazo antes de preparar proposta")
   - Caso contrario — decidir PARTICIPAR ou NAO PARTICIPAR baseado na analise

**REGRA:** O Gate 4 tem autonomia total para demandar reexecucao dos Steps 5, 6, e 7.

---

### Step 7.5 — Filtro Pos-Analise (OBRIGATORIO)

Apos a analise e validacao pelo Gate 4:
- **REMOVER do top20** editais com `recomendacao_acao = "NAO PARTICIPAR"`
- Substituir slots removidos pelos proximos editais elegiveis
- Se substituicao necessaria, rodar Steps 5-7 + Gate 3-4 para os novos editais.
**LIMITE:** Maximo 2 rodadas de substituicao. Se apos 2 rodadas o top20 tiver menos de 20 editais, aceitar o top20 com o numero disponivel.

**O relatorio PDF contem APENAS editais com recomendacao PARTICIPAR.**

### Step 7.6 — Adendo: Oportunidades Acima da Capacidade (via Consorcio)

Se houver editais relevantes ACIMA da capacidade 10x que seriam excelentes oportunidades:
- Listar ate 5 como "Oportunidades via Consorcio" em secao separada do relatorio
- Mencionar apenas brevemente (objeto, valor, municipio, por que e interessante)
- NAO fazer analise profunda — apenas sinalizar como potencial

---

## GATE 5 — Coerencia do Relatorio (antes do PDF)

**Objetivo:** Garantir que o PDF e fonte de clareza absoluta.

**Validacoes automaticas (executadas pelo `intel-report.py`):**
1. Nenhum edital EXPIRADO no relatorio
2. Nenhum edital com recomendacao "NAO PARTICIPAR" no relatorio
3. Todos os editais tem `data_sessao` preenchida ou `status_temporal` definido
4. `proximos_passos` ordenados por urgencia (data mais proxima primeiro)
5. Nenhum proximo passo contem "verificar" ou "buscar"
6. Todas as datas em `proximos_passos` sao futuras
7. `campos_completos_pct >= 60%` (threshold minimo para gerar PDF)

**Selo de qualidade no PDF:**
- "Completude dos dados: XX%"
- "SICAF: Verificado em DD/MM/YYYY"
- "Sancoes: Nenhuma / IMPEDIDA"

**Se `campos_completos_pct < 60%`:** O `intel-report.py` gera o PDF com warning, e o Gate 5 recomenda ao operador quais campos faltam para atingir o threshold.

---

### Step 8 — Gerar PDF

```bash
python scripts/intel-report.py --input {DATA_JSON} --output {PDF_FILE}
```

### Step 9 — Report Results

Informar ao usuario:
- Excel: `{EXCEL_FILE}` — {N} editais ({M} compativeis CNAE, {X} expirados excluidos)
- PDF: `{PDF_FILE}` — Analise de {K} oportunidades recomendadas (completude: XX%)
- JSON: `{DATA_JSON}`
- Resumo: top 3 oportunidades com valor, prazo, e status temporal

---

## GUARDRAILS

1. **NUNCA pular o Gate 2** (compatibilidade semantica) — e obrigatorio para zero noise
2. **NUNCA pular SICAF** — e obrigatorio, sempre a primeira verificacao cadastral
3. **NUNCA incluir Dispensa ou Inexigibilidade** — apenas modalidades competitivas
4. **NUNCA incluir editais EXPIRADOS** — nem no top20, nem no relatorio
5. **NUNCA incluir editais acima da capacidade 10x no top 20** — apenas no adendo de consorcio
6. **NUNCA incluir duplicatas** — dedup por orgao/ano/sequencial e por similaridade de objeto+valor
7. **NUNCA incluir no relatorio editais com recomendacao "NAO PARTICIPAR"** — apenas na planilha
8. **NUNCA usar "VERIFICAR" como recomendacao** — PARTICIPAR ou NAO PARTICIPAR, sempre
9. **NUNCA usar palavras proibidas** — "verificar", "possivelmente", "buscar edital", "nao detalhado", "a confirmar"
10. **Planilha contem TODOS os editais** — sem filtro de valor/viabilidade
11. **PDF contem apenas editais RECOMENDADOS** dentro da capacidade
12. Se download de documentos falhar: marcar "Analise limitada — edital principal nao disponivel para download"
13. Se PyMuPDF/OCR nao instalado: informar o usuario e prosseguir sem extracao (analise limitada ao objeto)
14. **Top 10 editais no PDF** (max 15 paginas). Se a empresa tem >10 editais PARTICIPAR, priorizar por valor e incluir os demais como lista resumida (1 linha por edital). O Excel contem a lista completa.
15. **Cada gate tem autonomia para demandar reexecucao** de etapas anteriores
16. **Benchmark de preco requer minimo 3 contratos com resultado** — orgaos com dados insuficientes nao geram sugestao de lance

## Params

$ARGUMENTS
