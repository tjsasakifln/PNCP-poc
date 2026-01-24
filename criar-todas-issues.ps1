# Script PowerShell para criar todas as issues do POC PNCP
# Execute com: .\criar-todas-issues.ps1

$REPO = "tjsasakifln/PNCP-poc"

Write-Host "Criando issues para $REPO..." -ForegroundColor Green

# Array de issues para criar
$issues = @(
    @{
        title = "Inicializar repositório e estrutura de pastas"
        labels = "infrastructure,setup"
        body = @"
## Descrição
Criar a estrutura completa de diretórios do projeto conforme PRD.

## Tarefas
- [ ] Criar estrutura backend/
- [ ] Criar estrutura frontend/
- [ ] Criar .gitignore
- [ ] Criar arquivos base

## Relacionado
Epic #2
"@
    },
    @{
        title = "Configurar ambientes (dev/prod) e variáveis"
        labels = "infrastructure,configuration"
        body = @"
## Descrição
Configurar variáveis de ambiente conforme PRD seção 10.

## Tarefas
- [ ] Criar .env.example
- [ ] Documentar variáveis
- [ ] Validação de env

## Relacionado
Epic #2
"@
    },
    @{
        title = "Setup Docker Compose para desenvolvimento"
        labels = "infrastructure,docker"
        body = @"
## Descrição
Docker Compose para backend + frontend.

## Tarefas
- [ ] Dockerfile backend
- [ ] Dockerfile frontend
- [ ] docker-compose.yml

## Relacionado
Epic #2
"@
    },
    @{
        title = "🔌 EPIC 2: Cliente PNCP e Resiliência"
        labels = "epic,backend,integration"
        body = @"
## Objetivo
Cliente HTTP resiliente para API do PNCP.

## Escopo
- Retry exponencial
- Paginação automática
- Rate limiting

## Referência PRD
Seção 2, 3
"@
    },
    @{
        title = "Implementar cliente HTTP resiliente com retry e backoff"
        labels = "backend,feature"
        body = @"
## Descrição
Classe PNCPClient com retry automático (PRD seção 3.2).

## Tarefas
- [ ] RetryConfig dataclass
- [ ] calculate_delay()
- [ ] PNCPClient com _create_session()
- [ ] fetch_page()
- [ ] Rate limiting
- [ ] Exceções customizadas

## Relacionado
Epic #6
"@
    },
    @{
        title = "Implementar paginação automática da API PNCP"
        labels = "backend,feature"
        body = @"
## Descrição
Métodos fetch_all() e _fetch_by_uf().

## Tarefas
- [ ] fetch_all() generator
- [ ] _fetch_by_uf()
- [ ] Progress callback
- [ ] Loop protection

## Relacionado
Epic #6
"@
    },
    @{
        title = "🎯 EPIC 3: Motor de Filtragem"
        labels = "epic,backend,core-logic"
        body = @"
## Objetivo
Sistema de filtragem sequencial para uniformes.

## Escopo
- Normalização de texto
- Keywords matching
- Filtros: UF → Valor → Keywords → Status

## Referência PRD
Seção 4
"@
    },
    @{
        title = "Implementar normalização e matching de keywords"
        labels = "backend,feature"
        body = @"
## Descrição
Funções normalize_text() e match_keywords().

## Tarefas
- [ ] normalize_text() (acentos, lowercase)
- [ ] match_keywords() com word boundaries
- [ ] KEYWORDS_UNIFORMES
- [ ] KEYWORDS_EXCLUSAO

## Relacionado
Epic #9
"@
    },
    @{
        title = "Implementar filtros sequenciais"
        labels = "backend,feature"
        body = @"
## Descrição
filter_licitacao() com fail-fast.

## Ordem
1. UF
2. Valor (R$ 50k-5M)
3. Keywords
4. Status (prazo)

## Relacionado
Epic #9
"@
    },
    @{
        title = "📊 EPIC 4: Geração de Saídas"
        labels = "epic,backend,output"
        body = @"
## Objetivo
Excel formatado + resumo LLM.

## Escopo
- Gerador Excel (openpyxl)
- GPT-4.1-nano integration
- Fallback sem LLM

## Referência PRD
Seções 5, 6
"@
    },
    @{
        title = "Implementar gerador de Excel"
        labels = "backend,feature"
        body = @"
## Descrição
Planilha com 11 colunas formatadas.

## Tarefas
- [ ] create_excel()
- [ ] Estilos e formatação
- [ ] Hyperlinks
- [ ] Metadata sheet

## Relacionado
Epic #12
"@
    },
    @{
        title = "Integração com GPT-4.1-nano"
        labels = "backend,feature,ai"
        body = @"
## Descrição
Resumo estruturado via OpenAI.

## Tarefas
- [ ] ResumoLicitacoes schema
- [ ] gerar_resumo()
- [ ] format_resumo_html()

## Relacionado
Epic #12
"@
    },
    @{
        title = "Fallback sem LLM"
        labels = "backend,feature"
        body = @"
## Descrição
Resumo básico sem OpenAI.

## Tarefas
- [ ] gerar_resumo_fallback()
- [ ] Stats básicas
- [ ] Top 3 por valor

## Relacionado
Epic #12
"@
    },
    @{
        title = "🌐 EPIC 5: API Backend (FastAPI)"
        labels = "epic,backend,api"
        body = @"
## Objetivo
API REST com FastAPI.

## Escopo
- Estrutura base
- POST /buscar
- Health check
- Logging

## Referência PRD
Seção 8
"@
    },
    @{
        title = "Estrutura base FastAPI"
        labels = "backend,setup"
        body = @"
## Descrição
App FastAPI com CORS e schemas.

## Tarefas
- [ ] main.py
- [ ] schemas.py
- [ ] config.py
- [ ] requirements.txt

## Relacionado
Epic #17
"@
    },
    @{
        title = "Endpoint POST /buscar"
        labels = "backend,feature,integration"
        body = @"
## Descrição
Orquestração: PNCP → Filtro → LLM → Excel.

## Tarefas
- [ ] buscar_licitacoes()
- [ ] Validações (max 30 dias)
- [ ] Try/except fallback
- [ ] Base64 encoding

## Relacionado
Epic #17
"@
    },
    @{
        title = "🎨 EPIC 6: Frontend (Next.js)"
        labels = "epic,frontend"
        body = @"
## Objetivo
Interface web com Next.js 14.

## Escopo
- Setup Next.js + Tailwind
- Seleção UFs e período
- Resultados com resumo
- Download Excel

## Referência PRD
Seção 7
"@
    },
    @{
        title = "Setup Next.js 14 + Tailwind"
        labels = "frontend,setup"
        body = @"
## Descrição
Configurar Next.js com App Router.

## Tarefas
- [ ] create-next-app
- [ ] Tailwind CSS
- [ ] TypeScript
- [ ] Estrutura de pastas

## Relacionado
Epic #21
"@
    },
    @{
        title = "Interface de seleção"
        labels = "frontend,feature"
        body = @"
## Descrição
Multi-select UFs + período.

## Componentes
- Botões toggle UFs
- Date inputs
- Validações
- Loading state

## Relacionado
Epic #21
"@
    },
    @{
        title = "Tela de resultados"
        labels = "frontend,feature"
        body = @"
## Descrição
Exibir resumo LLM + download.

## Componentes
- Card de resumo
- Stats visuais
- Destaques
- Botão download

## Relacionado
Epic #21
"@
    },
    @{
        title = "API Routes Next.js"
        labels = "frontend,feature"
        body = @"
## Descrição
/api/buscar e /api/download.

## Tarefas
- [ ] app/api/buscar/route.ts
- [ ] app/api/download/route.ts
- [ ] Cache em memória (Map)

## Relacionado
Epic #21
"@
    },
    @{
        title = "🚀 EPIC 7: Integração e Deploy"
        labels = "epic,integration,deployment"
        body = @"
## Objetivo
Integração completa e deploy.

## Escopo
- Frontend ↔ Backend
- Testes E2E
- Documentação
- Deploy

## Referência PRD
Todas as seções
"@
    },
    @{
        title = "Integrar frontend ↔ backend"
        labels = "integration,feature"
        body = @"
## Descrição
Conectar Next.js com FastAPI.

## Tarefas
- [ ] CORS no backend
- [ ] BACKEND_URL no frontend
- [ ] Testar comunicação
- [ ] Validar schemas

## Relacionado
Epic #26
"@
    },
    @{
        title = "Testes end-to-end"
        labels = "testing,feature"
        body = @"
## Descrição
Testar fluxo completo.

## Cenários
- Happy path
- Fallback LLM
- Sem resultados
- Validações

## Relacionado
Epic #26
"@
    }
)

# Criar cada issue
$count = 0
foreach ($issue in $issues) {
    $count++
    Write-Host "Criando issue $count/$($issues.Count): $($issue.title)" -ForegroundColor Cyan

    gh issue create `
        --repo $REPO `
        --title $issue.title `
        --label $issue.labels `
        --body $issue.body

    Start-Sleep -Milliseconds 500  # Evitar rate limiting
}

Write-Host "`n✓ $count issues criadas com sucesso!" -ForegroundColor Green
Write-Host "Acesse: https://github.com/$REPO/issues" -ForegroundColor Yellow
