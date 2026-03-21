# /intel-busca — Inteligencia Estrategica de Editais por CNPJ

## Purpose

Busca exaustiva e analise profunda de editais abertos no PNCP para um CNPJ especifico.
Zero ruido. Zero perda de oportunidades. Zero incerteza no relatorio.
Utiliza TODOS os CNAEs da empresa (principal + secundarios) para maxima cobertura.

**Entregaveis:**
1. `docs/intel/intel-{CNPJ}-{razao-slug}-{YYYY-MM-DD}.xlsx` — Planilha com TODAS as oportunidades compativeis (sem ruido — zero editais fora do setor)
2. `docs/intel/intel-{CNPJ}-{razao-slug}-{YYYY-MM-DD}.pdf` — Relatorio estrategico dos 20 editais analisados (max 15 paginas)

**Princípios:**
- O relatório é fonte de CLAREZA, nunca de dúvida
- Cada gate tem autonomia para demandar reexecução de etapas anteriores
- **O top20 DEVE conter 20 editais genuinamente compatíveis analisados.** Se um edital é excluído por incompatibilidade semântica (não pertence ao setor da empresa), o próximo elegível (#21, #22...) entra e passa pelo pipeline completo (Steps 5-7 + Gates 3-4). Máximo 3 rodadas de substituição.
- A recomendação (PARTICIPAR / NÃO PARTICIPAR) é resultado da análise, NÃO critério de exclusão do top20. Editais NÃO PARTICIPAR por motivos legítimos (prazo, acervo, distância) permanecem — o cliente precisa dessa informação.
- O cliente NUNCA vê editais fora do setor. Editais de medicamentos, alimentação, TI, etc. são filtrados antes de qualquer output.

**REGRA DE IDIOMA (OBRIGATÓRIA):**
- **TODO texto gerado pelo pipeline DEVE usar português correto com acentuação completa** (ç, ã, á, é, ê, í, ó, ô, ú, à).
- Isso inclui: `resumo_executivo`, `proximos_passos`, todos os campos de `analise` (resumo_objeto, observacoes_criticas, recomendacao_acao, custo_logistico_nota, etc.).
- Exemplos corretos: "construção" (não "construcao"), "não" (não "nao"), "patrimônio líquido" (não "patrimonio liquido"), "São Paulo" (não "Sao Paulo"), "distância" (não "distancia"), "logístico" (não "logistico").
- Campos enum com acento: "Não consta no edital disponível", "Empreitada por preço global", "Técnica e Preço", "NÃO PARTICIPAR".
- **Violação desta regra invalida o entregável.** O PDF é documento profissional entregue ao cliente.

### Capacidades v4 (novo)

1. **Classificacao Probabilistica** — CNAE gate agora produz `cnae_confidence` (0-100%) em vez de binario YES/NO. Threshold configuravel por setor. Compoe keyword density (40%), heuristica (30%), exclusion pattern (30%).
2. **Perfil de Vitoria** — Analisa historico de contratos da empresa e aprende: faixa de valor preferida, modalidades com maior vitoria, porte de municipio, tipos de obra recorrentes. Score de aderencia 0-100% por edital.
3. **Simulacao de Lance** — Para cada edital com dados de benchmark, calcula lance otimo: P(vitoria) × margem. Usa HHI, descontos historicos do orgao, margem minima do setor. Resultado: lance sugerido + faixa (agressivo/conservador) + probabilidade estimada.
4. **Extracao Estruturada** — Templates por tipo de documento (Edital, TR, Planilha). Regex especializados extraem campos tipados (patrimonio liquido, acervo, garantias, prazo) ANTES da analise LLM, fornecendo hints que reduzem "Nao consta" de ~30% para <5%.
5. **Delta Reporting** — Compara contra ultima execucao e marca cada edital: NOVO / ATUALIZADO / VENCENDO / INALTERADO. Excel e PDF mostram apenas mudancas relevantes.
6. **Dedup Semantico** — Alem do dedup por hash, detecta duplicatas cross-portal: mesmo orgao + municipio + valor ±15% + objeto com >65% token overlap = mesmo edital.

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

O script automaticamente executa nesta ordem:
1. **Perfil da empresa** (OpenCNPJ)
2. **SICAF + Sancoes** (Playwright captcha + Portal da Transparencia) — usuario resolve captcha no inicio e fica livre
3. **Mapeamento CNAE → keywords**
4. **Busca exaustiva PNCP** (todas UFs × modalidades)
5. **Filtro temporal** — expirados removidos ANTES de qualquer analise
6. **Gate CNAE** — keywords + density threshold
7. **Inteligencia competitiva** — contratos dos ultimos 2 anos (top 15 orgaos)
8. **Documentos PNCP** — top 50 por valor
9. **Benchmark de preco** — desconto mediano historico do orgao

Se `empresa._source.status == "API_FAILED"`: PARAR e informar que nao foi possivel obter dados da empresa.

### Step 2.5 — Enriquecimento (Distancia + IBGE + Custo)

**SICAF ja foi coletado no Step 2 (intel-collect.py).** O enrich agora foca em geocodificacao e custos.

```bash
python scripts/intel-enrich.py --input {DATA_JSON}
```

O script automaticamente (pula SICAF se ja coletado):
1. Geocodifica sede da empresa + municipios dos editais (OSRM + Nominatim)
2. Calcula distancia sede-edital (OSRM Table API — batch)
3. Coleta IBGE (populacao/PIB) de cada municipio
4. Calcula custo estimativo de proposta (presencial vs eletronico)
5. Calcula ROI simplificado (valor_edital / custo_proposta)

Verificar output:
- Empresa sancionada? Se SIM: **ALERTA VERMELHO** — empresa impedida de licitar
- Restricao SICAF? Se SIM: **WARNING** — risco de inabilitacao
- Quantas distancias calculadas?
- Quantos custos estimados?

Se `empresa.sancionada == true`: Informar o impedimento legal e recomendar regularizacao. O relatorio sera gerado com alerta de impedimento.

---

## GATE 1 — Validacao Temporal (apos coleta)

**Objetivo:** Garantir que APENAS editais com propostas abertas cheguem ao relatorio.

O `intel-collect.py` calcula `status_temporal` para cada edital:
- `EXPIRADO` — encerramento ja passou — **excluido automaticamente**
- `SESSAO_REALIZADA` — sessao de lances ja aconteceu — **excluido automaticamente** (oportunidade perdida)
- `URGENTE` — encerramento dentro de 7 dias — flag vermelho no relatorio
- `IMINENTE` — encerramento entre 7-15 dias — flag amarelo
- `PLANEJAVEL` — encerramento > 15 dias — normal
- `SEM_DATA` — sem data de encerramento

**Acao do Gate:** Verificar na saida do collect:
- Se `total_expirados` > 0: OK, foram excluidos automaticamente
- Se >50% dos compativeis sao `SEM_DATA`: ALERTA — muitos editais sem prazo definido, mencionar no relatorio

**REGRA ABSOLUTA:** Editais `EXPIRADO` e `SESSAO_REALIZADA` NUNCA aparecem no top20 nem no relatorio. Apenas oportunidades abertas.

---

## GATE 2 — Compatibilidade Semantica (antes da selecao do top20)

**Objetivo:** Garantir que NENHUM edital incompativel chegue ao top20.

### Step 3 — Validacao Semantica (Gate 2)

**O `intel-collect.py` agora faz a maior parte do trabalho:**
1. Exclusion patterns eliminam editais obviamente incompativeis (medicamentos, alimentacao, TI, etc.)
2. Classificador heuristico secundario resolve os `needs_llm_review` restantes
3. Resultado: `needs_llm_review = 0` — todos classificados automaticamente

**Neste step, validar os top 30 candidatos (por `_opportunity_score`):**
Para cada um, confirmar que o `objeto` e genuinamente compativel com a atividade da empresa.

Criterios de INCOMPATIBILIDADE (rejeitar imediatamente):
- Software/TI/ERP/sistemas quando empresa e de construcao
- Alimentacao/refeicoes quando empresa e de engenharia
- Limpeza/conservacao quando empresa e de obras
- Concessoes de servico publico (Zona Azul, iluminacao, transporte) quando empresa e construtora
- Construcao naval/lanchas quando empresa e de engenharia civil
- Equipamentos militares especializados fora do escopo

Resultado: lista limpa de candidatos ao top20+backlog, sem falsos positivos.

**Autonomia do Gate:** Se >10 dos 30 candidatos forem eliminados, expandir para top 50 e revalidar.

---

### Step 4 — Gerar Planilha Excel

```bash
python scripts/intel-excel.py --input {DATA_JSON} --output {EXCEL_FILE}
```

Verificar: arquivo gerado, tamanho, contagem de linhas.

---

### Step 5 — Download e Extracao de Documentos

```bash
python scripts/intel-extract-docs.py --input {DATA_JSON} --top 30
```

**IMPORTANTE:** Extrair documentos para **top 30** (50% buffer), nao apenas 20. Isso garante que quando editais forem excluidos por incompatibilidade semantica na analise, ja existem substitutos com documentos extraidos prontos para analise imediata.

O script automaticamente:
1. Usa `_opportunity_score` para ranking (valor x proximidade x urgencia), excluindo EXPIRADOS e SESSAO_REALIZADA
2. Prioriza documentos por relevancia (edital > TR > planilha > outros)
3. Baixa ate 3 documentos por edital (max 50MB cada)
4. Extrai texto: PDF (PyMuPDF + OCR fallback), ZIP/RAR (descompacta recursivamente), XLS/XLSX (openpyxl/xlrd)
5. Calcula `extraction_quality` por edital: COMPLETO / PARCIAL / INSUFICIENTE / VAZIO
6. Salva texto em `editais[].texto_documentos` e cria array `top20` (primeiros 20) + `_backlog` (posicoes 21-30) no JSON

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

**REGRA DE REDACAO:** A frase "Nao consta no edital disponivel" e permitida APENAS como valor de campo isolado (ex: data_sessao, visita_tecnica).
NUNCA deve aparecer DENTRO de frases em recomendacao_acao ou observacoes_criticas.
Se precisar indicar limitacao documental, reformular como: "Edital completo indisponivel para download — consultar diretamente no portal antes de elaborar proposta."

**REGRA SESSAO_REALIZADA:** Quando status_temporal == "SESSAO_REALIZADA":
- A recomendacao DEVE incluir: "Sessao de lances ja realizada. Consultar resultado no portal antes de qualquer acao."
- NUNCA dizer "a proposta esta aberta" ou "pode ser enviada imediatamente"
- No resumo executivo: contabilizar separadamente editais PLANEJAVEL/IMINENTE/URGENTE (acao imediata) vs SESSAO_REALIZADA (consultar resultado)

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

**Schema JSON (16 campos obrigatórios — TODOS com acentuação correta):**
```json
{
  "resumo_objeto": "2-3 frases descrevendo o que está sendo contratado",
  "requisitos_tecnicos": ["lista", "de", "requisitos"],
  "requisitos_habilitacao": ["lista", "de", "requisitos"],
  "qualificacao_economica": "Patrimônio líquido mínimo de X% (R$ Y)",
  "prazo_execucao": "X meses a partir da OS / N dias corridos",
  "garantias": "X% do valor do contrato (seguro-garantia/caução/fiança)",
  "criterio_julgamento": "Menor Preço Global / Técnica e Preço / Maior Desconto",
  "data_sessao": "DD/MM/YYYY às HH:MM (plataforma: BNC/BLL/BBMNET/PCP)",
  "prazo_proposta": "DD/MM/YYYY às HH:MM",
  "visita_tecnica": "Obrigatória até DD/MM/YYYY / Facultativa / Não consta no edital disponível",
  "exclusividade_me_epp": "Sim/Não/Cota reservada X%",
  "regime_execucao": "Empreitada por preço global / unitário / parcelada",
  "consorcio": "Permitido/Vedado/Não mencionado no edital",
  "observacoes_criticas": "Riscos, gaps, alertas relevantes (redigir com acentuação)",
  "nivel_dificuldade": "BAIXO/MÉDIO/ALTO",
  "recomendacao_acao": "PARTICIPAR ou NÃO PARTICIPAR (NUNCA 'VERIFICAR', NUNCA texto livre após o enum)",
  "custo_logistico_nota": "Avaliação de impacto logístico (redigir com acentuação)"
}
```

**REGRA ANL-03 (enum estrito para recomendacao_acao):**
- O campo `recomendacao_acao` aceita EXATAMENTE dois valores: `"PARTICIPAR"` ou `"NÃO PARTICIPAR"`.
- Qualificadores como "com cautela", "com ressalva", "condicional — se ME/EPP" devem ir em `observacoes_criticas`, NUNCA no campo de recomendação.
- Se há condição para participar (ex: exige CAT específico), a recomendação é `"PARTICIPAR"` e a condição vai em `observacoes_criticas`.
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
Redigir `resumo_executivo` (2-3 parágrafos) **em português com acentuação completa**: total de editais, compatíveis, recomendados, destaques, alertas.
Citar números concretos, valores, municípios. Ser direto e acionável.

**REGRA DE CONSISTENCIA:** Os numeros do resumo executivo DEVEM ser computados a partir do JSON:
- "X editais PARTICIPAR" = count de top20 com analise.recomendacao_acao == "PARTICIPAR"
- "R$ Y milhoes" = soma de valor_estimado dos editais PARTICIPAR
- NUNCA usar numeros diferentes dos que serao renderizados no PDF

Redigir resumo separando:
- Editais com acao imediata (PLANEJAVEL + IMINENTE + URGENTE): X editais, R$ Y
- Editais com sessao realizada (SESSAO_REALIZADA): X editais — consultar resultados nos portais

**7.3 — Próximos passos:**
Redigir `proximos_passos` (lista de 5-8 ações concretas) **em português com acentuação completa**.
Cada passo deve começar com prefixo: `URGENTE:` / `PRIORITÁRIO:` / `AVALIAR:` / `MONITORAR:`
Citar números de editais (#N), valores, datas, municípios. NUNCA usar "verificar".

**REGRA ABSOLUTA:** Proximos passos NUNCA devem citar editais cuja recomendacao_acao seja NAO PARTICIPAR.
Antes de incluir qualquer edital nos proximos passos, confirmar que sua recomendacao e PARTICIPAR.

Salvar `resumo_executivo` e `proximos_passos` no JSON.

---

## GATE 4 — Completude da Analise (apos analise profunda)

**Objetivo:** Garantir que NENHUM campo obrigatorio contem linguagem de incerteza.

**Campos obrigatórios com valor concreto (com acentuação):**
- `data_sessao` — data exata OU "Não consta no edital disponível"
- `criterio_julgamento` — valor do enum: Menor Preço / Técnica e Preço / Maior Desconto
- `regime_execucao` — valor do enum: Empreitada por preço global / Preço unitário / Semi-integrada
- `consorcio` — Permitido / Vedado / Não mencionado no edital
- `recomendacao_acao` — PARTICIPAR ou NÃO PARTICIPAR (NUNCA "VERIFICAR", NUNCA texto livre junto)

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

### Step 7.5 — Substituicao por Incompatibilidade (ITERATIVO)

Apos a analise:
1. **Identificar editais INCOMPATIVEIS** no top20 — editais que NAO pertencem ao setor da empresa e entraram por falha do gate CNAE (ex: lanchas militares para construtora, TI para engenharia civil, projetos farmaceuticos para empresa de obras).
2. **NAO REMOVER editais NAO PARTICIPAR por motivos legitimos** — prazo curto, acervo especifico, distancia inviavel. Estes PERMANECEM no top20 porque o cliente precisa saber POR QUE nao participar.
3. **Substituir slots de incompativeis** pelos proximos elegiveis do `_backlog` (posicoes 21-30, ja com documentos extraidos).
4. Para cada substituto: rodar analise (Steps 6-7) + Gates 3-4.
5. Se o backlog se esgotar e ainda faltar editais, expandir: `python scripts/intel-extract-docs.py --input {DATA_JSON} --top 40 --preserve-top20`

**LIMITE:** Maximo 3 rodadas de substituicao. Se apos 3 rodadas o top20 tiver menos de 20, aceitar com o numero disponivel.

**O relatorio PDF contem TODOS os 20 editais analisados — tanto PARTICIPAR quanto NAO PARTICIPAR com justificativa.**

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
2. Nenhum edital semanticamente incompativel no relatorio (editais fora do setor da empresa)
3. Todos os editais tem `data_sessao` preenchida ou `status_temporal` definido
4. Top20 tem exatamente 20 editais (ou maximo disponivel apos 3 rodadas de substituicao)
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
- Excel: `{EXCEL_FILE}` — {N} oportunidades compativeis com o perfil da empresa
- PDF: `{PDF_FILE}` — Analise de 20 editais ({K} PARTICIPAR, {L} NAO PARTICIPAR com justificativa, completude: XX%)
- JSON: `{DATA_JSON}`
- Resumo: top 3 oportunidades PARTICIPAR com valor, prazo, e status temporal
- Destaques: editais NAO PARTICIPAR mais relevantes e motivo (para contexto estrategico)

---

## GUARDRAILS

1. **NUNCA pular o Gate 2** (compatibilidade semantica) — e obrigatorio para zero noise
2. **NUNCA pular SICAF** — e obrigatorio, sempre a primeira verificacao cadastral
3. **NUNCA incluir Dispensa ou Inexigibilidade** — apenas modalidades competitivas
4. **NUNCA incluir editais EXPIRADOS** — nem no top20, nem no relatorio
5. **NUNCA incluir editais acima da capacidade 10x no top 20** — apenas no adendo de consorcio
6. **NUNCA incluir duplicatas** — dedup por orgao/ano/sequencial e por similaridade de objeto+valor
7. **Editais NAO PARTICIPAR por motivo legitimo PERMANECEM no relatorio** com justificativa clara. So sao removidos editais que entraram por erro do gate (incompatibilidade semantica com o setor).
8. **NUNCA usar "VERIFICAR" como recomendacao** — PARTICIPAR ou NAO PARTICIPAR, sempre
9. **NUNCA usar palavras proibidas** — "verificar", "possivelmente", "buscar edital", "nao detalhado", "a confirmar"
10. **Planilha contem APENAS oportunidades compativeis** — zero ruido (sem editais fora do setor)
11. **PDF contem os 20 editais analisados** — PARTICIPAR e NAO PARTICIPAR com justificativa
12. Se download de documentos falhar: marcar "Analise limitada — edital principal nao disponivel para download"
13. Se PyMuPDF/OCR nao instalado: informar o usuario e prosseguir sem extracao (analise limitada ao objeto)
14. **Top 10 editais no PDF** (max 15 paginas). Se a empresa tem >10 editais PARTICIPAR, priorizar por valor e incluir os demais como lista resumida (1 linha por edital). O Excel contem a lista completa.
15. **Cada gate tem autonomia para demandar reexecucao** de etapas anteriores
16. **Benchmark de preco requer minimo 3 contratos com resultado** — orgaos com dados insuficientes nao geram sugestao de lance

## Params

$ARGUMENTS
