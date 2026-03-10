# /report-b2g — Relatório Executivo de Oportunidades B2G

## Purpose

Gera um PDF executivo e institucional com TODAS as oportunidades abertas relevantes para um CNPJ específico, incluindo análise estratégica por edital e recomendações de ação.

**Output:** `docs/reports/report-{CNPJ}-{YYYY-MM-DD}.pdf`
**Rodapé:** "Tiago Sasaki - Consultor de Licitações (48)9 8834-4559"

---

## Usage

```
/report-b2g 12.345.678/0001-90
/report-b2g 12345678000190
```

## What It Does

### Phase 1: Perfil da Empresa (@data-engineer)

1. **OpenCNPJ** — Buscar dados cadastrais completos
   ```bash
   CNPJ_LIMPO=$(echo "{CNPJ}" | tr -d './-')
   curl -s "https://api.opencnpj.org/${CNPJ_LIMPO}"
   ```
   Extrair: razão social, nome fantasia, CNAE principal + secundários, porte, capital social, cidade/UF, email, telefones, QSA, situação cadastral.

2. **Mapear setor** — Cruzar CNAE principal com `backend/sectors_data.yaml` para identificar o setor de atuação e keywords relevantes. Se CNAE não tem match direto, usar CNAEs secundários. Se nenhum match, usar descrição do CNAE como keyword.

3. **Portal da Transparência** — Check de sanções + histórico de contratos federais
   ```bash
   PT_KEY=$(grep PORTAL_TRANSPARENCIA_API_KEY backend/.env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
   curl -s -H "chave-api-dados: ${PT_KEY}" \
     "https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-juridica?cnpj=${CNPJ_LIMPO}"
   curl -s -H "chave-api-dados: ${PT_KEY}" \
     "https://api.portaldatransparencia.gov.br/api-de-dados/contratos/cpf-cnpj?cpfCnpj=${CNPJ_LIMPO}&pagina=1"
   ```
   Verificar sanções (CEIS, CNEP, CEPIM, CEAF) e extrair histórico de contratos federais.

### Phase 2: Varredura de Editais Abertos (@data-engineer)

**2a. PNCP (obrigatório)**
```bash
# Buscar publicações abertas (últimos 30 dias)
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
  ?dataInicial={30_dias_atras_YYYYMMDD}\
  &dataFinal={hoje_YYYYMMDD}\
  &codigoModalidadeContratacao=5\
  &pagina=1&tamanhoPagina=50"
```
- Buscar com TODAS as modalidades relevantes: 4 (Concorrência), 5 (Pregão Eletrônico), 6 (Pregão Presencial), 8 (Inexigibilidade)
- Filtrar `objetoCompra` por keywords do setor mapeado na Phase 1
- Paginar até esgotar ou timeout (max 10 páginas por modalidade)
- Extrair: objeto, órgão, UF, município, valor estimado, modalidade, data abertura/encerramento, link PNCP

**2b. PCP v2 (obrigatório)**
```bash
curl -s "https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos?page=1"
```
- Paginar (10/page, usar `nextPage`)
- Filtrar client-side por keywords do setor
- PCP v2 não tem campo UF no servidor — filtrar client-side
- valor_estimado sempre 0.0 (PCP v2 não tem dados de valor)

**2c. Querido Diário (complementar — diários oficiais municipais)**
```bash
# Buscar por nome da empresa + keywords do setor nos diários oficiais
curl -s "https://api.queridodiario.ok.org.br/gazettes\
  ?querystring={keywords_setor_url_encoded}\
  &excerpt_size=500\
  &number_of_excerpts=3\
  &size=20"
```
- API retorna JSON (não HTML) com excerpts de texto dos diários oficiais
- Sem parâmetro de CNPJ — buscar por keywords do setor
- Buscar também pelo nome fantasia da empresa para menções diretas
- Não tem data range — resultados são os mais recentes
- Rate limit: ~60 req/min (self-imposed)
- Extrair: data publicação, território (município), excerpts com contexto
- IMPORTANTE: Querido Diário é texto OCR não estruturado — usar como fonte complementar, não primária

**Dedup:** Se mesmo edital aparece em PNCP + PCP, priorizar dados PNCP (mais completos).

### Phase 3: Análise Estratégica por Edital (@analyst)

Para CADA edital encontrado, o agente deve analisar e gerar:

1. **Aderência ao perfil** — O objeto do edital é compatível com os CNAEs da empresa? (Alta/Média/Baixa)
2. **Análise de valor** — O valor estimado está dentro da faixa operacional da empresa (baseado em capital social e histórico)?
3. **Análise geográfica** — Distância da sede ao local de execução. A empresa já atua naquela UF?
4. **Análise de prazo** — Dias restantes até encerramento. Tempo suficiente para preparar proposta?
5. **Análise de modalidade** — Pregão (preço) vs Concorrência (técnica+preço). Qual exige mais preparação?
6. **Competitividade** — Baseado no histórico do órgão, qual o padrão de desconto? Existem incumbentes?
7. **Riscos e alertas** — Prazos apertados, valores atípicos, requisitos de qualificação técnica específicos
8. **Recomendação** — PARTICIPAR / AVALIAR COM CAUTELA / NÃO RECOMENDADO
9. **Perguntas do decisor respondidas:**
   - "Vale a pena participar?"
   - "Quanto eu deveria ofertar?"
   - "Quem são os concorrentes prováveis?"
   - "Quais documentos preciso preparar?"
   - "Qual o risco de não conseguir executar?"
   - "Esse órgão paga em dia?"
   - "Existe alguma restrição que me impeça de participar?"

### Phase 4: Inteligência de Mercado (@analyst)

1. **Panorama setorial** — Quantos editais abertos no setor, valor total em jogo, concentração por UF
2. **Tendências** — Modalidades mais comuns, valores médios, órgãos mais ativos
3. **Vantagens competitivas da empresa** — Baseado no perfil (porte, localização, CNAEs, histórico)
4. **Recomendação geral** — Priorização dos editais por potencial de retorno vs esforço

### Phase 5: Geração do PDF (@dev)

Executar o script de geração:
```bash
cd D:/pncp-poc
python scripts/generate-report-b2g.py --input docs/reports/data-{CNPJ}-{data}.json --output docs/reports/report-{CNPJ}-{data}.pdf
```

O JSON de input deve ser criado pelo agente com toda a informação coletada nas fases anteriores.

**Estrutura do PDF:**
1. **Capa** — Título, nome da empresa, CNPJ, setor, data
2. **Perfil da Empresa** — Dados cadastrais, QSA, histórico gov, sanções
3. **Resumo Executivo** — Métricas chave, destaques, recomendação geral
4. **Panorama de Oportunidades** — Tabela resumo, distribuição por UF/modalidade/valor
5. **Análise Detalhada por Edital** — Uma seção por edital com todos os itens da Phase 3
6. **Inteligência de Mercado** — Tendências, competitividade, vantagens
7. **Menções em Diários Oficiais** — Resultados do Querido Diário (se houver)
8. **Próximos Passos** — Ações recomendadas com prioridade e prazo
9. **Rodapé em todas as páginas:** "Tiago Sasaki - Consultor de Licitações (48)9 8834-4559"

---

## APIs Reference

| API | Endpoint | Auth | Rate Limit |
|-----|----------|------|------------|
| OpenCNPJ | `api.opencnpj.org/{CNPJ}` | Nenhuma | 50 req/s |
| Portal Transparência | `api.portaldatransparencia.gov.br/api-de-dados/` | `chave-api-dados` header | 90 req/min |
| PNCP | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | Nenhuma | ~100 req/min |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | Nenhuma | ~60 req/min |
| Querido Diário | `api.queridodiario.ok.org.br/gazettes` | Nenhuma | ~60 req/min |

## Execution

Quando invocado:
1. Agentes Claude Code executam as 5 fases sequencialmente
2. Dados intermediários salvos em `docs/reports/data-{CNPJ}-{data}.json`
3. PDF final gerado em `docs/reports/report-{CNPJ}-{data}.pdf`
4. Relatório Markdown resumido em `docs/reports/report-{CNPJ}-{data}.md`

## Params

$ARGUMENTS
