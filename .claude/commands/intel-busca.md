# /intel-busca — Inteligência Estratégica de Editais por CNPJ

## Purpose

Busca exaustiva e análise profunda de editais abertos no PNCP para um CNPJ específico.
Zero ruído. Zero perda de oportunidades. Funciona para qualquer ramo de atividade.
Utiliza TODOS os CNAEs da empresa (principal + secundários) para máxima cobertura.

**Entregáveis:**
1. `docs/intel/intel-{CNPJ}-{YYYY-MM-DD}.xlsx` — Planilha completa com TODOS os editais
2. `docs/intel/intel-{CNPJ}-{YYYY-MM-DD}.pdf` — Relatório estratégico dos top 20 (max 15 páginas)

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
- `DATA_JSON = docs/intel/intel-{CNPJ}-{YYYY-MM-DD}.json`
- `EXCEL_FILE = docs/intel/intel-{CNPJ}-{YYYY-MM-DD}.xlsx`
- `PDF_FILE = docs/intel/intel-{CNPJ}-{YYYY-MM-DD}.pdf`

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

Ler o JSON. Filtrar editais onde:
- `cnae_compatible == true`
- `valor_estimado <= 10 * empresa.capital_social` (ou valor_estimado é null/sigiloso)

Ordenar por `valor_estimado` desc. Pegar os top 20.

Se menos de 20 disponíveis, usar todos os disponíveis.

### Step 6 — Download e Extração de Documentos

```bash
python scripts/intel-extract-docs.py --input {DATA_JSON} --top 20
```

O script automaticamente:
1. Filtra top 20 editais compatíveis dentro da capacidade (10× capital)
2. Prioriza documentos por relevância (edital > TR > planilha > outros)
3. Baixa até 3 documentos por edital (max 50MB cada)
4. Extrai texto: PDF (PyMuPDF + OCR fallback), ZIP/RAR (descompacta recursivamente), XLS/XLSX (openpyxl/xlrd)
5. Salva texto em `editais[].texto_documentos` e cria array `top20` no JSON

Verificar: quantos editais tiveram texto extraído? Algum falhou?

### Step 7 — Análise Profunda (Claude inline)

Para cada edital do top 20, ler o texto extraído dos documentos e produzir a análise estruturada:

```json
{
  "resumo_objeto": "...",
  "requisitos_tecnicos": ["...", "..."],
  "requisitos_habilitacao": ["...", "..."],
  "qualificacao_economica": "...",
  "prazo_execucao": "...",
  "garantias": "...",
  "criterio_julgamento": "...",
  "visita_tecnica": "Obrigatória/Facultativa/Não mencionada",
  "consorcio": "Permitido/Não permitido/Não mencionado",
  "observacoes_criticas": "...",
  "nivel_dificuldade": "BAIXO/MEDIO/ALTO",
  "recomendacao_acao": "..."
}
```

Salvar no JSON como `top20[].analise`.

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
- 📋 PDF: `{PDF_FILE}` — Análise de {K} oportunidades prioritárias
- 💾 JSON: `{DATA_JSON}`
- Resumo: top 3 oportunidades com valor e prazo

---

## GUARDRAILS

1. **NUNCA pular o Step 3** (gate de ruído) — é obrigatório para zero noise
2. **NUNCA incluir Dispensa ou Inexigibilidade** — apenas modalidades competitivas
3. **Planilha contém TODOS os editais** — sem filtro de valor/viabilidade
4. **PDF contém apenas top 20** dentro da capacidade
5. Se download de documentos falhar: marcar "Documentos indisponíveis — análise baseada no objeto" e analisar apenas com o texto do `objeto`
6. Se PyMuPDF/OCR não instalado: informar o usuário e prosseguir sem extração (análise limitada ao objeto)
7. **Limite de 15 páginas** no PDF — se 20 editais não cabem, priorizar os de maior valor

## Params

$ARGUMENTS
