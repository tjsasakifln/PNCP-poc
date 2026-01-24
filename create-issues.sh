#!/bin/bash

# Script para criar todas as issues do POC PNCP
# Baseado no PRD v0.2

REPO="tjsasakifln/PNCP-poc"

echo "Criando issues para $REPO..."

# EPIC 1: Setup e Infraestrutura Base
gh issue create --repo "$REPO" \
  --title "🏗️ EPIC 1: Setup e Infraestrutura Base" \
  --label "epic,infrastructure" \
  --body "## Objetivo
Estabelecer a estrutura base do projeto conforme especificado no PRD v0.2.

## Escopo
- Estrutura de diretórios (backend/ e frontend/)
- Configuração de ambientes
- Docker Compose para desenvolvimento local

## Issues Relacionadas
- [ ] #2 - Inicializar repositório e estrutura de pastas
- [ ] #3 - Configurar ambientes (dev/prod) e variáveis
- [ ] #4 - Setup Docker Compose para desenvolvimento

## Referência PRD
Seção 11 - Estrutura Final de Diretórios
Seção 10 - Variáveis de Ambiente

## Critérios de Aceitação
- [ ] Estrutura de diretórios criada conforme PRD seção 11
- [ ] Arquivo .env.example com todas as variáveis documentadas
- [ ] Docker Compose funcional para backend + frontend
- [ ] README.md com instruções de setup inicial"

# Issue 2
gh issue create --repo "$REPO" \
  --title "Inicializar repositório e estrutura de pastas" \
  --label "infrastructure,setup" \
  --body "## Descrição
Criar a estrutura completa de diretórios do projeto conforme especificado no PRD.

## Estrutura Esperada
\`\`\`
pncp-poc/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── pncp_client.py
│   ├── filter.py
│   ├── excel.py
│   ├── llm.py
│   ├── schemas.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── api/
│   │       ├── buscar/route.ts
│   │       └── download/route.ts
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── .env.example
├── docker-compose.yml
└── README.md
\`\`\`

## Tarefas
- [ ] Criar estrutura de diretórios backend/
- [ ] Criar estrutura de diretórios frontend/
- [ ] Criar arquivos base vazios (main.py, page.tsx, etc.)
- [ ] Criar .gitignore apropriado (Python + Node.js)

## Referência PRD
Seção 11 - Estrutura Final de Diretórios

## Relacionado
Epic #1"

# Issue 3
gh issue create --repo "$REPO" \
  --title "Configurar ambientes (dev/prod) e variáveis" \
  --label "infrastructure,configuration" \
  --body "## Descrição
Configurar variáveis de ambiente conforme especificado no PRD seção 10.

## Variáveis Obrigatórias
\`\`\`bash
# .env.example
OPENAI_API_KEY=sk-...

# Backend
BACKEND_PORT=8000
LOG_LEVEL=INFO

# PNCP Client
PNCP_TIMEOUT=30
PNCP_MAX_RETRIES=5
PNCP_BACKOFF_BASE=2
PNCP_BACKOFF_MAX=60

# LLM
LLM_MODEL=gpt-4.1-nano
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
\`\`\`

## Tarefas
- [ ] Criar arquivo .env.example com todas as variáveis
- [ ] Documentar cada variável (propósito e valores padrão)
- [ ] Adicionar .env ao .gitignore
- [ ] Criar função de validação de env no backend (config.py)

## Referência PRD
Seção 10 - Variáveis de Ambiente
Seção 1.2 - Parâmetros do Sistema

## Relacionado
Epic #1"

# Issue 4
gh issue create --repo "$REPO" \
  --title "Setup Docker Compose para desenvolvimento" \
  --label "infrastructure,docker" \
  --body "## Descrição
Criar Docker Compose para executar backend e frontend em desenvolvimento.

## Serviços
- **backend**: FastAPI (porta 8000)
- **frontend**: Next.js (porta 3000)

## Tarefas
- [ ] Criar Dockerfile para backend (Python 3.11+)
- [ ] Criar Dockerfile para frontend (Node.js 20+)
- [ ] Criar docker-compose.yml
- [ ] Testar build e execução dos containers
- [ ] Documentar comandos no README.md

## Referência PRD
Seção 11 - Estrutura Final de Diretórios

## Relacionado
Epic #1"

echo "✓ EPIC 1 completo (4 issues)"

# EPIC 2: Cliente PNCP e Resiliência
gh issue create --repo "$REPO" \
  --title "🔌 EPIC 2: Cliente PNCP e Resiliência" \
  --label "epic,backend,integration" \
  --body "## Objetivo
Implementar cliente HTTP resiliente para consumir a API do PNCP com retry automático, paginação e tratamento de erros.

## Escopo
- Cliente HTTP com retry exponencial
- Paginação automática
- Rate limiting e circuit breaker
- Tratamento de todos os códigos HTTP relevantes

## Issues Relacionadas
- [ ] #6 - Implementar cliente HTTP resiliente com retry e backoff
- [ ] #7 - Implementar paginação automática da API PNCP
- [ ] #8 - Implementar tratamento de rate limiting (429)
- [ ] #9 - Implementar circuit breaker (opcional)

## Referência PRD
Seção 2 - Integração PNCP
Seção 3 - Lógica de Retry e Resiliência

## Critérios de Aceitação
- [ ] Cliente resiliente implementado conforme seção 3.2 do PRD
- [ ] Paginação automática funcionando para múltiplas UFs
- [ ] Rate limiting respeitado (header Retry-After)
- [ ] Logs estruturados de todas as requisições
- [ ] Testes unitários com >80% cobertura"

# Issue 6
gh issue create --repo "$REPO" \
  --title "Implementar cliente HTTP resiliente com retry e backoff" \
  --label "backend,feature" \
  --body "## Descrição
Implementar classe \`PNCPClient\` com retry automático usando exponential backoff conforme especificado no PRD.

## Implementação
Arquivo: \`backend/pncp_client.py\`

Seguir especificação completa da seção 3.2 do PRD:
- Usar \`requests\` com \`urllib3.util.retry.Retry\`
- Exponential backoff configurável
- Jitter para evitar thundering herd
- User-Agent customizado: \"BidIQ-POC/0.2\"

## Parâmetros de Retry (seção 1.2 PRD)
\`\`\`python
max_retries: 5
base_delay: 2.0
max_delay: 60.0
exponential_base: 2.0
jitter: True
retryable_status_codes: (408, 429, 500, 502, 503, 504)
\`\`\`

## Tarefas
- [ ] Implementar classe \`RetryConfig\` (dataclass)
- [ ] Implementar função \`calculate_delay()\`
- [ ] Implementar classe \`PNCPClient\` com \`_create_session()\`
- [ ] Implementar método \`fetch_page()\`
- [ ] Implementar rate limiting básico (10 req/s)
- [ ] Adicionar logging estruturado
- [ ] Criar exceções customizadas (\`PNCPAPIError\`, \`PNCPRateLimitError\`)

## Referência PRD
Seção 3.1 - Estratégia de Retry
Seção 3.2 - Cliente HTTP Resiliente
Seção 3.3 - Tratamento de Erros por Tipo

## Relacionado
Epic #5"

# Issue 7
gh issue create --repo "$REPO" \
  --title "Implementar paginação automática da API PNCP" \
  --label "backend,feature" \
  --body "## Descrição
Implementar métodos \`fetch_all()\` e \`_fetch_by_uf()\` para paginação automática da API PNCP.

## Especificação API
- **Endpoint**: \`GET /api/consulta/v1/contratacoes/publicacao\`
- **Página inicial**: 1 (1-indexed)
- **Tamanho máximo**: 500 itens/página
- **Campos resposta**: \`data\`, \`totalPaginas\`, \`temProximaPagina\`

## Tarefas
- [ ] Implementar método \`fetch_all()\` como generator
- [ ] Implementar método \`_fetch_by_uf()\` para paginação por UF
- [ ] Implementar callback \`on_progress\` para UI
- [ ] Otimizar: fazer busca por UF quando UFs específicas selecionadas
- [ ] Adicionar logging de progresso (página atual/total)
- [ ] Tratar caso de paginação infinita (loop protection)

## Referência PRD
Seção 2.2 - Parâmetros de Request
Seção 2.3 - Estrutura de Resposta

## Relacionado
Epic #5"

# Issue 8
gh issue create --repo "$REPO" \
  --title "Implementar tratamento de rate limiting (429)" \
  --label "backend,feature" \
  --body "## Descrição
Tratar código HTTP 429 (Rate Limit) respeitando header \`Retry-After\` conforme seção 3.3 do PRD.

## Comportamento Esperado
1. Receber status code 429
2. Ler header \`Retry-After\` (padrão: 60s se não presente)
3. Aguardar tempo especificado
4. Tentar novamente
5. Logar warning com tempo de espera

## Tarefas
- [ ] Validar implementação existente em \`fetch_page()\`
- [ ] Adicionar contador de rate limits no logging
- [ ] Adicionar métrica \`pncp_rate_limit_hits\`
- [ ] Testar comportamento com mock de 429
- [ ] Documentar estratégia de rate limiting no README

## Referência PRD
Seção 3.3 - Tratamento de Erros por Tipo
Seção 12.2 - Métricas a Coletar

## Relacionado
Epic #5"

# Issue 9
gh issue create --repo "$REPO" \
  --title "Implementar circuit breaker (opcional)" \
  --label "backend,enhancement,optional" \
  --body "## Descrição
Implementar Circuit Breaker para proteger contra falhas em cascata (OPCIONAL - não crítico para POC).

## Especificação
Estados: CLOSED, OPEN, HALF_OPEN

## Configuração Padrão
\`\`\`python
failure_threshold: 5
recovery_timeout: 30  # segundos
\`\`\`

## Tarefas
- [ ] Implementar classe \`CircuitBreaker\` conforme PRD seção 3.4
- [ ] Integrar com \`PNCPClient\`
- [ ] Adicionar logging de mudanças de estado
- [ ] Adicionar métricas de circuit breaker
- [ ] Testes unitários dos 3 estados

## Referência PRD
Seção 3.4 - Circuit Breaker

## Prioridade
**Baixa** - Pode ser implementado após POC funcional

## Relacionado
Epic #5"

echo "✓ EPIC 2 completo (4 issues)"

# EPIC 3: Motor de Filtragem
gh issue create --repo "$REPO" \
  --title "🎯 EPIC 3: Motor de Filtragem" \
  --label "epic,backend,core-logic" \
  --body "## Objetivo
Implementar sistema de filtragem sequencial (fail-fast) para licitações de uniformes.

## Escopo
- Normalização de texto
- Matching de keywords com word boundaries
- Filtros sequenciais: UF → Valor → Keywords → Status
- Estatísticas de filtragem

## Issues Relacionadas
- [ ] #11 - Implementar normalização de texto e matching de keywords
- [ ] #12 - Implementar filtros sequenciais (UF, valor, keywords, status)
- [ ] #13 - Implementar estatísticas de filtragem

## Referência PRD
Seção 4 - Motor de Filtragem

## Critérios de Aceitação
- [ ] Normalização remove acentos e normaliza espaços
- [ ] Matching usa word boundaries (não match parcial)
- [ ] Keywords de exclusão implementadas
- [ ] Filtros aplicados em ordem fail-fast
- [ ] Estatísticas mostram motivos de rejeição"

# Issue 11
gh issue create --repo "$REPO" \
  --title "Implementar normalização de texto e matching de keywords" \
  --label "backend,feature" \
  --body "## Descrição
Implementar funções de normalização de texto e matching de keywords para uniformes/fardamentos.

## Implementação
Arquivo: \`backend/filter.py\`

Funções:
- \`normalize_text(text: str) -> str\`
- \`match_keywords(objeto, keywords, exclusions) -> tuple[bool, list[str]]\`

## Keywords de Uniformes
Ver lista completa no PRD seção 4.1 (uniformes, fardamentos, jaleco, etc.)

## Tarefas
- [ ] Implementar \`normalize_text()\` conforme PRD seção 4.2
- [ ] Implementar \`match_keywords()\` com word boundaries
- [ ] Definir \`KEYWORDS_UNIFORMES\` (lista completa)
- [ ] Definir \`KEYWORDS_EXCLUSAO\`
- [ ] Testes unitários (acentos, word boundaries, compostas)

## Referência PRD
Seção 4.1 - Keywords de Uniformes/Fardamentos
Seção 4.2 - Algoritmo de Matching

## Relacionado
Epic #10"

# Issue 12
gh issue create --repo "$REPO" \
  --title "Implementar filtros sequenciais (UF, valor, keywords, status)" \
  --label "backend,feature" \
  --body "## Descrição
Implementar função \`filter_licitacao()\` com filtros sequenciais fail-fast.

## Ordem dos Filtros
1. **UF** ∈ UFs selecionadas
2. **Valor** entre R$ 50.000 e R$ 5.000.000
3. **Keywords** match em \`objetoCompra\`
4. **Status** aberto (\`dataAberturaProposta\` futura)

## Parâmetros de Valor
- \`VALOR_MIN\`: R$ 50.000,00
- \`VALOR_MAX\`: R$ 5.000.000,00

## Tarefas
- [ ] Implementar \`filter_licitacao()\` conforme PRD seção 4.2
- [ ] Implementar filtro de UF (primeiro)
- [ ] Implementar filtro de valor (segundo)
- [ ] Implementar filtro de keywords (terceiro)
- [ ] Implementar filtro de status/prazo (quarto)
- [ ] Parse de datas ISO com timezone
- [ ] Retornar motivo de rejeição para estatísticas

## Referência PRD
Seção 4.2 - Algoritmo de Matching
Seção 1.2 - Parâmetros do Sistema

## Relacionado
Epic #10
Depende de: #11"

# Issue 13
gh issue create --repo "$REPO" \
  --title "Implementar estatísticas de filtragem" \
  --label "backend,feature" \
  --body "## Descrição
Implementar função \`filter_batch()\` que processa lote de licitações e retorna estatísticas.

## Estatísticas Esperadas
\`\`\`python
stats = {
    \"total\": int,
    \"aprovadas\": int,
    \"rejeitadas_uf\": int,
    \"rejeitadas_valor\": int,
    \"rejeitadas_keyword\": int,
    \"rejeitadas_prazo\": int,
    \"rejeitadas_outros\": int
}
\`\`\`

## Tarefas
- [ ] Implementar \`filter_batch()\` conforme PRD seção 4.2
- [ ] Contabilizar motivos de rejeição
- [ ] Adicionar logging de estatísticas
- [ ] Retornar lista de aprovadas + stats
- [ ] Testes com batch grande (>1000 licitações)

## Referência PRD
Seção 4.2 - Algoritmo de Matching

## Relacionado
Epic #10
Depende de: #12"

echo "✓ EPIC 3 completo (3 issues)"

# EPIC 4: Geração de Saídas
gh issue create --repo "$REPO" \
  --title "📊 EPIC 4: Geração de Saídas" \
  --label "epic,backend,output" \
  --body "## Objetivo
Implementar geração de Excel formatado e resumo via LLM (GPT-4.1-nano).

## Escopo
- Gerador de Excel com formatação profissional
- Integração com OpenAI GPT-4.1-nano
- Fallback sem LLM para casos de falha
- Structured output com Pydantic

## Issues Relacionadas
- [ ] #15 - Implementar gerador de Excel com formatação
- [ ] #16 - Implementar integração com GPT-4.1-nano para resumos
- [ ] #17 - Implementar fallback sem LLM

## Referência PRD
Seção 5 - Geração de Excel
Seção 6 - Resumo via LLM

## Critérios de Aceitação
- [ ] Excel gerado com 11 colunas conforme seção 5.1
- [ ] Formatação: header verde, bordas, auto-width, freeze panes
- [ ] Hyperlinks funcionais para PNCP
- [ ] Resumo LLM estruturado (Pydantic schema)
- [ ] Fallback funciona sem API key"

# Issue 15
gh issue create --repo "$REPO" \
  --title "Implementar gerador de Excel com formatação" \
  --label "backend,feature" \
  --body "## Descrição
Implementar geração de planilha Excel formatada com \`openpyxl\` conforme especificação do PRD.

## Estrutura da Planilha
11 colunas: Código PNCP, Objeto, Órgão, UF, Município, Valor Estimado, Modalidade, Publicação, Abertura, Situação, Link

## Formatação
- **Header**: Verde (#2E7D32), texto branco, negrito
- **Células**: Bordas finas, wrap text
- **Moeda**: R$ #,##0.00
- **Datas**: DD/MM/YYYY
- **Links**: Hyperlinks funcionais
- **Freeze panes**: Row 2

## Tarefas
- [ ] Implementar função \`create_excel()\` conforme PRD seção 5.2
- [ ] Aplicar estilos (cores, fontes, bordas)
- [ ] Configurar auto-width para colunas
- [ ] Adicionar hyperlinks na coluna K
- [ ] Criar linha de totais com fórmula SUM
- [ ] Criar aba \"Metadata\"
- [ ] Implementar \`parse_datetime()\` para ISO dates
- [ ] Implementar \`generate_filename()\`

## Referência PRD
Seção 5 - Geração de Excel

## Relacionado
Epic #14"

# Issue 16
gh issue create --repo "$REPO" \
  --title "Implementar integração com GPT-4.1-nano para resumos" \
  --label "backend,feature,ai" \
  --body "## Descrição
Integrar com OpenAI GPT-4.1-nano para gerar resumos estruturados usando Structured Output.

## Configuração LLM
\`\`\`python
model: \"gpt-4.1-nano\"
temperature: 0.3
max_tokens: 500
response_format: Structured Output (Pydantic)
\`\`\`

## Schema Pydantic
\`\`\`python
class ResumoLicitacoes(BaseModel):
    resumo_executivo: str
    total_oportunidades: int
    valor_total: float
    destaques: list[str]
    distribuicao_uf: dict[str, int]
    alerta_urgencia: str | None
\`\`\`

## Tarefas
- [ ] Implementar \`ResumoLicitacoes\` (Pydantic model)
- [ ] Implementar \`gerar_resumo()\` com OpenAI client
- [ ] Limitar input a 50 licitações
- [ ] Implementar \`format_resumo_html()\`
- [ ] Tratar caso de lista vazia
- [ ] Adicionar logging de chamadas LLM
- [ ] Configurar env var \`OPENAI_API_KEY\`

## Referência PRD
Seção 6 - Resumo via LLM

## Relacionado
Epic #14"

# Issue 17
gh issue create --repo "$REPO" \
  --title "Implementar fallback sem LLM" \
  --label "backend,feature" \
  --body "## Descrição
Implementar geração de resumo básico sem usar LLM para casos de falha ou ausência de API key.

## Comportamento Fallback
- Calcular estatísticas básicas (total, valor_total)
- Distribuição por UF (agregação simples)
- Top 3 por valor
- Verificar urgência (data_abertura < 7 dias)
- Retornar mesmo schema \`ResumoLicitacoes\`

## Tarefas
- [ ] Implementar \`gerar_resumo_fallback()\` conforme PRD seção 6.4
- [ ] Calcular estatísticas básicas
- [ ] Calcular distribuição por UF
- [ ] Selecionar top 3 por valor
- [ ] Verificar alerta de urgência
- [ ] Gerar resumo executivo simples
- [ ] Adicionar flag indicando uso de fallback

## Referência PRD
Seção 6.4 - Fallback sem LLM

## Relacionado
Epic #14
Relacionado: #16"

echo "✓ EPIC 4 completo (3 issues)"

# EPIC 5: API Backend (FastAPI)
gh issue create --repo "$REPO" \
  --title "🌐 EPIC 5: API Backend (FastAPI)" \
  --label "epic,backend,api" \
  --body "## Objetivo
Implementar API REST com FastAPI para orquestrar todo o fluxo de busca e processamento.

## Escopo
- Estrutura base do FastAPI
- Endpoint POST /buscar
- Health check
- Logging estruturado
- CORS para frontend

## Issues Relacionadas
- [ ] #19 - Criar estrutura base do FastAPI
- [ ] #20 - Implementar endpoint POST /buscar
- [ ] #21 - Implementar logging estruturado
- [ ] #22 - Implementar health check

## Referência PRD
Seção 8 - Backend API (FastAPI)
Seção 12 - Logging e Observabilidade

## Critérios de Aceitação
- [ ] FastAPI servindo em porta 8000
- [ ] POST /buscar orquestrando: PNCP → Filtro → Excel → LLM
- [ ] CORS configurado
- [ ] Logs estruturados com timestamp
- [ ] Health check retornando status"

# Issue 19
gh issue create --repo "$REPO" \
  --title "Criar estrutura base do FastAPI" \
  --label "backend,setup" \
  --body "## Descrição
Criar aplicação FastAPI base com CORS, schemas Pydantic e estrutura de arquivos.

## Arquivos
- main.py (entrypoint)
- config.py (env vars)
- schemas.py (Pydantic models)
- requirements.txt

## Schemas
\`\`\`python
class BuscaRequest(BaseModel):
    ufs: list[str]
    data_inicial: str  # YYYY-MM-DD
    data_final: str    # YYYY-MM-DD

class BuscaResponse(BaseModel):
    resumo: ResumoLicitacoes
    excel_base64: str
    total_raw: int
    total_filtrado: int
\`\`\`

## Tarefas
- [ ] Criar \`main.py\` com FastAPI app
- [ ] Criar \`schemas.py\` com Pydantic models
- [ ] Criar \`config.py\` para env vars
- [ ] Criar \`requirements.txt\` conforme PRD seção 9.1
- [ ] Configurar CORS
- [ ] Testar servidor com uvicorn

## Referência PRD
Seção 8.1 - Estrutura
Seção 9.1 - Backend Dependencies

## Relacionado
Epic #18"

# Issue 20
gh issue create --repo "$REPO" \
  --title "Implementar endpoint POST /buscar" \
  --label "backend,feature,integration" \
  --body "## Descrição
Implementar endpoint principal que orquestra: PNCP → Filtro → LLM → Excel.

## Fluxo
1. Validar request
2. Buscar via \`PNCPClient.fetch_all()\`
3. Filtrar com \`filter_batch()\`
4. Gerar resumo (try/except para fallback)
5. Gerar Excel
6. Converter para base64
7. Retornar response

## Validações
- ufs: lista não-vazia
- datas: formato YYYY-MM-DD
- data_final >= data_inicial
- diferença <= 30 dias

## Códigos HTTP
- 200: Sucesso
- 400: Validação
- 502: Erro PNCP
- 500: Erro interno

## Tarefas
- [ ] Implementar \`buscar_licitacoes()\`
- [ ] Integrar todos os módulos
- [ ] Validar diferença de datas (max 30 dias)
- [ ] Try/except para fallback LLM
- [ ] Converter Excel para base64
- [ ] Tratamento de exceções
- [ ] Logging de cada etapa
- [ ] Testes end-to-end

## Referência PRD
Seção 8.2 - Endpoint Principal

## Relacionado
Epic #18
Depende de: #6, #7, #11, #12, #15, #16"

# Issue 21
gh issue create --repo "$REPO" \
  --title "Implementar logging estruturado" \
  --label "backend,feature" \
  --body "## Descrição
Configurar logging estruturado conforme PRD seção 12.1.

## Formato
\`\`\`
%(asctime)s | %(levelname)-8s | %(name)s | %(message)s
\`\`\`

## Tarefas
- [ ] Implementar \`setup_logging()\` em config.py
- [ ] Configurar formatação estruturada
- [ ] Silenciar logs verbosos de libs (urllib3, httpx)
- [ ] Configurar nível via env var LOG_LEVEL
- [ ] Adicionar logging em pontos críticos

## Referência PRD
Seção 12.1 - Configuração de Logging

## Relacionado
Epic #18"

# Issue 22
gh issue create --repo "$REPO" \
  --title "Implementar health check" \
  --label "backend,feature" \
  --body "## Descrição
Implementar endpoint GET /health para monitoramento.

## Implementação
\`\`\`python
@app.get(\"/health\")
async def health():
    return {\"status\": \"ok\"}
\`\`\`

## Tarefas
- [ ] Implementar endpoint /health
- [ ] Retornar status da aplicação
- [ ] Adicionar timestamp
- [ ] Opcionalmente verificar conectividade com PNCP

## Referência PRD
Seção 8.2 - Endpoint Principal (linha 1654)

## Relacionado
Epic #18"

echo "✓ EPIC 5 completo (4 issues)"

# Continua no próximo bloco...
echo "Criadas primeiras 22 issues. Continuando..."
