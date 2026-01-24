# BidIQ Uniformes - POC v0.2

Sistema de busca e análise de licitações de uniformes do Portal Nacional de Contratações Públicas (PNCP).

## 📋 Descrição

POC para automatizar a busca de oportunidades de licitações de uniformes e fardamentos através da API do PNCP, com:

- ✅ Filtragem inteligente por estado, valor e keywords
- ✅ Geração automática de planilhas Excel formatadas
- ✅ Resumo executivo via GPT-4.1-nano
- ✅ Interface web para seleção de parâmetros
- ✅ Retry logic e resiliência para API instável

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- OpenAI API key

### Instalação

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

## 📚 Documentação

- [PRD Técnico](./PRD.md) - Especificação completa
- [Tech Stack](./docs/framework/tech-stack.md) - Tecnologias utilizadas
- [Source Tree](./docs/framework/source-tree.md) - Estrutura de arquivos
- [Coding Standards](./docs/framework/coding-standards.md) - Padrões de código

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

## 🏗️ Arquitetura

```
┌─────────────┐
│   Next.js   │  Frontend (React + Tailwind)
└──────┬──────┘
       │ HTTP
┌──────▼──────┐
│   FastAPI   │  Backend (Python)
└──────┬──────┘
       │
       ├─────► PNCP API (Licitações)
       └─────► OpenAI API (Resumos)
```

## 📊 Fluxo de Dados

1. Usuário seleciona UFs e período
2. Backend consulta API PNCP com retry logic
3. Motor de filtragem aplica regras:
   - UF válida
   - R$ 50k - R$ 5M
   - Keywords de uniformes
   - Status aberto
4. GPT-4.1-nano gera resumo executivo
5. Excel formatado + resumo retornados

## 🧪 Testes

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 🚢 Deploy

### Docker (Recomendado)

```bash
docker-compose up -d
```

### Manual

Ver [PRD.md](./PRD.md) seção 11 para instruções detalhadas.

## 📝 Variáveis de Ambiente

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Backend
BACKEND_PORT=8000
LOG_LEVEL=INFO

# PNCP Client
PNCP_TIMEOUT=30
PNCP_MAX_RETRIES=5

# LLM
LLM_MODEL=gpt-4.1-nano
LLM_TEMPERATURE=0.3
```

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Commit: `git commit -m "feat: adicionar nova feature"`
3. Push: `git push origin feature/nova-feature`
4. Abra um Pull Request

## 📄 Licença

MIT

## 🔗 Links Úteis

- [API PNCP](https://pncp.gov.br/api/consulta/swagger-ui/index.html)
- [AIOS Framework](https://github.com/tjsasakifln/aios-core)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
