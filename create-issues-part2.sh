#!/bin/bash

# Script para criar issues - PARTE 2 (EPICs 6 e 7)
# Continua de create-issues.sh

REPO="tjsasakifln/PNCP-poc"

echo "Criando EPICs 6 e 7..."

# EPIC 6: Frontend (Next.js)
gh issue create --repo "$REPO" \
  --title "🎨 EPIC 6: Frontend (Next.js)" \
  --label "epic,frontend" \
  --body "## Objetivo
Implementar interface web com Next.js 14 para interação do usuário.

## Escopo
- Setup Next.js com Tailwind CSS
- Interface de seleção (UFs multi-select e período)
- Tela de resultados com resumo LLM
- API Routes para buscar e download
- Sistema de cache para downloads

## Issues Relacionadas
- [ ] #23 - Setup Next.js 14 com Tailwind CSS
- [ ] #24 - Implementar interface de seleção (UFs e período)
- [ ] #25 - Implementar tela de resultados com resumo LLM
- [ ] #26 - Implementar API Routes (/api/buscar e /api/download)
- [ ] #27 - Implementar sistema de cache para downloads

## Referência PRD
Seção 7 - Interface Web

## Critérios de Aceitação
- [ ] Next.js 14 configurado com App Router
- [ ] Tailwind CSS funcionando
- [ ] Multi-select de UFs com feedback visual
- [ ] Seleção de período com validação
- [ ] Resumo LLM exibido com formatação
- [ ] Download de Excel funcionando
- [ ] Loading states e error handling
- [ ] Responsivo (desktop e mobile)"

# Issue 23
gh issue create --repo "$REPO" \
  --title "Setup Next.js 14 com Tailwind CSS" \
  --label "frontend,setup" \
  --body "## Descrição
Configurar Next.js 14 com App Router e Tailwind CSS conforme PRD seção 7.

## Tecnologias
- Next.js 14 (App Router)
- React 18
- Tailwind CSS 3
- TypeScript 5

## Estrutura
\`\`\`
frontend/
├── app/
│   ├── page.tsx
│   ├── layout.tsx
│   ├── loading.tsx
│   ├── error.tsx
│   └── api/
│       ├── buscar/route.ts
│       └── download/route.ts
├── package.json
├── tailwind.config.js
└── tsconfig.json
\`\`\`

## Tarefas
- [ ] Inicializar Next.js 14 com \`create-next-app\`
- [ ] Configurar TypeScript
- [ ] Configurar Tailwind CSS
- [ ] Criar estrutura de pastas App Router
- [ ] Criar layout.tsx base
- [ ] Configurar package.json conforme PRD seção 9.2
- [ ] Testar dev server em porta 3000

## Referência PRD
Seção 7.1 - Stack Frontend
Seção 7.2 - Estrutura de Páginas
Seção 9.2 - Frontend Dependencies

## Relacionado
Epic #22"

# Issue 24
gh issue create --repo "$REPO" \
  --title "Implementar interface de seleção (UFs e período)" \
  --label "frontend,feature" \
  --body "## Descrição
Implementar componente principal com seleção de UFs e período.

## Componentes
1. **Multi-select de UFs**
   - Botões toggle para cada UF (27 estados)
   - \"Selecionar todos\" / \"Limpar\"
   - Feedback visual (verde quando selecionado)
   - Contador de selecionados

2. **Seleção de Período**
   - Input date para data inicial
   - Input date para data final
   - Validação: data_final >= data_inicial
   - Validação: diferença <= 30 dias
   - Default: últimos 7 dias

3. **Botão de Busca**
   - Desabilitado se nenhuma UF selecionada
   - Loading state durante busca
   - Feedback visual de progresso

## Tarefas
- [ ] Implementar state management (useState)
- [ ] Implementar multi-select de UFs conforme PRD seção 7.3
- [ ] Implementar seleção de período
- [ ] Validações de data
- [ ] Estilização com Tailwind CSS
- [ ] Feedback visual de estados (loading, error)
- [ ] Responsividade mobile

## Referência PRD
Seção 7.3 - Componente Principal (linhas 1196-1393)

## Relacionado
Epic #22"

# Issue 25
gh issue create --repo "$REPO" \
  --title "Implementar tela de resultados com resumo LLM" \
  --label "frontend,feature" \
  --body "## Descrição
Implementar exibição de resultados com resumo GPT e botão de download.

## Componentes de Resultado

1. **Resumo Executivo**
   - Card verde com resumo em texto
   - Stats: total de licitações e valor total
   - Destaques em lista
   - Alerta de urgência (se houver)
   - Distribuição por UF

2. **Botão de Download**
   - Link para \`/api/download?id={download_id}\`
   - Mostra quantidade de licitações
   - Ícone de download
   - Azul com hover effect

3. **Loading State**
   - Skeleton loading durante busca
   - Mensagem de progresso

4. **Error State**
   - Card vermelho com mensagem de erro
   - Opção de tentar novamente

## Tarefas
- [ ] Implementar componente de resumo conforme PRD seção 7.3
- [ ] Estilizar stats (grandes números verde)
- [ ] Renderizar destaques como lista
- [ ] Exibir alerta de urgência (amarelo)
- [ ] Botão de download com link correto
- [ ] Loading state com skeleton
- [ ] Error handling com mensagem clara
- [ ] Responsividade

## Referência PRD
Seção 7.3 - Componente Principal (linhas 1394-1453)

## Relacionado
Epic #22"

# Issue 26
gh issue create --repo "$REPO" \
  --title "Implementar API Routes (/api/buscar e /api/download)" \
  --label "frontend,feature" \
  --body "## Descrição
Implementar Next.js API Routes para comunicação com backend.

## Route 1: POST /api/buscar
Proxy para backend FastAPI:
- Validar request body
- Chamar \`{BACKEND_URL}/buscar\`
- Cachear Excel para download
- Retornar resumo + download_id

## Route 2: GET /api/download
Servir Excel cacheado:
- Validar query param \`id\`
- Buscar buffer no cache
- Retornar arquivo com headers corretos
- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment

## Tarefas
- [ ] Implementar \`app/api/buscar/route.ts\` conforme PRD seção 7.4
- [ ] Implementar \`app/api/download/route.ts\` conforme PRD seção 7.5
- [ ] Validação de inputs (Zod ou native)
- [ ] Tratamento de erros HTTP
- [ ] Configurar env var BACKEND_URL
- [ ] Testes de integração

## Referência PRD
Seção 7.4 - API Route: Buscar (linhas 1456-1525)
Seção 7.5 - API Route: Download (linhas 1527-1563)

## Relacionado
Epic #22"

# Issue 27
gh issue create --repo "$REPO" \
  --title "Implementar sistema de cache para downloads" \
  --label "frontend,feature" \
  --body "## Descrição
Implementar cache em memória para arquivos Excel gerados.

## Especificação
- **Estrutura**: Map<string, Buffer>
- **TTL**: 10 minutos
- **Key**: UUID gerado no /api/buscar
- **Cleanup**: setTimeout para remover após TTL

## Implementação
\`\`\`typescript
const downloadCache = new Map<string, Buffer>();

// Em /api/buscar
const downloadId = randomUUID();
downloadCache.set(downloadId, excelBuffer);
setTimeout(() => downloadCache.delete(downloadId), 10 * 60 * 1000);

// Em /api/download
const buffer = downloadCache.get(id);
if (!buffer) return 404;
\`\`\`

## Nota para Produção
Em produção, substituir por Redis ou similar.

## Tarefas
- [ ] Criar Map compartilhado entre routes
- [ ] Gerar UUID no /api/buscar
- [ ] Cachear buffer com TTL
- [ ] Recuperar buffer no /api/download
- [ ] Implementar cleanup automático
- [ ] Tratar caso de cache miss (404)
- [ ] Documentar limitação do cache em memória

## Referência PRD
Seção 7.4 - API Route: Buscar (linhas 1504-1510)

## Relacionado
Epic #22
Relacionado: #26"

echo "✓ EPIC 6 completo (5 issues)"

# EPIC 7: Integração e Deploy
gh issue create --repo "$REPO" \
  --title "🚀 EPIC 7: Integração e Deploy" \
  --label "epic,integration,deployment" \
  --body "## Objetivo
Integrar todos os componentes e preparar para deploy.

## Escopo
- Integração frontend ↔ backend
- Testes end-to-end do fluxo completo
- Documentação de uso
- Deploy inicial

## Issues Relacionadas
- [ ] #28 - Integrar frontend ↔ backend
- [ ] #29 - Testes end-to-end do fluxo completo
- [ ] #30 - Documentação de uso (README.md)
- [ ] #31 - Deploy inicial

## Referência PRD
Todas as seções (fluxo completo)

## Critérios de Aceitação
- [ ] Frontend se comunica com backend sem erros
- [ ] Fluxo completo: seleção → busca → filtro → resumo → download
- [ ] README.md com instruções claras
- [ ] Ambiente de produção funcionando
- [ ] Variáveis de ambiente documentadas"

# Issue 28
gh issue create --repo "$REPO" \
  --title "Integrar frontend ↔ backend" \
  --label "integration,feature" \
  --body "## Descrição
Conectar frontend Next.js com backend FastAPI e testar comunicação.

## Tarefas de Integração
1. **Configurar CORS no backend**
   - Permitir origem do frontend
   - Verificar headers permitidos

2. **Configurar BACKEND_URL no frontend**
   - Env var em .env.local
   - Usar em API routes

3. **Testar comunicação**
   - POST /api/buscar → backend /buscar
   - Verificar response format
   - Testar error handling

4. **Ajustes de tipos**
   - Garantir schema consistency
   - TypeScript interfaces match Pydantic

## Tarefas
- [ ] Configurar CORS no backend
- [ ] Configurar BACKEND_URL no frontend
- [ ] Testar POST /api/buscar
- [ ] Testar GET /api/download
- [ ] Validar schemas (frontend ↔ backend)
- [ ] Testar error scenarios
- [ ] Documentar env vars necessárias

## Relacionado
Epic #27
Depende de: EPICs 5 e 6"

# Issue 29
gh issue create --repo "$REPO" \
  --title "Testes end-to-end do fluxo completo" \
  --label "testing,feature" \
  --body "## Descrição
Testar fluxo completo da aplicação: UI → API → PNCP → Filtro → LLM → Excel → Download.

## Cenários de Teste

1. **Fluxo Happy Path**
   - Selecionar 3 UFs (SC, PR, RS)
   - Período: últimos 7 dias
   - Aguardar busca
   - Verificar resumo exibido
   - Baixar Excel
   - Validar conteúdo do Excel

2. **Fluxo com Fallback LLM**
   - Remover OPENAI_API_KEY
   - Executar busca
   - Verificar resumo básico (fallback)

3. **Fluxo sem Resultados**
   - Selecionar UF remota
   - Período antigo
   - Verificar mensagem \"0 licitações\"

4. **Fluxo com Erro PNCP**
   - Simular timeout/erro na API
   - Verificar mensagem de erro apropriada

5. **Validações de Input**
   - Tentar buscar sem UFs → erro
   - Período > 30 dias → erro
   - Data final < data inicial → erro

## Tarefas
- [ ] Testar fluxo happy path completo
- [ ] Testar fallback LLM
- [ ] Testar caso sem resultados
- [ ] Testar error handling
- [ ] Testar validações de input
- [ ] Testar download de Excel
- [ ] Verificar conteúdo do Excel gerado
- [ ] Documentar bugs encontrados

## Relacionado
Epic #27
Depende de: #28"

# Issue 30
gh issue create --repo "$REPO" \
  --title "Documentação de uso (README.md)" \
  --label "documentation" \
  --body "## Descrição
Criar README.md completo com instruções de setup, uso e arquitetura.

## Seções do README

1. **Introdução**
   - O que é o BidIQ Uniformes POC
   - Funcionalidades principais

2. **Requisitos**
   - Python 3.11+
   - Node.js 20+
   - Docker (opcional)
   - OpenAI API Key

3. **Instalação**
   - Clone do repositório
   - Setup backend
   - Setup frontend
   - Configuração de .env

4. **Execução**
   - Com Docker Compose
   - Sem Docker (manual)

5. **Uso**
   - Acessar interface
   - Selecionar UFs e período
   - Interpretar resultados
   - Download do Excel

6. **Arquitetura**
   - Diagrama de fluxo (do PRD seção 1.1)
   - Tecnologias utilizadas
   - Estrutura de diretórios

7. **Configuração**
   - Variáveis de ambiente
   - Parâmetros do sistema

8. **Troubleshooting**
   - Erros comuns e soluções

9. **Referências**
   - API PNCP
   - PRD v0.2

## Tarefas
- [ ] Criar estrutura do README
- [ ] Documentar requisitos
- [ ] Documentar instalação passo a passo
- [ ] Documentar execução (Docker e manual)
- [ ] Documentar uso da interface
- [ ] Incluir diagrama de arquitetura
- [ ] Documentar variáveis de ambiente
- [ ] Seção de troubleshooting
- [ ] Adicionar badges (se aplicável)
- [ ] Revisar e validar instruções

## Relacionado
Epic #27"

# Issue 31
gh issue create --repo "$REPO" \
  --title "Deploy inicial" \
  --label "deployment,infrastructure" \
  --body "## Descrição
Realizar deploy inicial em ambiente de produção ou staging.

## Opções de Deploy

1. **Vercel** (Frontend)
   - Next.js otimizado
   - Edge functions
   - Configurar BACKEND_URL

2. **Railway/Render** (Backend)
   - FastAPI com Uvicorn
   - Configurar env vars
   - Health check endpoint

3. **Docker Compose** (Self-hosted)
   - Build e push de imagens
   - Configurar reverse proxy
   - SSL/HTTPS

## Tarefas
- [ ] Escolher plataforma de deploy
- [ ] Configurar CI/CD (opcional)
- [ ] Deploy do backend
- [ ] Deploy do frontend
- [ ] Configurar variáveis de ambiente em produção
- [ ] Configurar domínio/URL
- [ ] Testar aplicação em produção
- [ ] Configurar CORS para domínio de produção
- [ ] Monitoramento básico (logs, health check)
- [ ] Documentar processo de deploy no README

## Referência PRD
Arquitetura completa

## Relacionado
Epic #27
Depende de: #28, #29, #30"

echo "✓ EPIC 7 completo (4 issues)"
echo ""
echo "======================================"
echo "✓ TODAS AS 31 ISSUES CRIADAS COM SUCESSO!"
echo "======================================"
echo ""
echo "Resumo:"
echo "- EPIC 1: Setup e Infraestrutura (4 issues)"
echo "- EPIC 2: Cliente PNCP e Resiliência (4 issues)"
echo "- EPIC 3: Motor de Filtragem (3 issues)"
echo "- EPIC 4: Geração de Saídas (3 issues)"
echo "- EPIC 5: API Backend (4 issues)"
echo "- EPIC 6: Frontend Next.js (5 issues)"
echo "- EPIC 7: Integração e Deploy (4 issues)"
echo ""
echo "Total: 31 issues organizadas em 7 épicos"
echo ""
echo "Acesse: https://github.com/$REPO/issues"
