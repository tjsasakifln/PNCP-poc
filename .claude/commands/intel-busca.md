# /intel-busca — Inteligência Estratégica de Editais por CNPJ

## Purpose

Busca exaustiva e análise profunda de editais abertos no PNCP para um CNPJ específico.
Zero ruído. Zero perda de oportunidades. Funciona para qualquer ramo de atividade.
Utiliza TODOS os CNAEs da empresa (principal + secundários) para máxima cobertura.

**Entregáveis:**
1. `docs/intel/intel-{CNPJ}-{razao-slug}-{YYYY-MM-DD}.xlsx` — Planilha completa com TODOS os editais (inclui distância, custo, ROI)
2. `docs/intel/intel-{CNPJ}-{razao-slug}-{YYYY-MM-DD}.pdf` — Relatório estratégico dos top 20 RECOMENDADOS (max 15 páginas)

---

## Execution

### Step 1 — Parse Input

Extrair CNPJ e UFs dos argumentos ($ARGUMENTS).
Aceita formatos:
- `12.345.678/0001-90 SC,PR,RS`
- `12345678000190 SC PR RS`
- `--cnpj 12345678000190 --ufs SC,PR,RS`

Definir variáveis:
- `CNPJ` = 14 dígitos limpos
- `UFS` = lista de UF siglas (uppercase)
- `DATA_JSON = docs/intel/intel-{CNPJ}-{razao-social-slug}-{YYYY-MM-DD}.json`
- `EXCEL_FILE = docs/intel/intel-{CNPJ}-{razao-social-slug}-{YYYY-MM-DD}.xlsx`
- `PDF_FILE = docs/intel/intel-{CNPJ}-{razao-social-slug}-{YYYY-MM-DD}.pdf`

### Step 2 — Coleta Determinística

```bash
cd D:/pncp-poc
python scripts/intel-collect.py --cnpj {CNPJ} --ufs {UFS} --output {DATA_JSON}
```

Verificar output:
- Quantos editais brutos capturados?
- Quantos compatíveis com CNAE?
- Algum erro de API?
- Capital social obtido?

Se `empresa._source.status == "API_FAILED"`: PARAR e informar que não foi possível obter dados da empresa.

### Step 2.5 — Enriquecimento (SICAF + Sanções + Distância + Custo)

**SICAF é OBRIGATÓRIO — NUNCA pular.** É a primeira verificação cadastral e deve ser feita antes de qualquer análise.

```bash
python scripts/intel-enrich.py --input {DATA_JSON}
```

**NÃO usar `--skip-sicaf`.** O captcha manual do SICAF é necessário 1x por execução. Aguardar o usuário resolver o captcha.

O script automaticamente:
1. **Coleta SICAF via Playwright (CRC, restrição)** — requer captcha manual 1x
2. Consulta Portal da Transparência (CEIS/CNEP/CEPIM/CEAF) — sanções
3. Geocodifica sede da empresa + municípios dos editais (OSRM + Nominatim)
4. Calcula distância sede→edital (OSRM Table API — batch)
5. Coleta IBGE (população/PIB) de cada município
6. Calcula custo estimativo de proposta (presencial vs eletrônico)
7. Calcula ROI simplificado (valor_edital / custo_proposta)

Verificar output:
- Empresa sancionada? → Se SIM: **ALERTA VERMELHO** — empresa impedida de licitar
- Restrição SICAF? → Se SIM: **WARNING** — risco de inabilitação
- Quantas distâncias calculadas?
- Quantos custos estimados?

Se `empresa.sancionada == true`: Informar o impedimento legal e recomendar regularização. O relatório será gerado com alerta de impedimento.

### Step 3 — Gate de Ruído (Claude inline)

Ler o JSON gerado. Para editais marcados com `needs_llm_review = true` (keyword density baixa ou zero match):

Para CADA edital ambíguo, julgar:
- Ler o campo `objeto`
- Considerar o CNAE da empresa (código + descrição)
- Decidir: este edital é compatível com o ramo da empresa? SIM ou NÃO?
- Se SIM: alterar `cnae_compatible = true`
- Se NÃO: manter `cnae_compatible = false`

Critério: ser conservador. Na dúvida, manter como incompatível (zero ruído > zero perda neste gate).

Salvar JSON atualizado.

### Step 4 — Gerar Planilha Excel

```bash
python scripts/intel-excel.py --input {DATA_JSON} --output {EXCEL_FILE}
```

Verificar: arquivo gerado, tamanho, contagem de linhas.

### Step 5 — Selecionar Top 20 para Análise Profunda

O script `intel-extract-docs.py` faz a seleção automaticamente com:
- `cnae_compatible == true`
- `valor_estimado <= 10 * empresa.capital_social` (ou sigiloso)
- **Dedup automático** (mesmo edital em portais diferentes é contado 1x)

### Step 6 — Download e Extração de Documentos

```bash
python scripts/intel-extract-docs.py --input {DATA_JSON} --top 20
```

O script automaticamente:
1. Filtra top 20 editais compatíveis dentro da capacidade (10× capital) **SEM DUPLICATAS**
2. Prioriza documentos por relevância (edital > TR > planilha > outros)
3. Baixa até 3 documentos por edital (max 50MB cada)
4. Extrai texto: PDF (PyMuPDF + OCR fallback), ZIP/RAR (descompacta recursivamente), XLS/XLSX (openpyxl/xlrd)
5. Salva texto em `editais[].texto_documentos` e cria array `top20` no JSON

Verificar: quantos editais tiveram texto extraído? Algum falhou?

### Step 7 — Análise Profunda (Claude inline)

Para cada edital do top 20, ler o texto extraído dos documentos e produzir a análise estruturada.

**REGRA ABSOLUTA: NUNCA escrever "verificar", "a confirmar", "não mencionado no trecho", "não detalhado".** Se o documento foi baixado e lido, TODAS as informações concretas devem ser extraídas. Buscar no texto extraído por regex/keyword para cada campo abaixo. Se genuinamente ausente após busca exaustiva, escrever "Não consta no edital disponível".

**Extração obrigatória do texto do edital:**
- Data e hora da sessão pública (buscar: "sessão pública", "data da disputa", "abertura")
- Prazo limite de propostas (buscar: "limite para", "encaminhamento das propostas")
- Prazo de execução exato (buscar: "prazo de execução", "meses", "dias corridos")
- Patrimônio líquido mínimo (buscar: "patrimônio líquido", "PL mínimo", "10%", "qualificação econômica")
- Acervo técnico / CAT exigido (buscar: "acervo técnico", "CAT", "atestado de capacidade")
- Garantia de proposta (buscar: "garantia", "caução", "seguro-garantia")
- Visita técnica (buscar: "visita técnica", "vistoria")
- Consórcio (buscar: "consórcio", "vedada", "permitida")
- Plataforma eletrônica (BNC, BLL, BBMNET, ComprasGov, Portal de Compras)
- Regime de execução (empreitada global, preço unitário, parcelada)
- Exclusividade ME/EPP (buscar: "exclusiv", "LC 123", "microempresa")

Usar os dados enriquecidos (distância, custo, IBGE, SICAF) como contexto:
- Se `distancia.km` > 500: mencionar custo logístico elevado
- Se `custo_proposta.total` > 5% do valor: alertar sobre margem
- Se `roi_proposta.classificacao` == "DESFAVORAVEL": recomendar cautela
- Se `ibge.populacao` < 5000 e valor > R$1M: alertar fragilidade logística
- Se empresa sancionada/com restrição SICAF: todas as recomendações = NÃO RECOMENDADO

```json
{
  "resumo_objeto": "...",
  "requisitos_tecnicos": ["...", "..."],
  "requisitos_habilitacao": ["...", "..."],
  "qualificacao_economica": "Patrimônio líquido mínimo de X% (R$ Y)",
  "prazo_execucao": "X meses a partir da OS",
  "garantias": "X% do valor do contrato (seguro-garantia/caução/fiança)",
  "criterio_julgamento": "Menor Preço Global / Técnica e Preço",
  "data_sessao": "DD/MM/YYYY às HH:MM (plataforma: BNC/BLL/BBMNET/PCP)",
  "prazo_proposta": "DD/MM/YYYY às HH:MM",
  "visita_tecnica": "Obrigatória até DD/MM/YYYY / Facultativa / Não consta no edital",
  "exclusividade_me_epp": "Sim/Não/Cota reservada X%",
  "regime_execucao": "Empreitada por preço global / unitário / parcelada",
  "consorcio": "Permitido/Não permitido/Não mencionado",
  "observacoes_criticas": "...",
  "nivel_dificuldade": "BAIXO/MEDIO/ALTO",
  "recomendacao_acao": "...",
  "custo_logistico_nota": "..."
}
```

Salvar no JSON como `top20[].analise`.

### Step 7.5 — Filtro Pós-Análise (OBRIGATÓRIO)

Após a análise profunda, **REMOVER do top20** todos os editais onde:
- `recomendacao_acao` contém "NÃO PARTICIPAR" ou "DUPLICATA"
- Objeto é claramente incompatível com a atividade da empresa (ex: fornecimento de materiais quando a empresa é construtora)

Substituir os slots removidos pelos próximos editais elegíveis da lista de compatíveis dentro da capacidade.

**O relatório PDF deve conter APENAS editais RECOMENDADOS.** Editais descartados podem ser mencionados brevemente em uma nota ("X editais analisados mas descartados por incompatibilidade — ver planilha Excel para lista completa").

### Step 7.6 — Adendo: Oportunidades Acima da Capacidade (via Consórcio)

Se houver editais relevantes ACIMA da capacidade 10x que seriam excelentes oportunidades:
- Listar até 5 como "Oportunidades via Consórcio" em seção separada do relatório
- Mencionar apenas brevemente (objeto, valor, município, por que é interessante)
- NÃO fazer análise profunda — apenas sinalizar como potencial para expansão via consórcio

Também redigir:
- `resumo_executivo`: 2-3 parágrafos de visão geral
- `proximos_passos`: lista de ações priorizadas com deadlines

### Step 8 — Gerar PDF

```bash
python scripts/intel-report.py --input {DATA_JSON} --output {PDF_FILE}
```

### Step 9 — Report Results

Informar ao usuário:
- 📊 Excel: `{EXCEL_FILE}` — {N} editais ({M} compatíveis CNAE)
- 📋 PDF: `{PDF_FILE}` — Análise de {K} oportunidades recomendadas
- 💾 JSON: `{DATA_JSON}`
- Resumo: top 3 oportunidades com valor e prazo

---

## GUARDRAILS

1. **NUNCA pular o Step 3** (gate de ruído) — é obrigatório para zero noise
2. **NUNCA pular SICAF** — é obrigatório, sempre a primeira verificação cadastral
3. **NUNCA incluir Dispensa ou Inexigibilidade** — apenas modalidades competitivas
4. **NUNCA incluir editais acima da capacidade 10x no top 20** — estes vão apenas no adendo de consórcio
5. **NUNCA incluir duplicatas** — dedup por orgão/ano/sequencial e por similaridade de objeto+valor
6. **NUNCA incluir no relatório editais com recomendação "NÃO PARTICIPAR"** — apenas na planilha
7. **Planilha contém TODOS os editais** — sem filtro de valor/viabilidade
8. **PDF contém apenas editais RECOMENDADOS** dentro da capacidade
9. Se download de documentos falhar: marcar "Documentos indisponíveis — análise baseada no objeto" e analisar apenas com o texto do `objeto`
10. Se PyMuPDF/OCR não instalado: informar o usuário e prosseguir sem extração (análise limitada ao objeto)
11. **Limite de 15 páginas** no PDF — se 20 editais não cabem, priorizar os de maior valor

## Params

$ARGUMENTS
