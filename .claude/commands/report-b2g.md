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
- **LINK PNCP (CRÍTICO):** Cada resultado da API PNCP retorna os campos `cnpjCompra` (ou `cnpjOrgao`), `anoCompra` e `sequencialCompra`. O link correto é:
  ```
  https://pncp.gov.br/app/editais/{cnpjCompra}/{anoCompra}/{sequencialCompra}
  ```
  Exemplo: `https://pncp.gov.br/app/editais/27142058000126/2026/85`
  **NUNCA use hyphens** (errado: `27142058000126-2026-85`). **NUNCA fabrique URLs de busca** (errado: `?q=reforma+obra`).
  Se o campo `linkSistemaOrigem` estiver presente no resultado da API, usar ele diretamente.
  Se nenhum campo de link estiver disponível, usar o `numeroControlePNCP` no formato: `https://pncp.gov.br/app/editais/{numeroControlePNCP}` (onde numeroControlePNCP já contém cnpj/ano/seq separados por `-`, mas o link usa o valor como path único).

**2b. PCP v2 (obrigatório)**
```bash
curl -s "https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos?page=1"
```
- Paginar (10/page, usar `nextPage`)
- Filtrar client-side por keywords do setor
- PCP v2 não tem campo UF no servidor — filtrar client-side
- valor_estimado sempre 0.0 (PCP v2 não tem dados de valor)
- **LINK PCP v2:** Cada resultado tem campo `url` ou pode ser construído a partir de `id`. Se não tiver URL direta, usar `https://www.portaldecompraspublicas.com.br/processos/{id}`. Se o edital também tem `numeroControlePNCP`, construir o link PNCP: `https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}`

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

### Phase 2b: Download e Análise Documental dos Editais (Claude direto)

**OBJETIVO:** Baixar os PDFs reais dos editais encontrados na Phase 2 e extrair insights factuais concretos — em vez de recomendações genéricas como "vale conferir o edital", entregar fatos extraídos do documento.

**IMPORTANTE:** Esta análise é feita pelo próprio Claude (execução local do command), sem chamada a APIs de LLM externas.

#### 2b.1. Descobrir documentos disponíveis

Para cada edital PNCP encontrado na Phase 2a, buscar os documentos publicados:

```bash
# Endpoint descoberto: API interna PNCP de arquivos
# Padrão: /api/pncp/v1/orgaos/{cnpj_orgao}/compras/{ano}/{sequencial}/arquivos
curl -s "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{anoCompra}/{sequencialCompra}/arquivos"
```

**Response esperada (JSON array):**
```json
[
  {
    "uri": "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/1",
    "url": "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/1",
    "tipoDocumentoNome": "Edital",
    "tipoDocumentoId": 2,
    "tipoDocumentoDescricao": "Edital",
    "titulo": "EDITAL PREGAO ELETRONICO 012026",
    "sequencialDocumento": 1,
    "statusAtivo": true
  },
  {
    "tipoDocumentoNome": "Outros Documentos",
    "titulo": "Termo de Referência",
    "sequencialDocumento": 2
  }
]
```

**Tipos de documento relevantes (prioridade de download):**
1. `tipoDocumentoId: 2` — **Edital** (obrigatório — documento principal)
2. `tipoDocumentoNome: "Termo de Referência"` ou `"TR"` (altamente relevante — detalha o escopo)
3. `tipoDocumentoNome: "Outros Documentos"` cujo `titulo` contenha: "anexo", "planilha", "projeto basico" (quando disponível)

**Regra de download:** Baixar no máximo 3 documentos por edital (Edital + TR + 1 anexo relevante) para não sobrecarregar a análise.

#### 2b.2. Download dos PDFs

```bash
# Download direto — sem autenticação, CORS aberto
# O endpoint retorna o PDF com header: content-disposition: attachment; filename="nome.pdf"
curl -s -o /tmp/edital_{cnpj}_{ano}_{seq}.pdf \
  "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{sequencialDocumento}"
```

**Constraints:**
- Arquivos tipicamente entre 200KB-5MB (editais de pregão)
- Alguns podem ser >10MB (editais de obras com projetos)
- Se download falhar ou arquivo >10MB, pular e registrar "Documento indisponível para análise"
- Rate limit self-imposed: max 2 downloads simultâneos, 1s entre requests

#### 2b.3. Extração de texto do PDF

**Opção 1 (preferida):** Usar a ferramenta `Read` do Claude Code que suporta leitura de PDFs nativamente.
```
Read(file_path="/tmp/edital_{cnpj}_{ano}_{seq}.pdf", pages="1-20")
```
- Claude Code lê PDFs diretamente (multimodal)
- Limitar a 20 páginas por request (limite da ferramenta)
- Para editais longos (>20 páginas), ler em blocos: pages="1-20", depois "21-40", etc.

**Opção 2 (fallback):** Se o PDF não for legível (scan/imagem), registrar "PDF não-textual — análise visual limitada" e tentar ler as primeiras 10 páginas que frequentemente contêm o resumo.

#### 2b.4. Análise documental pelo Claude

Para CADA edital cujo PDF foi lido com sucesso, Claude deve extrair e analisar:

**A. Ficha Técnica do Edital (fatos puros — sem interpretação)**

| Campo | Onde encontrar no edital |
|-------|------------------------|
| Número do edital | Cabeçalho / primeira página |
| Modalidade e tipo | Preâmbulo |
| Critério de julgamento | "menor preço" / "técnica e preço" / "maior desconto" |
| Modo de disputa | Aberto / Fechado / Aberto-Fechado |
| Data e hora de abertura | Seção de prazos |
| Data limite para impugnação | Seção de prazos |
| Data limite para esclarecimentos | Seção de prazos |
| Prazo de execução/entrega | Cláusula contratual ou Termo de Referência |
| Prazo de vigência do contrato | Cláusula contratual |
| Local de execução/entrega | Termo de Referência ou cláusula específica |
| Valor estimado (se divulgado) | Pode ser sigiloso — registrar "sigiloso" se não informado |
| Fonte de recursos / dotação orçamentária | Seção financeira |

**B. Requisitos de Habilitação (checklist factual)**

| Requisito | Presente? | Detalhe extraído |
|-----------|-----------|-----------------|
| Habilitação jurídica | Sim/Não | Quais documentos específicos |
| Regularidade fiscal federal | Sim/Não | CND, FGTS, Trabalhista |
| Regularidade fiscal estadual/municipal | Sim/Não | Quais certidões |
| Qualificação técnica — atestados | Sim/Não | Quantidade mínima, percentuais, objetos similares exigidos |
| Qualificação técnica — equipe | Sim/Não | Profissionais exigidos (engenheiro, etc.) |
| Qualificação técnica — visita técnica | Sim/Não/Facultativa | Prazo e local da visita |
| Qualificação econômico-financeira | Sim/Não | Índices contábeis, patrimônio líquido mínimo, capital social mínimo |
| Garantia de proposta | Sim/Não | % do valor estimado |
| Garantia contratual | Sim/Não | % e tipo (caução, seguro, fiança) |
| Amostra/demonstração | Sim/Não | Prazo e condições |
| Certidões negativas de sanções | Sim/Não | CEIS, CNEP, TCU |

**C. Condições Comerciais Relevantes**

| Item | Extraído do edital |
|------|-------------------|
| Subcontratação permitida? | Sim/Não + % limite |
| Consórcio permitido? | Sim/Não + regras |
| Participação de ME/EPP | Exclusiva / Cota reservada / Aberta |
| Margem de preferência | Sim/Não + % |
| Prazo de pagamento | X dias após aceite/atesto |
| Reajuste previsto? | Índice (IPCA, INPC, etc.) |
| Penalidades relevantes | Multa diária, % máximo, suspensão |
| Dotação orçamentária confirmada? | Sim/Não |

**D. Red Flags e Alertas (interpretação do Claude)**

Identificar automaticamente:
- **Prazo de entrega apertado** — prazo irreal para o escopo descrito
- **Exigências restritivas** — atestados com quantitativos muito específicos que limitam competição
- **Valor estimado desalinhado** — muito acima ou abaixo do mercado para o objeto
- **Cláusulas incomuns** — garantia excessiva, penalidades desproporcionais, prazos de pagamento longos
- **Direcionamento suspeito** — especificações que apontam para marca/fornecedor específico
- **Impugnação viável** — cláusulas que podem ser impugnadas por restringir competitividade

**E. Resumo Executivo do Edital (2-3 parágrafos)**

Em linguagem acessível para o decisor:
- O que está sendo comprado (escopo real, não apenas o título)
- O que é preciso para participar (resumo dos requisitos mais relevantes)
- Qual o principal risco/oportunidade

#### 2b.5. Tratamento de editais PCP v2

Para editais encontrados via PCP v2 (que não têm endpoint PNCP de arquivos):
- Tentar construir URL PNCP equivalente se `numeroControlePNCP` disponível
- Se não disponível, registrar "Edital disponível apenas no portal PCP — análise documental não realizada"
- Incluir link direto para o portal PCP para acesso manual

#### 2b.6. Output da Phase 2b

Para cada edital analisado, gerar um bloco estruturado:

```
## Edital {numero} — {orgao} — {UF}
### Análise Documental
**Status:** Analisado / PDF indisponível / PDF não-textual
**Documentos lidos:** Edital (42 pág.) + TR (18 pág.)

**Ficha Técnica:**
[tabela A preenchida]

**Habilitação:**
[checklist B preenchido]

**Condições Comerciais:**
[tabela C preenchida]

**Red Flags:** [lista D]
**Resumo:** [texto E]
```

### Phase 3: Análise Estratégica por Edital (@analyst + dados da Phase 2b)

Para CADA edital encontrado, o agente deve analisar cruzando METADADOS (Phase 2a) + ANÁLISE DOCUMENTAL (Phase 2b) + PERFIL DA EMPRESA (Phase 1):

1. **Aderência ao perfil** — O objeto do edital é compatível com os CNAEs da empresa? Cruzar com escopo real extraído do documento (não apenas título). (Alta/Média/Baixa)
2. **Análise de valor** — O valor estimado está dentro da faixa operacional da empresa (baseado em capital social e histórico)? Se sigiloso, estimar baseado em contratos similares.
3. **Análise geográfica** — Distância da sede ao local de execução (extraído da Phase 2b). A empresa já atua naquela UF?
4. **Análise de prazo** — Dias restantes até encerramento. Tempo suficiente para preparar proposta E atender requisitos de habilitação identificados na Phase 2b?
5. **Análise de modalidade** — Pregão (preço) vs Concorrência (técnica+preço). Critério de julgamento extraído do edital.
6. **Competitividade** — Baseado no histórico do órgão, qual o padrão de desconto? Existem incumbentes?
7. **Análise de habilitação** — A empresa CONSEGUE atender os requisitos? Cruzar checklist da Phase 2b com perfil da empresa:
   - Capital social mínimo vs capital social real da empresa
   - Atestados exigidos vs histórico de contratos da empresa
   - Equipe técnica vs porte da empresa
   - Se NÃO atende algum requisito crítico → recomendação automática NÃO RECOMENDADO com motivo
8. **Riscos e alertas** — Red flags da Phase 2b + prazos apertados + valores atípicos
9. **Recomendação** — PARTICIPAR / AVALIAR COM CAUTELA / NÃO RECOMENDADO (com motivo factual)
10. **Perguntas do decisor respondidas com FATOS do edital:**
    - "Vale a pena participar?" → Resposta baseada em aderência + habilitação + valor
    - "Quanto eu deveria ofertar?" → Baseado em valor estimado (se público) + histórico de descontos do órgão
    - "Quem são os concorrentes prováveis?" → Da Phase 3b (incumbentes)
    - "Quais documentos preciso preparar?" → **Lista EXATA extraída da seção de habilitação do edital**
    - "Qual o risco de não conseguir executar?" → Baseado em prazo de execução + local + escopo real
    - "Esse órgão paga em dia?" → Prazo de pagamento extraído do edital + histórico (se disponível)
    - "Existe alguma restrição que me impeça?" → Checklist de habilitação cruzado com perfil real da empresa

### Phase 3b: Inteligência Competitiva por Edital (@data-engineer + @analyst)

Para CADA edital com recomendação PARTICIPAR ou AVALIAR COM CAUTELA, mapear o cenário competitivo:

**3b.1. Identificar incumbentes do órgão comprador**
```bash
# Buscar contratos anteriores do mesmo órgão no PNCP (últimos 24 meses)
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
  ?dataInicial={24_meses_atras_YYYYMMDD}\
  &dataFinal={hoje_YYYYMMDD}\
  &codigoUnidadeAdministrativa={codigo_orgao}\
  &pagina=1&tamanhoPagina=50"
```
- Extrair CNPJs vencedores de contratos anteriores do MESMO órgão
- Filtrar por objeto similar (mesmo setor/keywords)
- Identificar: quem ganhou, quantas vezes, valores praticados

**3b.2. Enriquecer perfil dos concorrentes**
```bash
# Para cada CNPJ concorrente (top 5 por frequência)
curl -s "https://api.opencnpj.org/${CNPJ_CONCORRENTE}"
```
- Extrair: razão social, porte, capital social, cidade sede, CNAEs
- Calcular: faturamento gov mensal estimado (baseado em contratos PNCP)

**3b.3. Análise competitiva por edital**

Para cada edital, gerar:

| Campo | Fonte | Descrição |
|-------|-------|-----------|
| Concorrentes prováveis | PNCP histórico do órgão | Top 3-5 empresas que já forneceram para este órgão |
| Incumbente principal | PNCP | Empresa com mais contratos recentes neste órgão/objeto |
| Preço médio praticado | PNCP contratos anteriores | Média dos valores de contratos similares |
| Desconto médio | Valor estimado vs valor contratado | % de desconto típico neste órgão |
| Porte dos concorrentes | OpenCNPJ | Micro/Pequeno/Médio/Grande |
| Vantagem competitiva do cliente | Análise cruzada | Onde o cliente é mais forte que os concorrentes |
| Vulnerabilidade | Análise cruzada | Onde o cliente é mais fraco |
| Estratégia sugerida | Síntese | Preço agressivo / Diferenciação técnica / Evitar |

**3b.4. Mapa de calor competitivo (consolidado)**
- Tabela resumo: para cada edital, nível de competição (Baixa/Média/Alta/Muito Alta)
- Critérios:
  - **Baixa:** <3 fornecedores históricos, sem incumbente dominante
  - **Média:** 3-5 fornecedores, incumbente com <40% dos contratos
  - **Alta:** 5-10 fornecedores, incumbente com 40-60% dos contratos
  - **Muito Alta:** >10 fornecedores OU incumbente com >60% dos contratos
- Recomendação ajustada: editais com competição Baixa/Média sobem na priorização

### Phase 4: Inteligência de Mercado (@analyst)

1. **Panorama setorial** — Quantos editais abertos no setor, valor total em jogo, concentração por UF
2. **Tendências** — Modalidades mais comuns, valores médios, órgãos mais ativos
3. **Vantagens competitivas da empresa** — Baseado no perfil (porte, localização, CNAEs, histórico)
4. **Ranking competitivo** — Posição do cliente vs concorrentes no setor (por volume de contratos, valor, diversificação geográfica)
5. **Oportunidades de nicho** — Órgãos/UFs onde poucos concorrentes atuam mas há demanda
6. **Recomendação geral** — Priorização dos editais por potencial de retorno vs esforço vs competição

### Phase 5: Geração do PDF (@dev)

Executar o script de geração:
```bash
cd C:/Users/tiagosasaki/Desktop/PNCP-poc
python scripts/generate-report-b2g.py --input docs/reports/data-{CNPJ}-{data}.json --output docs/reports/report-{CNPJ}-{data}.pdf
```

O JSON de input deve ser criado pelo agente com toda a informação coletada nas fases anteriores.

**Estrutura do PDF:**
1. **Capa** — Título, nome da empresa, CNPJ, setor, data
2. **Perfil da Empresa** — Dados cadastrais, QSA, histórico gov, sanções
3. **Resumo Executivo** — Métricas chave, destaques, recomendação geral
4. **Panorama de Oportunidades** — Tabela resumo, distribuição por UF/modalidade/valor
5. **Análise Detalhada por Edital** — Uma seção por edital com:
   - Ficha técnica factual (dados extraídos do PDF do edital)
   - Checklist de habilitação (requisitos reais vs perfil da empresa)
   - Condições comerciais (subcontratação, consórcio, pagamento, penalidades)
   - Red flags e alertas (cláusulas restritivas, prazos irreais, direcionamento)
   - Resumo executivo do edital (escopo real em linguagem acessível)
   - Análise estratégica completa (aderência + valor + geografia + prazo + habilitação)
   - Recomendação com motivo factual
   - Respostas às perguntas do decisor baseadas em fatos do documento
6. **Mapa Competitivo** — Para cada edital recomendado: incumbentes, concorrentes prováveis, preços praticados, nível de competição, estratégia sugerida. Inclui mapa de calor consolidado (Baixa/Média/Alta/Muito Alta competição por edital)
7. **Inteligência de Mercado** — Tendências, ranking competitivo do cliente vs concorrentes, oportunidades de nicho, vantagens competitivas
8. **Menções em Diários Oficiais** — Resultados do Querido Diário (se houver)
9. **Próximos Passos** — Ações recomendadas com prioridade e prazo, priorizando editais com menor competição e maior aderência. Para cada edital PARTICIPAR: lista exata de documentos a preparar (extraída do edital)
10. **Rodapé em todas as páginas:** "Tiago Sasaki - Consultor de Licitações (48)9 8834-4559"

---

## APIs Reference

| API | Endpoint | Auth | Rate Limit | Uso |
|-----|----------|------|------------|-----|
| OpenCNPJ | `api.opencnpj.org/{CNPJ}` | Nenhuma | 50 req/s | Perfil da empresa |
| Portal Transparência | `api.portaldatransparencia.gov.br/api-de-dados/` | `chave-api-dados` header | 90 req/min | Sanções + contratos federais |
| PNCP Consulta | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | Nenhuma | ~100 req/min | Busca de editais |
| **PNCP Arquivos** | **`pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos`** | **Nenhuma** | **~60 req/min** | **Lista de documentos do edital** |
| **PNCP Download** | **`pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{n}`** | **Nenhuma** | **~30 req/min** | **Download direto do PDF** |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | Nenhuma | ~60 req/min | Editais complementares |
| Querido Diário | `api.queridodiario.ok.org.br/gazettes` | Nenhuma | ~60 req/min | Diários oficiais |

### PNCP Arquivos — Detalhes Técnicos

**Endpoint de listagem:**
```
GET /api/pncp/v1/orgaos/{cnpj_orgao}/compras/{anoCompra}/{sequencialCompra}/arquivos
```
- Retorna JSON array com todos os documentos publicados
- Campos úteis: `tipoDocumentoNome`, `tipoDocumentoId`, `titulo`, `sequencialDocumento`, `url`
- `tipoDocumentoId: 2` = Edital (documento principal)

**Endpoint de download:**
```
GET /pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{sequencialDocumento}
```
- Retorna PDF direto (binary)
- Header: `content-disposition: attachment; filename="nome.pdf"`
- Sem autenticação, CORS aberto (`access-control-allow-origin: *`)
- Arquivos tipicamente 200KB-5MB

## Execution

Quando invocado:
1. **Phase 1:** Perfil da empresa (OpenCNPJ + Portal Transparência)
2. **Phase 2a:** Varredura de editais abertos (PNCP + PCP + Querido Diário)
3. **Phase 2b:** Download dos PDFs dos editais PNCP + análise documental pelo Claude (ficha técnica, habilitação, condições, red flags)
4. **Phase 3:** Análise estratégica cruzando perfil + edital + documento real
5. **Phase 3b:** Inteligência competitiva (incumbentes, concorrentes, preços)
6. **Phase 4:** Inteligência de mercado (panorama, tendências, nichos)
7. **Phase 5:** Geração do PDF final
8. Dados intermediários salvos em `docs/reports/data-{CNPJ}-{data}.json`
9. PDF final gerado em `docs/reports/report-{CNPJ}-{nome-slug}-{data}.pdf` (nome fantasia ou razão social slugificado, max 40 chars)
10. Relatório Markdown resumido em `docs/reports/report-{CNPJ}-{nome-slug}-{data}.md`

**Tempo estimado:** 5-15 minutos dependendo do número de editais encontrados e tamanho dos PDFs.

## Params

$ARGUMENTS
