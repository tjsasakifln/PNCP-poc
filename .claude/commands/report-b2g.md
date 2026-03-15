# /report-b2g — Relatório Executivo de Oportunidades B2G

## Purpose

Gera um PDF executivo e institucional com TODAS as oportunidades abertas relevantes para um CNPJ específico, incluindo análise estratégica por edital e recomendações de ação.

**Output:** `docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.pdf`
**Rodapé:** "Tiago Sasaki - Consultor de Licitações (48)9 8834-4559"

---

## Usage

```
/report-b2g 12.345.678/0001-90
/report-b2g 12345678000190
```

## GUARDRAILS — REGRAS INVIOLÁVEIS

1. **NUNCA fabricar dados.** Todo dado factual (editais, valores, datas, CNPJs, órgãos, distâncias) DEVE vir de API ou do JSON coletado. Se uma API falhar, registrar `"status": "API_FAILED"` — NUNCA inventar valores plausíveis.
2. **NUNCA estimar distâncias.** Usar apenas o campo `distancia_km` do JSON (calculado via OSRM). Se `null`, escrever "Distância não calculada".
3. **NUNCA fabricar links.** Usar apenas `link` do JSON. Se vazio, omitir.
4. **Acentuação obrigatória.** Todo texto em português DEVE usar acentos corretos: "NÃO RECOMENDADO" (nunca "NAO"), "Concorrência" (nunca "Concorrencia"), etc.
5. **Transparência de fontes.** Cada seção do relatório deve indicar a fonte dos dados (API, documento, análise Claude).
6. **Se dados insuficientes, dizer.** "Dados insuficientes para análise" é preferível a qualquer estimativa sem fonte.
7. **Toda recomendação DEVE ter justificativa.** NUNCA emitir PARTICIPAR, AVALIAR COM CAUTELA ou NÃO RECOMENDADO sem `justificativa` preenchida com motivo factual específico. Uma recomendação sem justificativa é inaceitável.
8. **ZERO termos técnicos ou em inglês no PDF final.** Nenhuma menção a tecnologias (Playwright, httpx, OpenCNPJ, API, JSON, Python, etc.) deve aparecer no relatório entregue ao cliente. Na seção "Fontes de Dados", usar nomes institucionais: "Receita Federal", "Portal da Transparência", "Portal Nacional de Contratações Públicas", "Diários Oficiais Municipais", "Sistema de Cadastro de Fornecedores". Coluna "Detalhe" não pode conter termos como "raw", "filtered", "pages", "errors", "GET", "POST", "200 OK".
9. **NUNCA incluir editais encerrados ou descartados.** Editais com `dias_restantes <= 0`, `status_edital == "ENCERRADO"`, `recomendacao == "DESCARTADO"` ou `relevante == False` devem ser **excluídos do relatório** — não aparecem em nenhuma seção, não recebem análise, não consomem API calls. O Resumo Executivo deve citar quantas licitações foram descartadas e o motivo (ex: "5 licitações descartadas por falta de aderência aos CNAEs da empresa"). Editais com recomendação NÃO RECOMENDADO continuam no relatório — a decisão final cabe ao leitor.

---

## What It Does

### Phase 1: Coleta Determinística de Dados (script automatizado)

Executar o script de coleta que faz TODAS as chamadas de API de forma determinística e rastreável:

```bash
cd D:/pncp-poc
python scripts/collect-report-data.py \
  --cnpj {CNPJ} \
  --dias 30 \
  --ufs {UF_DA_EMPRESA} \
  --output docs/reports/data-{CNPJ}-{YYYY-MM-DD}.json
```

**O que o script coleta automaticamente:**
- **OpenCNPJ** — Perfil completo (razão social, CNAEs, capital social, QSA, telefones)
- **BrasilAPI** — Simples Nacional, MEI, fallback de porte (em `empresa.simples_nacional`, `empresa.mei`)
- **Portal da Transparência** — Sanções (CEIS/CNEP/CEPIM/CEAF) + histórico de contratos federais
- **Mapeamento de setor** — CNAE → setor via `sectors_data.yaml` (keywords automáticas)
- **PNCP** — Editais abertos em 4 modalidades (Concorrência, Pregão Eletrônico/Presencial, Inexigibilidade), filtrados por keywords do setor + UFs
- **PNCP /contratos expandido** — Histórico com aditivos (`valor_aditivos`), situação (`situacao_contrato`), subcontratação (`tem_subcontratacao`)
- **PCP v2** — Editais complementares com filtro client-side
- **IBGE SIDRA** — População + PIB municipal para cada município dos editais (em `editais[].ibge.populacao`, `editais[].ibge.pib_mil_reais`, `editais[].ibge.pib_per_capita`)
- **Querido Diário** — Menções em diários oficiais municipais
- **Distâncias** — Geocoding (Nominatim) + rota real (OSRM) para cada edital
- **Validação de links** — HEAD requests para verificar URLs dos editais

**Cada dado é tagueado com `_source`:**
```json
{
  "_source": {
    "status": "API",          // API | API_PARTIAL | API_FAILED | CALCULATED | UNAVAILABLE
    "timestamp": "2026-03-12T10:30:00",
    "detail": "OpenCNPJ 200 OK"
  }
}
```

**Flags opcionais:**
- `--skip-distances` — Pular cálculo de distâncias (mais rápido)
- `--skip-docs` — Pular listagem de documentos PNCP
- `--skip-links` — Pular validação de links
- `--skip-pcp` — Pular PCP v2
- `--skip-qd` — Pular Querido Diário
- `--skip-sicaf` — Pular verificação SICAF
- `--skip-competitive` — Pular coleta de inteligência competitiva
- `--skip-ibge` — Pular enriquecimento IBGE (população/PIB municipal)
- `--skip-brasilapi` — Pular consulta BrasilAPI (Simples Nacional)

**O script agora calcula automaticamente (Phase 1 v2):**
- **Índice de Viabilidade** — Nota 0-100 que mede quão viável é participar deste edital para ESTA empresa. Combina: modalidade (30%), prazo (25%), valor vs. capacidade (25%) e proximidade geográfica (20%). Em `editais[].risk_score`
- **Resultado Potencial** — Estimativa de lucro líquido caso a empresa vença, baseado no valor do edital × probabilidade de vitória × margem líquida do setor. Em `editais[].roi_potential`
- **Cronograma Reverso** — Marcos automáticos do deadline para trás em `editais[].cronograma`
- **Inteligência Competitiva** — Contratos históricos dos órgãos licitantes (PNCP 24 meses) em `editais[].competitive_intel`
- **Multi-setor** — CNAE mapeado para todos os 15 setores (não apenas engenharia)

**IMPORTANTE:** O script filtra automaticamente editais encerrados ANTES de gastar API calls com documentos, distâncias e inteligência competitiva. Apenas editais com prazo aberto entram no relatório.

**Após execução, VERIFICAR o output do script:**
- Quantos editais abertos foram encontrados?
- Alguma API falhou? (verificar `_metadata.sources`)
- Se PNCP retornou 0 editais abertos, considerar ampliar `--dias` ou `--ufs`

**SICAF integrado:** O script chama automaticamente `collect-sicaf.py` via subprocess:
- Abre navegador para o usuário resolver o hCaptcha (~5s por consulta)
- Coleta CRC (status cadastral, habilitações) + restrições
- Dados SICAF são incorporados diretamente no JSON de saída (`data.sicaf`)
- Use `--skip-sicaf` apenas se Playwright não estiver instalado

### Phase 2: Download e Análise Documental dos Editais (Claude direto)

**OBJETIVO:** Baixar os PDFs reais dos editais encontrados na Phase 1 e extrair insights factuais concretos.

**IMPORTANTE:** Esta análise é feita pelo próprio Claude (execução local), sem chamada a APIs de LLM externas.

#### 2.1. Descobrir documentos disponíveis

Para cada edital PNCP do JSON (campo `docs_url` se disponível, ou construir):

```bash
curl -s "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{anoCompra}/{sequencialCompra}/arquivos"
```

Response: JSON array com `tipoDocumentoNome`, `tipoDocumentoId`, `titulo`, `sequencialDocumento`, `url`.

**Prioridade de download:**
1. `tipoDocumentoId: 2` — Edital (obrigatório)
2. Termo de Referência (altamente relevante)
3. 1 anexo relevante (planilha, projeto básico)

**Máximo 3 documentos por edital.**

#### 2.2. Download e leitura dos PDFs

```bash
curl -s -o /tmp/edital_{id}.pdf \
  "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{sequencialDocumento}"
```

Ler com `Read(file_path="/tmp/edital_{id}.pdf", pages="1-20")`. Para editais longos, ler em blocos de 20 páginas.

Se PDF >10MB ou download falhar → registrar "Documento indisponível para análise".

#### 2.3. Extração factual do edital

Para CADA edital lido, extrair:

**A. Ficha Técnica** — Número, modalidade, critério de julgamento, modo de disputa, datas (abertura, impugnação, esclarecimentos), prazo de execução, prazo de vigência, local de execução, valor estimado (ou "sigiloso"), dotação orçamentária.

**B. Requisitos de Habilitação (checklist)** — Jurídica, fiscal federal/estadual/municipal, qualificação técnica (atestados, equipe, visita), econômico-financeira (índices, patrimônio líquido, capital mínimo), garantias, amostra, certidões de sanções.

**C. Condições Comerciais** — Subcontratação, consórcio, ME/EPP, margem de preferência, prazo de pagamento, reajuste, penalidades.

**D. Red Flags** — Prazo apertado, exigências restritivas, valor desalinhado, cláusulas incomuns, direcionamento suspeito, impugnação viável.

**E. Resumo Executivo** — 2-3 parágrafos: escopo real, requisitos-chave, principal risco/oportunidade.

#### 2.4. Editais PCP v2

Para editais sem endpoint PNCP de arquivos:
- Se `numero_controle_pncp` disponível, tentar construir URL PNCP
- Se não disponível → "Análise documental não realizada — edital disponível apenas no portal PCP"

### Phase 3: Análise Estratégica por Edital (Claude)

Para CADA edital, cruzar dados do JSON (Phase 1) + análise documental (Phase 2) + perfil da empresa.

**USE os campos pré-calculados pelo script:**
- `risk_score.total` (0-100) → INFORMAR a recomendação. Score ≥60 favorece PARTICIPAR, 30-60 = AVALIAR, <30 = NÃO RECOMENDADO.
- `roi_potential` → Citar no relatório como "ROI Potencial: R$X — R$Y"
- `cronograma` → Usar na seção de Próximos Passos e alertas de prazo
- `competitive_intel` → Usar na análise de competitividade por edital

**Análises a produzir por edital:**

1. **Aderência ao perfil** — CNAEs vs objeto real. (Alta/Média/Baixa)
2. **Análise de valor** — Valor estimado vs capital social e histórico da empresa. Se `empresa.simples_nacional == true` e valor > R$4,8M: alertar incompatibilidade com regime Simples. Se `empresa.mei == true` e valor > R$81k: alertar bloqueio MEI.
3. **Análise geográfica** — Usar `distancia_km` do JSON (OSRM). Se `null`, escrever "Distância não calculada". **NUNCA estimar.** Usar `editais[].ibge.populacao` e `editais[].ibge.pib_mil_reais` para contextualizar porte do município (ex: "Município de 3.000 habitantes licitando R$20M — risco fiscal elevado"). Se PIB per capita baixo, alertar sobre capacidade fiscal do órgão.
4. **Análise de prazo** — Dias até encerramento. Tempo para preparar proposta?
5. **Análise de modalidade** — Pregão (preço) vs Concorrência (técnica+preço).
6. **Análise de habilitação** — Empresa atende requisitos? Cruzar checklist da Phase 2 com perfil:
   - Capital mínimo vs capital real
   - Atestados exigidos vs histórico de contratos
   - Simples Nacional / MEI vs limites de faturamento
   - Se NÃO atende requisito crítico → NÃO RECOMENDADO com motivo
7. **Análise de aditivos** — Se `competitive_intel` mostra contratos com `valor_aditivos > 0` ou `situacao_contrato == "3" (rescindido)`, alertar sobre padrão do órgão. Aditivos frequentes = risco de escopo mal definido. Rescisões = red flag.
8. **Divergência setorial** — Se `qualification_gap.gap_type == "ACERVO_SETOR_DIVERGENTE"`, a empresa tem CNAE no setor mas contratos históricos em segmento distinto. Neste caso: **NÃO invalidar o edital como NÃO RECOMENDADO**. Em vez disso, recomendar **AVALIAR COM CAUTELA** com justificativa "Participação depende de confirmação de acervo técnico no setor — verificar CATs e atestados reais da empresa". O alerta de divergência setorial já aparece no topo do relatório; a análise por edital deve complementar, não repetir.
9. **Análise de consórcio e subcontratação** — Se o edital permite consórcio (`permite_consorcio`) e a empresa tem barreiras de capital, acervo ou capacidade operacional, sugerir consórcio como alternativa viável. Se o edital permite subcontratação (`permite_subcontratacao`), identificar componentes fora do core que podem ser subcontratados. Definir `alternativa_participacao`: "INDIVIDUAL", "CONSORCIO_RECOMENDADO" (quando há barreiras superáveis via consórcio), ou "SUBCONTRATACAO_PARCIAL" (quando componentes específicos excedem a capacidade operacional). Incluir na justificativa quando aplicável.
10. **Recomendação** — PARTICIPAR / AVALIAR COM CAUTELA / NÃO RECOMENDADO. **Editais VETADOS pelo script (sanção, capital insuficiente, limite MEI/Simples) já vêm com `risk_score.vetoed=true` e `risk_score.veto_reasons` — estes devem ser marcados como NÃO RECOMENDADO com justificativa citando o veto específico.**
11. **Justificativa (OBRIGATÓRIA)** — Motivo factual da recomendação. TODA recomendação DEVE ter justificativa. Para NÃO RECOMENDADO, explicar o motivo específico (ex: "Capital social R$X insuficiente para exigência de R$Y", "Distância 800km inviabiliza logística", "CNAE incompatível com objeto"). Para PARTICIPAR, explicar por que é viável. Para AVALIAR COM CAUTELA, explicar o risco específico. **Para editais com risco fiscal ALTO (`risk_score.fiscal_risk.nivel == "ALTO"`), obrigatoriamente mencionar o risco fiscal na justificativa.** Para editais com `acervo_confirmado=false`, incluir nota sobre necessidade de verificação de atestados técnicos.

### Phase 4: Inteligência Competitiva (Claude + API)

Para editais com recomendação PARTICIPAR ou AVALIAR COM CAUTELA:

**4.1. Incumbentes do órgão**
```bash
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
  ?dataInicial={24_meses_atras_YYYYMMDD}\
  &dataFinal={hoje_YYYYMMDD}\
  &codigoUnidadeAdministrativa={codigo_orgao}\
  &pagina=1&tamanhoPagina=50"
```

**4.2. Perfil dos concorrentes (top 5)**
```bash
curl -s "https://api.opencnpj.org/${CNPJ_CONCORRENTE}"
```

**4.3. Análise por edital** — Concorrentes prováveis, incumbente principal, preço médio praticado, desconto médio, porte dos concorrentes, vantagem/vulnerabilidade, estratégia sugerida.

**4.4. Mapa de calor competitivo** — Baixa (<3 fornecedores) / Média (3-5) / Alta (5-10) / Muito Alta (>10 ou incumbente >60%).

### Phase 5: Inteligência de Mercado (Claude)

1. **Panorama setorial** — Editais abertos, valor total, concentração por UF
2. **Tendências** — Modalidades comuns, valores médios, órgãos mais ativos
3. **Vantagens competitivas** — Baseado em perfil (porte, localização, CNAEs)
4. **Oportunidades de nicho** — Órgãos/UFs com pouca competição
5. **Recomendação geral** — Priorização por potencial vs esforço vs competição

### Phase 6: Montagem do JSON e Geração do PDF

**6.1. Montar/enriquecer o JSON de dados**

O JSON da Phase 1 deve ser enriquecido com as análises das Phases 2-5:
- `resumo_executivo` — Métricas consolidadas
- `editais[].analise_documental` — Ficha técnica, habilitação, red flags (Phase 2)
- `editais[].recomendacao` — PARTICIPAR/AVALIAR COM CAUTELA/NÃO RECOMENDADO
- `editais[].justificativa` — **OBRIGATÓRIO.** Motivo factual da recomendação. NUNCA deixar vazio.
- `editais[].analise_detalhada` — Texto analítico completo (Phases 3-4)
- `inteligencia_mercado` — Panorama, tendências, nichos (Phase 5)
- `proximos_passos` — Lista de ações priorizadas

**6.2. Gerar o PDF**
```bash
cd D:/pncp-poc
python scripts/generate-report-b2g.py \
  --input docs/reports/data-{CNPJ}-{YYYY-MM-DD}.json \
  --output docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.pdf
```

**6.3. Gerar markdown resumido**

Salvar versão markdown em `docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.md`.

---

## Estrutura do PDF Final (v4 — Arquitetura de 3 Camadas)

Numeração dinâmica — seções opcionais só aparecem quando há dados. Toda referência a edital é clicável (hyperlink para fonte oficial PNCP/PCP).

### Camada 1 — Decisão Executiva (máx. 3 páginas)

O decisor lê SÓ estas páginas e já sabe o que fazer.

1. **Capa** — Título, empresa, CNPJ, setor, data. Badge Simples/MEI se aplicável.
2. **Aviso de Cobertura** (condicional) — Banner âmbar se taxa de captura < 70% (E3)
3. **Resumo Executivo** — Tabela de métricas-chave (editais encontrados, PARTICIPAR/AVALIAR/NR, valor total, ROI agregado, cobertura) + max 3 destaques
4. **Decisão em 30 Segundos** — Agrupada por recomendação: PARTICIPAR primeiro, AVALIAR segundo, NÃO RECOMENDADO resumido em 1 bloco de 3 linhas (detalhe no Anexo A). Cada edital com: município (+ pop/PIB IBGE inline), objeto (clicável), valor, prazo, score, diferencial

### Camada 2 — Inteligência Estratégica (3-5 páginas)

Para quem quer entender o contexto antes de agir.

5. **Inteligência Exclusiva** — 4 diferenciais (incumbência, viabilidade calibrada, acervo, clusters)
6. **Análise Detalhada** — **SÓ editais PARTICIPAR e AVALIAR COM CAUTELA.** Fichas compactas com barras visuais por dimensão (aderência/financeiro/geográfico/prazo/competitivo), alertas condicionais (⚠ IBGE pop/PIB, ⚠ Simples/MEI, ⚠ aditivos do órgão), cronograma em 1 linha. Títulos clicáveis para fonte oficial. ~20 linhas por edital (vs ~50 antes).
7. **Portfólio + Regional** (unificado) — Quick Wins / Oportunidades / Investimentos / Inacessíveis + Clusters geográficos com PIB agregado (IBGE)
8. **Mapa Competitivo** — Fornecedores recorrentes + aditivos/rescisões (PNCP expandido) + mercados favoráveis. Condensado.
9. **Inteligência de Mercado** — Panorama, tendências, vantagens, recomendação geral
10. **Plano de Desenvolvimento** — Lacunas consolidadas com ações e prazos
11. **Próximos Passos** — Ações priorizadas com prazos

### Camada 3 — Anexos (referência)

Material de consulta, fora do fluxo principal.

- **Anexo A — Editais Não Recomendados** — Tabela condensada: nº, município/objeto (clicável), valor, motivo (1 linha cada). Max 1 página.
- **Anexo B — Perfil da Empresa** — Dados cadastrais, QSA, regime tributário (BrasilAPI: Simples/MEI/Geral), sanções, SICAF, maturidade (E8), histórico de contratos
- **Anexo C — Fontes de Dados e Metodologia** — Tabela de fontes (nomes institucionais, status, detalhe) + Querido Diário (se houver menções)

**Rodapé em todas as páginas:** "Tiago Sasaki — Consultor de Inteligência em Licitações"

**Regras visuais:**
- Recomendações coloridas: PARTICIPAR (verde), AVALIAR COM CAUTELA (âmbar), NÃO RECOMENDADO (vermelho)
- "Resultado Potencial" (não "Faturamento") — cálculo: valor × probabilidade × margem líquida setorial
- Números em formato brasileiro: vírgula decimal, ponto milhar (12,5% não 12.5%)
- Palavras nunca quebram no meio (wordWrap CJK)

---

## APIs Reference

| API | Endpoint | Auth | Rate Limit | Uso |
|-----|----------|------|------------|-----|
| OpenCNPJ | `api.opencnpj.org/{CNPJ}` | Nenhuma | 50 req/s | Perfil da empresa |
| Portal Transparência | `api.portaldatransparencia.gov.br/api-de-dados/` | `chave-api-dados` header (env: `PORTAL_TRANSPARENCIA_API_KEY` em `backend/.env`) | 90 req/min | Sanções + contratos — **OBRIGATÓRIO usar a chave configurada** |
| PNCP Consulta | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | Nenhuma | ~100 req/min | Editais (primário) |
| PNCP Arquivos | `pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos` | Nenhuma | ~60 req/min | Documentos do edital |
| PNCP Download | `pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{n}` | Nenhuma | ~30 req/min | Download PDF |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | Nenhuma | ~60 req/min | Editais complementares |
| Querido Diário | `api.queridodiario.ok.org.br/gazettes` | Nenhuma | ~60 req/min | Diários oficiais |
| Nominatim | `nominatim.openstreetmap.org/search` | Nenhuma | 1 req/s | Geocoding |
| OSRM | `router.project-osrm.org/route/v1/driving/` | Nenhuma | ~60 req/min | Distância rodoviária |
| BrasilAPI | `brasilapi.com.br/api/cnpj/v1/{cnpj}` | Nenhuma | ~3 req/s | Simples Nacional + MEI + fallback porte |
| IBGE Localidades | `servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios` | Nenhuma | ~1 req/s | Código IBGE do município |
| IBGE SIDRA | `apisidra.ibge.gov.br/values/t/{tabela}/n6/{cod}/v/{var}/p/last` | Nenhuma | ~1 req/s | População (tabela 6579) + PIB (tabela 5938) |

**Fontes testadas e descartadas (2026-03-10):** ComprasGov v3 (404), Comprasnet Contratos (500), Portal Transparência /licitacoes (0 resultados), TCE-PE (500), TCE-RJ (HTML não JSON). SICAF não possui API pública.
**Fontes avaliadas e rejeitadas (2026-03-14):** Base dos Dados/BigQuery (dependência GCP), TCU Webservices (só licitações próprias), CND Federal (exige e-CNPJ), CAGED/RAIS (requer solicitação formal MTE).

---

## Execution

Quando invocado:
1. **Phase 1:** Executar `collect-report-data.py` (coleta todas as APIs + SICAF via Playwright integrado)
2. **Phase 1.5 — GATE DETERMINÍSTICO (OBRIGATÓRIO):** Executar `validate-report-data.py` no JSON. Se BLOCKED → PARAR, informar o motivo, NÃO prosseguir. Se WARNINGS → listar todos os alertas e endereçar CADA UM no relatório.
3. **Phase 2:** Download + análise documental dos PDFs dos editais (Claude direto)
4. **Phase 3:** Análise estratégica cruzando perfil + edital + documento real
5. **Phase 4:** Inteligência competitiva (PNCP histórico + OpenCNPJ concorrentes)
6. **Phase 5:** Inteligência de mercado (panorama, tendências, nichos)
7. **Phase 6:** Enriquecer JSON + gerar PDF + gerar markdown
8. **Phase 7 — GATE ADVERSARIAL (OBRIGATÓRIO):** Revisão com persona do leitor. Se QUALQUER item falhar → corrigir e re-gerar.
9. JSON final salvo em `docs/reports/data-{CNPJ}-{YYYY-MM-DD}.json`
10. PDF gerado em `docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.pdf`
11. Markdown em `docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.md`

### Phase 1.5: Gate Determinístico (script automatizado)

```bash
python scripts/validate-report-data.py docs/reports/data-{CNPJ}-{YYYY-MM-DD}.json
```

O script verifica coerência semântica dos dados ANTES de gerar o relatório:

| Verificação | Se falhar |
|-------------|-----------|
| Keywords vieram do histórico ou do CNAE fallback? | BLOCK se fallback com >10 contratos |
| Cluster dominante bate com os editais encontrados? | BLOCK se <10% de match |
| Divergência setorial (CNAE ≠ histórico)? | BLOCK se zero contratos no setor |
| >90% dos editais com habilitação parcial? | WARN — rebaixar recomendações |
| Todas as probabilidades de vitória <5%? | WARN — transparência obrigatória |
| Todos os ROIs negativos? | WARN — classificar como investimento |
| Fontes obrigatórias falharam? | BLOCK |

**Exit codes:** 0 = OK, 1 = BLOCKED (parar), 2 = WARNINGS (endereçar no relatório).

**Se BLOCKED:** Informar o usuário qual verificação falhou e sugerir ação corretiva. NÃO prosseguir com Phases 2-7.

**Se WARNINGS:** Listar cada alerta no início da Phase 2 e garantir que o relatório final endereça TODOS.

### Phase 7: Gate Adversarial — Revisão com Persona do Leitor

**OBJETIVO:** O agente DEVE abandonar a perspectiva de quem gerou o relatório e assumir a persona do DONO DO CNPJ — o empresário que vai ler este documento para decidir onde investir tempo e dinheiro.

**COMO EXECUTAR:**

1. **Reler o markdown completo** com a seguinte persona:

> "Eu sou o dono da empresa [RAZÃO SOCIAL]. Pago R$X por este relatório. Tenho 10 minutos para ler. Quero saber: em quais licitações devo investir meu tempo esta semana? Se o relatório não me disser isso de forma clara e honesta, foi dinheiro jogado fora."

2. **Para CADA seção do relatório, perguntar:**

| Pergunta | Se a resposta for NÃO |
|----------|----------------------|
| "Isso me ajuda a decidir algo CONCRETO?" | Cortar ou reescrever — texto que não gera ação é enchimento |
| "Eu confiaria meu dinheiro nesta recomendação?" | Adicionar ressalvas ou rebaixar recomendação |
| "Isso é informação que eu não conseguiria sozinho em 5 minutos?" | Cortar — o leitor paga por inteligência, não por compilação de dados públicos |
| "Se eu seguir este conselho e perder, o relatório me avisou do risco?" | Adicionar alerta explícito |
| "Tem alguma frase que eu precisaria ler duas vezes para entender?" | Reescrever mais simples |
| "Tem algo repetido que já li em outra seção?" | Consolidar — repetição destrói credibilidade |
| "Os números fazem sentido para uma empresa do meu porte?" | Se R$2M de capital e edital exige R$20M, a recomendação PARTICIPAR é desonesta |

3. **Teste do "E daí?"** — Para cada parágrafo: se o leitor pode responder "e daí?", o parágrafo não agrega valor. Exemplos:

- ❌ "O mercado de obras públicas atravessa período de alta demanda" → E daí? Isso não me diz em qual edital participar.
- ✅ "Bofete/SP (R$3,3M) é a melhor oportunidade: 13,5% de chance, prazo de 73 dias, consórcio permitido. Decisão até 15/04." → Ação clara.

4. **Teste de honestidade** — Para cada recomendação PARTICIPAR:

- A empresa tem CAT/atestado para este tipo de obra? Se não confirmado → não é PARTICIPAR, é AVALIAR COM CAUTELA.
- O ROI é positivo ou é investimento? Se investimento → dizer explicitamente "você vai gastar R$X para construir acervo, sem retorno financeiro direto".
- A probabilidade é realista? Se 3% → dizer "em média, você precisaria participar de ~33 licitações para vencer 1".

5. **Registrar resultado** — Após a revisão adversarial, incluir no JSON:

```json
"delivery_validation": {
    "gate_deterministic": "OK|WARNINGS|BLOCKED",
    "gate_adversarial": "PASSED|REVISED",
    "revisions_made": ["Rebaixado São Paulo de PARTICIPAR para AVALIAR (CAT não confirmado)", ...],
    "reader_persona": "Empresário de EPP, 10min de atenção, busca ação concreta"
}
```

### Checklist de Formato (complementar — verificar APÓS o gate adversarial)

- [ ] Datas em DD/MM/YYYY
- [ ] Números em formato brasileiro (vírgula decimal, ponto milhar)
- [ ] Zero termos em inglês ou técnicos no PDF
- [ ] Rodapé presente em todas as páginas
- [ ] Links de editais clicáveis e validados
- [ ] Seção de Fontes com nomes institucionais (não técnicos)

**Se QUALQUER revisão adversarial gerou mudança:** re-gerar PDF e markdown com as correções.

## Params

$ARGUMENTS
