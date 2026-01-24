# Source Tree - PNCP POC

## Estrutura de Diretórios

```
pncp-poc/
├── backend/                    # API Backend (FastAPI)
│   ├── main.py                # Entrypoint da aplicação
│   ├── config.py              # Configurações e variáveis de ambiente
│   ├── pncp_client.py         # Cliente HTTP para API PNCP
│   ├── filter.py              # Motor de filtragem de licitações
│   ├── excel.py               # Gerador de planilhas Excel
│   ├── llm.py                 # Integração com GPT-4.1-nano
│   ├── schemas.py             # Modelos Pydantic
│   └── requirements.txt       # Dependências Python
│
├── frontend/                   # Interface Web (Next.js)
│   ├── app/
│   │   ├── page.tsx           # Página principal
│   │   ├── layout.tsx         # Layout base
│   │   └── api/
│   │       ├── buscar/route.ts    # Endpoint de busca
│   │       └── download/route.ts  # Endpoint de download
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── docs/                       # Documentação
│   ├── framework/
│   │   ├── tech-stack.md      # Stack tecnológico
│   │   ├── source-tree.md     # Estrutura de arquivos
│   │   └── coding-standards.md # Padrões de código
│   ├── architecture/          # Decisões arquiteturais
│   ├── stories/               # Stories de desenvolvimento
│   │   └── backlog/
│   └── qa/                    # QA e testes
│
├── .aios-core/                # Framework AIOS
│   ├── core-config.yaml       # Configuração do AIOS
│   └── ...
│
├── .claude/                   # Configurações Claude Code
│   ├── commands/
│   └── rules/
│
├── .ai/                       # Logs de decisões
│   └── decision-logs-index.md
│
├── PRD.md                     # Product Requirements Document
├── .env.example               # Template de variáveis de ambiente
├── .gitignore
├── docker-compose.yml         # (a criar)
└── README.md                  # (a criar)
```

## Convenções de Nomenclatura

### Python
- **Arquivos**: `snake_case.py`
- **Classes**: `PascalCase`
- **Funções**: `snake_case()`
- **Constantes**: `UPPER_SNAKE_CASE`

### TypeScript/React
- **Arquivos de componentes**: `PascalCase.tsx`
- **Arquivos utilitários**: `camelCase.ts`
- **Componentes**: `PascalCase`
- **Funções**: `camelCase()`
- **Constantes**: `UPPER_SNAKE_CASE`

## Fluxo de Dados

```
Frontend (Next.js)
    ↓ HTTP POST /api/buscar
Backend API (FastAPI)
    ↓ fetch_all()
PNCP API Client
    ↓ paginação + retry
API PNCP
    ↓ response
Filter Engine
    ↓ licitações filtradas
Excel Generator + LLM Summary
    ↓ excel_base64 + resumo
Frontend (Download)
```

## Deployment

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm start
```

### Docker (Recomendado)
```bash
docker-compose up -d
```

## Variáveis de Ambiente

Ver `.env.example` para lista completa de variáveis necessárias.
