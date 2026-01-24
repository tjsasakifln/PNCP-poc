# Tech Stack - PNCP POC

## Backend

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|---------|---------------|
| Framework | FastAPI | 0.109+ | Performance, async support, validação automática |
| Runtime | Python | 3.11+ | Ecosystem rico para data processing |
| HTTP Client | Requests + urllib3 | 2.31+ | Retry logic, connection pooling |
| Excel | openpyxl | 3.1+ | Geração de planilhas formatadas |
| LLM SDK | OpenAI | 1.10+ | Integração com GPT-4.1-nano |
| Validação | Pydantic | 2.5+ | Type safety, structured outputs |

## Frontend

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|---------|---------------|
| Framework | Next.js | 14+ | App Router, SSR, API routes |
| Runtime | React | 18+ | Component model, hooks |
| Styling | Tailwind CSS | 3.4+ | Utility-first, responsive |
| Language | TypeScript | 5.3+ | Type safety |

## Infraestrutura

| Componente | Tecnologia | Versão |
|------------|------------|---------|
| Container | Docker | 24+ |
| Orchestration | Docker Compose | 2.0+ |
| Reverse Proxy | Nginx | (opcional) |

## APIs Externas

| Serviço | Endpoint | Uso |
|---------|----------|-----|
| PNCP | `https://pncp.gov.br/api/consulta/v1` | Busca de licitações |
| OpenAI | `api.openai.com` | Resumos via GPT-4.1-nano |

## Dependências Python

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
requests==2.31.0
urllib3==2.1.0
openpyxl==3.1.2
openai==1.10.0
python-dotenv==1.0.0
```

## Dependências Node.js

```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  },
  "devDependencies": {
    "@types/node": "20.11.0",
    "@types/react": "18.2.48",
    "typescript": "5.3.3",
    "tailwindcss": "3.4.1"
  }
}
```
