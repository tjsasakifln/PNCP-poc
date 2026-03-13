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
8. **NUNCA incluir editais encerrados.** Editais com `dias_restantes <= 0` ou `status_edital == "ENCERRADO"` devem ser **descartados silenciosamente** — não aparecem no relatório, não recebem recomendação, não consomem API calls. O relatório existe para orientar AÇÃO; editais mortos são ruído.

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
- **Portal da Transparência** — Sanções (CEIS/CNEP/CEPIM/CEAF) + histórico de contratos federais
- **Mapeamento de setor** — CNAE → setor via `sectors_data.yaml` (keywords automáticas)
- **PNCP** — Editais abertos em 4 modalidades (Concorrência, Pregão Eletrônico/Presencial, Inexigibilidade), filtrados por keywords do setor + UFs
- **PCP v2** — Editais complementares com filtro client-side
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

**O script agora calcula automaticamente (Phase 1 v2):**
- **Índice de Viabilidade** — Nota 0-100 que mede quão viável é participar deste edital para ESTA empresa. Combina: modalidade (30%), prazo (25%), valor vs. capacidade (25%) e proximidade geográfica (20%). Em `editais[].risk_score`
- **Faturamento Potencial** — Estimativa de receita caso a empresa vença, baseado no valor do edital × margem típica do setor. "Chance de vitória" é uma estimativa baseada no perfil competitivo. Em `editais[].roi_potential`
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
2. **Análise de valor** — Valor estimado vs capital social e histórico da empresa.
3. **Análise geográfica** — Usar `distancia_km` do JSON (OSRM). Se `null`, escrever "Distância não calculada". **NUNCA estimar.**
4. **Análise de prazo** — Dias até encerramento. Tempo para preparar proposta?
5. **Análise de modalidade** — Pregão (preço) vs Concorrência (técnica+preço).
6. **Análise de habilitação** — Empresa atende requisitos? Cruzar checklist da Phase 2 com perfil:
   - Capital mínimo vs capital real
   - Atestados exigidos vs histórico de contratos
   - Se NÃO atende requisito crítico → NÃO RECOMENDADO com motivo
7. **Recomendação** — PARTICIPAR / AVALIAR COM CAUTELA / NÃO RECOMENDADO
8. **Justificativa (OBRIGATÓRIA)** — Motivo factual da recomendação. TODA recomendação DEVE ter justificativa. Para NÃO RECOMENDADO, explicar o motivo específico (ex: "Capital social R$X insuficiente para exigência de R$Y", "Distância 800km inviabiliza logística", "CNAE incompatível com objeto"). Para PARTICIPAR, explicar por que é viável. Para AVALIAR COM CAUTELA, explicar o risco específico.

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

## Estrutura do PDF Final (v2 Premium)

Numeração dinâmica — seções opcionais (QD, competitivo) só aparecem quando há dados.

1. **Capa** — Título, empresa, CNPJ, setor, data
2. **Decisão em 30 Segundos** — Tabela semáforo (●verde/amarelo/vermelho) com objeto, valor, prazo, risk score e justificativa 1-linha
3. **Perfil da Empresa** — Dados cadastrais, QSA, histórico gov, sanções
4. **Resumo Executivo** — Métricas-chave, destaques, distribuição UF
5. **Panorama de Oportunidades** — Tabela resumo com badges de confiança
6. **Análise Detalhada por Edital** — Ficha técnica + **Risk Score bar** (0-100 visual) + **ROI Potencial card** + **Cronograma Reverso** + análise por dimensão + recomendação
7. **Mapa Competitivo** — Contratos históricos dos órgãos, incumbentes, valores praticados (dados PNCP)
8. **Inteligência de Mercado** — Panorama, tendências, nichos, ranking
9. **Menções em Diários Oficiais** — Querido Diário (se houver)
10. **Próximos Passos** — Ações priorizadas com prazos
11. **Verificação SICAF** — Status cadastral (CRC), restrições, habilitações
12. **Fontes de Dados e Confiabilidade** — Tabela com status de cada API consultada
13. **Rodapé em todas as páginas:** "Tiago Sasaki - Consultor de Licitações (48)9 8834-4559"

---

## APIs Reference

| API | Endpoint | Auth | Rate Limit | Uso |
|-----|----------|------|------------|-----|
| OpenCNPJ | `api.opencnpj.org/{CNPJ}` | Nenhuma | 50 req/s | Perfil da empresa |
| Portal Transparência | `api.portaldatransparencia.gov.br/api-de-dados/` | `chave-api-dados` header | 90 req/min | Sanções + contratos |
| PNCP Consulta | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | Nenhuma | ~100 req/min | Editais (primário) |
| PNCP Arquivos | `pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos` | Nenhuma | ~60 req/min | Documentos do edital |
| PNCP Download | `pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{n}` | Nenhuma | ~30 req/min | Download PDF |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | Nenhuma | ~60 req/min | Editais complementares |
| Querido Diário | `api.queridodiario.ok.org.br/gazettes` | Nenhuma | ~60 req/min | Diários oficiais |
| Nominatim | `nominatim.openstreetmap.org/search` | Nenhuma | 1 req/s | Geocoding |
| OSRM | `router.project-osrm.org/route/v1/driving/` | Nenhuma | ~60 req/min | Distância rodoviária |

**Fontes testadas e descartadas (2026-03-10):** ComprasGov v3 (404), Comprasnet Contratos (500), Portal Transparência /licitacoes (0 resultados), TCE-PE (500), TCE-RJ (HTML não JSON). SICAF não possui API pública.

---

## Execution

Quando invocado:
1. **Phase 1:** Executar `collect-report-data.py` (coleta todas as APIs + SICAF via Playwright integrado)
2. **Phase 2:** Download + análise documental dos PDFs dos editais (Claude direto)
4. **Phase 3:** Análise estratégica cruzando perfil + edital + documento real
5. **Phase 4:** Inteligência competitiva (PNCP histórico + OpenCNPJ concorrentes)
6. **Phase 5:** Inteligência de mercado (panorama, tendências, nichos)
7. **Phase 6:** Enriquecer JSON + gerar PDF + gerar markdown
7. JSON final salvo em `docs/reports/data-{CNPJ}-{YYYY-MM-DD}.json`
8. PDF gerado em `docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.pdf`
9. Markdown em `docs/reports/report-{CNPJ}-{nome-slug}-{YYYY-MM-DD}.md`

**Tempo estimado:** 5-15 minutos dependendo do número de editais e PDFs.

## Params

$ARGUMENTS
