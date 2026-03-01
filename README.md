# SmartLic — Inteligencia em Licitacoes Publicas

[![Backend Tests](https://github.com/tjsasakifln/PNCP-poc/actions/workflows/tests.yml/badge.svg)](https://github.com/tjsasakifln/PNCP-poc/actions/workflows/tests.yml)
[![CodeQL](https://github.com/tjsasakifln/PNCP-poc/actions/workflows/codeql.yml/badge.svg)](https://github.com/tjsasakifln/PNCP-poc/actions/workflows/codeql.yml)

**SmartLic** e uma plataforma de inteligencia em licitacoes publicas que automatiza a descoberta, analise e qualificacao de oportunidades para empresas B2G (Business-to-Government).

**Production:** https://smartlic.tech | **Estagio:** POC avancado (v0.5) | **Backend:** 65+ modulos | **Frontend:** 22 paginas

## Sobre o Projeto

### Funcionalidades Principais

- **Busca multi-fonte** — Agrega PNCP + PCP v2 + ComprasGov v3 com deduplicacao inteligente
- **15 setores** — Vestuario, alimentos, informatica, engenharia, saude, vigilancia, transporte, e 8 outros
- **Classificacao IA** — GPT-4.1-nano classifica relevancia setorial (keyword + zero-match)
- **Analise de viabilidade** — 4 fatores: modalidade (30%), timeline (25%), valor (25%), geografia (20%)
- **Pipeline de oportunidades** — Kanban com drag-and-drop para gerenciar editais
- **Relatorios** — Excel estilizado + resumo executivo com IA
- **Historico + Analytics** — Buscas salvas, sessoes, dashboard com metricas
- **Resiliencia** — Circuit breakers, two-level cache (SWR), fallback cascade
- **Billing** — Stripe subscriptions (SmartLic Pro R$397/mes + trial 14 dias)
- **Observabilidade** — Prometheus metrics, OpenTelemetry tracing, Sentry errors
- **304+ testes automatizados** — 169 backend + 135 frontend + E2E (Playwright)

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

#### Pré-requisitos
- Docker Engine 20.10+
- Docker Compose 2.0+
- OpenAI API key

#### Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd pncp-poc
```

2. Configure variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

3. Inicie os serviços com Docker Compose:
```bash
docker-compose up
```

4. Acesse os serviços:
- **Frontend**: http://localhost:3000 (Aplicação Next.js)
- **Backend API**: http://localhost:8000/docs (Swagger UI)

**📖 Guia completo de integração:** [docs/INTEGRATION.md](docs/INTEGRATION.md)

#### Testando a Aplicacao

**Production:**
1. Acesse https://smartlic.tech
2. Crie conta ou faca login
3. Complete o onboarding (CNAE + UFs + objetivo)
4. Busque licitacoes (setor + UFs + periodo)
5. Analise resultados com badges de relevancia e viabilidade

**Local Development:**
1. Acesse http://localhost:3000
2. Mesmos passos acima

#### Comandos Docker Úteis

```bash
# Iniciar em background (detached)
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend

# Parar serviços
docker-compose down

# Rebuild após mudanças em dependências
docker-compose build --no-cache

# Ver status dos containers
docker-compose ps

# Executar comandos no container
docker-compose exec backend python -c "print('Hello from container')"
```

---

### Opção 2: Instalação Manual

#### Pré-requisitos
- Python 3.12+
- Node.js 18+
- OpenAI API key
- Supabase project (URL + keys)
- Redis (optional, has fallback)

#### Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd pncp-poc
```

2. Configure variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

3. Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

4. Frontend:
```bash
cd frontend
npm install
npm run dev
```

5. Acesse: http://localhost:3000

## Estrutura de Diretorios

```
pncp-poc/
├── backend/                    # API Backend (FastAPI 0.129, Python 3.12)
│   ├── main.py                # Entrypoint FastAPI
│   ├── config.py              # 70+ env vars
│   ├── search_pipeline.py     # Pipeline multi-fonte
│   ├── consolidation.py       # Agregacao + dedup
│   ├── pncp_client.py         # PNCP API client (circuit breaker)
│   ├── filter.py              # Keyword density scoring
│   ├── llm_arbiter.py         # LLM zero-match classification
│   ├── viability.py           # Viability assessment (4 fatores)
│   ├── search_cache.py        # Two-level cache + SWR
│   ├── job_queue.py           # ARQ background jobs
│   ├── metrics.py             # Prometheus exporter
│   ├── telemetry.py           # OpenTelemetry tracing
│   ├── sectors_data.yaml      # 15 setores (keywords, exclusoes)
│   ├── routes/                # 19 route modules (49 endpoints)
│   ├── clients/               # PCP, ComprasGov, etc.
│   ├── services/              # Billing, sanctions
│   ├── models/                # Cache, search state, stripe
│   ├── migrations/            # 7 backend migrations
│   ├── tests/                 # 169 test files
│   │   ├── integration/       # 10 integration test files
│   │   └── snapshots/         # OpenAPI schema drift detection
│   └── requirements.txt       # 32 production packages
│
├── frontend/                   # Next.js 16, React 18, TypeScript 5.9
│   ├── app/                   # 22 pages (App Router)
│   │   ├── buscar/            # Main search page + 18 components
│   │   ├── dashboard/         # Analytics dashboard
│   │   ├── pipeline/          # Opportunity pipeline (kanban)
│   │   ├── admin/             # Admin + cache dashboards
│   │   ├── onboarding/        # 3-step wizard
│   │   └── api/               # API proxy routes
│   ├── components/            # 15 shared components
│   ├── hooks/                 # Custom hooks (useSearch, useSearchSSE)
│   ├── __tests__/             # 135 test files
│   ├── e2e-tests/             # Playwright E2E tests
│   └── package.json           # 46 packages (22 prod + 24 dev)
│
├── supabase/
│   └── migrations/            # 35 Supabase migrations
│
├── docs/                       # Documentacao
│   ├── summaries/             # gtm-resilience-summary, gtm-fixes-summary
│   ├── framework/             # tech-stack, coding-standards
│   ├── stories/               # Development stories
│   └── guides/                # Setup guides
│
├── .aios-core/                # AIOS Framework
│   └── development/           # Agents, tasks, workflows
│
├── PRD.md                     # Product Requirements Document
├── CLAUDE.md                  # Claude Code instructions
├── ROADMAP.md                 # Roadmap + backlog
├── CHANGELOG.md               # Detailed changelog
└── README.md                  # Este arquivo
```

## Documentacao

- [PRD Tecnico](./PRD.md) — Especificacao tecnica
- [Tech Stack](./docs/framework/tech-stack.md) — Tecnologias e versoes
- [Coding Standards](./docs/framework/coding-standards.md) — Padroes de codigo
- [Roadmap](./ROADMAP.md) — Status e backlog
- [CHANGELOG](./CHANGELOG.md) — Historico de versoes
- [GTM Resilience Summary](./docs/summaries/gtm-resilience-summary.md) — Arquitetura de resiliencia
- [GTM Fixes Summary](./docs/summaries/gtm-fixes-summary.md) — Fixes de producao

## 🤖 AIOS Framework

Este projeto utiliza o [AIOS Framework](https://github.com/tjsasakifln/aios-core) para desenvolvimento orquestrado por IA.

### Agentes Disponíveis

- **@dev** - Desenvolvimento e implementação
- **@qa** - Quality assurance e testes
- **@architect** - Decisões arquiteturais
- **@pm** - Gerenciamento de stories

### Comandos AIOS

```bash
# Criar nova story
/AIOS/story

# Review de código
/AIOS/review

# Gerar documentação
/AIOS/docs
```

Ver [User Guide](./.aios-core/user-guide.md) para lista completa de comandos.

## Arquitetura

```
┌──────────────┐
│   Next.js    │  Frontend (22 paginas, React + Tailwind)
└──────┬───────┘
       │ API Proxy
┌──────▼───────┐
│   FastAPI    │  Backend (65+ modulos, 49 endpoints)
└──────┬───────┘
       │
       ├─────► PNCP API (prioridade 1)
       ├─────► PCP v2 API (prioridade 2)
       ├─────► ComprasGov v3 (prioridade 3)
       ├─────► OpenAI API (classificacao + resumos)
       ├─────► Stripe API (billing)
       ├─────► Supabase (database + auth)
       └─────► Redis (cache + jobs)
```

## Fluxo de Dados

1. Usuario seleciona setor, UFs e periodo
2. Backend consulta 3 fontes em paralelo (PNCP + PCP + ComprasGov)
3. Consolidacao + deduplicacao por prioridade
4. Filtragem: UF, valor, keywords, LLM zero-match, status
5. Viability assessment (4 fatores)
6. LLM summary + Excel (ARQ background jobs)
7. Resultados via SSE em tempo real

## Testes

```bash
# Backend (169 test files, ~3966 passing)
cd backend && pytest

# Frontend (135 test files, ~1921 passing)
cd frontend && npm test

# E2E (Playwright, 60 critical flows)
cd frontend && npm run test:e2e
```

## 🚢 Deploy

### Docker Compose (Desenvolvimento)

O projeto inclui configuração completa do Docker Compose para ambiente de desenvolvimento:

**Características:**
- ✅ Hot-reload para backend (mudanças de código reiniciam automaticamente)
- ✅ Health checks para todos os serviços
- ✅ Volumes montados para desenvolvimento
- ✅ Network bridge para comunicação inter-serviços
- ✅ Variáveis de ambiente injetadas de `.env`

**Serviços:**
- `backend` - FastAPI em Python 3.11 (porta 8000)
- `frontend` - Placeholder nginx (porta 3000)

```bash
# Iniciar ambiente completo
docker-compose up -d

# Verificar saúde dos serviços
docker-compose ps

# Ver logs
docker-compose logs -f
```

### Deploy em Producao

**Production:**
- **Frontend:** https://smartlic.tech
- **Backend API:** Railway (web + worker processes)
- **Database:** Supabase Cloud (PostgreSQL + Auth)
- **Cache:** Redis (Upstash ou Railway addon)

**Plataformas:**
- **Frontend + Backend + Worker:** Railway (tudo em um)
- **Database + Auth:** Supabase Cloud
- **Payments:** Stripe

**Quick Deploy:**
```bash
# Railway (backend + frontend)
npm install -g @railway/cli
railway login
railway up
```

## 📝 Variáveis de Ambiente

### Local Development

Configure as variáveis abaixo no arquivo `.env` (copie de `.env.example`):

```env
# === REQUIRED ===
OPENAI_API_KEY=sk-...              # Obrigatória - Get from https://platform.openai.com/api-keys

# === OPTIONAL (Backend) ===
BACKEND_PORT=8000                  # Porta do FastAPI (default: 8000)
LOG_LEVEL=INFO                     # Nível de logging: DEBUG|INFO|WARNING|ERROR
BACKEND_URL=http://localhost:8000  # URL base para frontend chamar backend

# === OPTIONAL (PNCP Client) ===
PNCP_TIMEOUT=30                    # Timeout por request em segundos (default: 30)
PNCP_MAX_RETRIES=5                 # Máximo de tentativas de retry (default: 5)
PNCP_RATE_LIMIT=100                # Delay mínimo entre requests em ms (default: 100)

# === OPTIONAL (LLM) ===
LLM_MODEL=gpt-4.1-nano              # Modelo OpenAI (default: gpt-4.1-nano)
LLM_TEMPERATURE=0.3                # Temperatura do modelo (0.0-2.0, default: 0.3)
LLM_MAX_TOKENS=500                 # Máximo de tokens na resposta (default: 500)
```

### Production Environment

Production environment variables are configured in Railway dashboard.
See [.env.example](.env.example) for the full list of 70+ environment variables with documentation.

---

## 🔧 Troubleshooting

### Problemas Comuns e Soluções

#### 0. Production Issues

**Problema:** Frontend não consegue conectar ao backend em produção

**Solução:**
1. Verifique se backend está online:
   ```bash
   curl https://smartlic.tech/health
   # Deve retornar: {"status":"healthy"}
   ```

2. Verifique variável de ambiente no Railway:
   - Acesse Railway dashboard → Project Settings → Environment Variables
   - Confirme: `BACKEND_URL=https://smartlic.tech`

3. Verifique CORS no backend:
   - Backend deve permitir origem do Railway frontend
   - Ver `backend/main.py` linha ~48 para configuração CORS

**Problema:** "Service Unavailable" ou "502 Bad Gateway" na API

**Solução:**
1. Verifique logs do Railway:
   ```bash
   railway logs
   ```

2. Causas comuns:
   - Backend em cold start (primeiro request após inatividade) - aguarde 30s
   - OpenAI API key inválida - verifique no Railway dashboard
   - Memória insuficiente - verifique métricas no Railway
   - Build falhou - verifique deploy logs

**Problema:** Frontend mostra erro de CORS em produção

**Solução:**
Atualizar lista de origens permitidas em `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smartlic.tech",  # Production frontend
        "http://localhost:3000"  # Local development
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

#### 1. Docker / Container Issues

**Problema:** `Cannot connect to the Docker daemon`
```bash
# Solução: Inicie o Docker Desktop
# Windows: Procure "Docker Desktop" no menu Iniciar
# macOS: Abra Docker.app da pasta Applications
# Linux: sudo systemctl start docker
```

**Problema:** `Error response from daemon: Conflict. The container name "/bidiq-backend" is already in use`
```bash
# Solução: Remova containers antigos
docker-compose down
docker-compose up --build
```

**Problema:** `bidiq-backend exited with code 137` (Out of Memory)
```bash
# Solução: Aumente memória do Docker Desktop
# Settings → Resources → Memory: aumentar para 4GB+
```

**Problema:** Serviços não ficam "healthy" após 2 minutos
```bash
# Diagnóstico: Verifique logs dos containers
docker-compose logs backend
docker-compose logs frontend

# Solução: Health check automático
bash scripts/verify-integration.sh
```

---

#### 2. Backend API Issues

**Problema:** `ImportError: No module named 'httpx'`
```bash
# Solução: Reinstale dependências
cd backend
pip install -r requirements.txt --force-reinstall
```

**Problema:** `401 Unauthorized` ou `invalid_api_key` (OpenAI)
```bash
# Solução 1: Verifique se a chave está correta
cat .env | grep OPENAI_API_KEY
# Deve exibir: OPENAI_API_KEY=sk-...

# Solução 2: Verifique se a chave tem créditos
# Acesse: https://platform.openai.com/usage

# Solução 3: Use o modo fallback (sem LLM)
# O sistema possui fallback automático - não precisa de API key para funcionar
```

**Problema:** `PNCP API timeout` ou `504 Gateway Timeout`
```bash
# Solução: Aumente o timeout (API PNCP é instável)
# No .env:
PNCP_TIMEOUT=60
PNCP_MAX_RETRIES=10
```

**Problema:** `429 Too Many Requests` (PNCP Rate Limit)
```bash
# Solução: O cliente possui rate limiting automático
# Aguarde 1 minuto e tente novamente
# O sistema respeita header Retry-After automaticamente
```

**Problema:** `No matching distributions found for openpyxl`
```bash
# Solução: Use Python 3.11+ (versão mínima suportada)
python --version  # Deve ser 3.11.0 ou superior
# Se necessário, instale Python 3.11: https://www.python.org/downloads/
```

---

#### 3. Frontend Issues

**Problema:** `Error: Cannot find module 'next'`
```bash
# Solução: Reinstale node_modules
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Problema:** `CORS policy: No 'Access-Control-Allow-Origin' header`
```bash
# Solução 1: Verifique se backend está rodando
curl http://localhost:8000/health
# Deve retornar: {"status":"healthy"}

# Solução 2: Verifique CORS no backend (main.py linhas 49-55)
# CORS já está configurado para allow_origins=["*"]
# Se problema persistir, verifique BACKEND_URL no .env
```

**Problema:** Frontend mostra "Nenhum resultado encontrado" mas backend retornou dados
```bash
# Diagnóstico: Verifique console do navegador (F12)
# Procure por erros de parse JSON ou validação de schema

# Solução: Verifique estrutura de resposta da API
curl -X POST http://localhost:8000/buscar \
  -H "Content-Type: application/json" \
  -d '{"ufs":["SC"],"data_inicial":"2026-01-01","data_final":"2026-01-31"}'
```

**Problema:** `Error: ENOENT: no such file or directory, open '.next/...'`
```bash
# Solução: Rebuild Next.js
cd frontend
rm -rf .next
npm run build
npm run dev
```

---

#### 4. Test Failures

**Problema:** `pytest: command not found`
```bash
# Solução: Ative o ambiente virtual
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Problema:** `FAILED test_pncp_integration.py` (testes de integração)
```bash
# Solução: Testes de integração requerem internet e API PNCP funcionando
# Pule estes testes com:
pytest -m "not integration"
```

**Problema:** Coverage abaixo do threshold (70% backend / 60% frontend)
```bash
# Diagnóstico: Veja relatório detalhado
cd backend && pytest --cov --cov-report=html
# Abra: backend/htmlcov/index.html no navegador

cd frontend && npm run test:coverage
# Abra: frontend/coverage/index.html no navegador

# Solução: Adicione testes para módulos não cobertos
```

---

#### 5. Excel Download Issues

**Problema:** Botão "Download Excel" não funciona ou arquivo corrupto
```bash
# Diagnóstico: Verifique cache de downloads
# Frontend usa cache in-memory com TTL de 10min

# Solução 1: Tente novamente (cache pode ter expirado)
# Solução 2: Verifique logs do backend
docker-compose logs backend | grep "download_id"

# Solução 3: Teste endpoint diretamente
curl "http://localhost:3000/api/download?id=DOWNLOAD_ID" -o test.xlsx
```

**Problema:** Excel abre com erro "formato inválido"
```bash
# Solução: Verifique se openpyxl está instalado
cd backend
python -c "import openpyxl; print(openpyxl.__version__)"
# Deve exibir versão 3.1.0+
```

---

#### 6. E2E Test Issues

**Problema:** E2E tests failing with "Timed out waiting for page"
```bash
# Solução: Garanta que ambos serviços estejam rodando
docker-compose up -d
bash scripts/verify-integration.sh  # Health check

# Execute testes E2E
cd frontend
npm run test:e2e
```

**Problema:** `Error: browserType.launch: Executable doesn't exist`
```bash
# Solução: Instale browsers do Playwright
cd frontend
npx playwright install
```

---

### Scripts Úteis de Diagnóstico

```bash
# Health check completo (recomendado)
bash scripts/verify-integration.sh

# Verificar portas ocupadas
# Windows: netstat -ano | findstr :8000
# Linux/Mac: lsof -i :8000

# Rebuild completo (limpa cache)
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
docker-compose up

# Logs em tempo real de todos os serviços
docker-compose logs -f --tail=50

# Ver variáveis de ambiente carregadas
docker-compose exec backend env | grep -E "OPENAI|PNCP|LLM"
```

---

### Onde Buscar Ajuda

1. **Documentação Detalhada:**
   - [Integration Guide](./docs/INTEGRATION.md) - Troubleshooting E2E
   - [PRD.md](./PRD.md) - Especificação técnica completa

2. **Issues do GitHub:**
   - Procure issues existentes: https://github.com/tjsasakifln/PNCP-poc/issues
   - Crie nova issue se não encontrar solução

3. **Logs e Debugging:**
   ```bash
   # Backend logs estruturados
   docker-compose logs backend | grep -E "ERROR|WARNING"

   # Frontend logs (console do navegador)
   # Abra DevTools (F12) → Console
   ```

4. **Testes Automatizados:**
   - Backend: `cd backend && pytest -v`
   - Frontend: `cd frontend && npm test -- --verbose`
   - E2E: `cd frontend && npm run test:e2e`

---

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Commit: `git commit -m "feat: adicionar nova feature"`
3. Push: `git push origin feature/nova-feature`
4. Abra um Pull Request

## Licenca e Propriedade

Este software e de propriedade exclusiva da **CONFENGE AVALIACOES E INTELIGENCIA ARTIFICIAL LTDA**.

**Todos os direitos reservados.** Este codigo-fonte, incluindo mas nao se limitando a algoritmos, arquitetura, documentacao, configuracoes, e quaisquer materiais relacionados, e propriedade intelectual da CONFENGE. E estritamente proibido o uso, copia, modificacao, distribuicao, sublicenciamento ou qualquer forma de reproducao deste software, no todo ou em parte, sem consentimento previo por escrito da CONFENGE.

**Contato para licenciamento:**
- **Nome:** Tiago Sasaki
- **Telefone:** +55 (48) 9 8834-4559
- **Empresa:** CONFENGE Avaliacoes e Inteligencia Artificial LTDA

## Links Uteis

- [PNCP API](https://pncp.gov.br/api/consulta/swagger-ui/index.html)
- [PCP v2 API](https://compras.api.portaldecompraspublicas.com.br)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Stripe Docs](https://stripe.com/docs)
