# Tech Stack - Lei 14.133 Modalidades Squad

## Backend

### Python 3.11+
- **FastAPI** - REST API framework
- **Pydantic 2.0+** - Data validation and schemas
- **httpx** - Async HTTP client for source adapters
- **pytest** - Testing framework

### Key Libraries
```python
pydantic>=2.0.0      # Schema validation
httpx>=0.24.0        # Async HTTP client
pytest>=7.0.0        # Testing
pytest-asyncio       # Async test support
```

## Frontend

### React 18+ with TypeScript
- **Next.js 14+** - React framework
- **TypeScript 5+** - Type safety
- **TailwindCSS** - Styling

### Key Libraries
```json
{
  "react": "^18.0.0",
  "next": "^14.0.0",
  "typescript": "^5.0.0"
}
```

## Data Sources

### APIs Consulted
1. **PNCP** (Portal Nacional de Contratações Públicas) - Priority 1
2. **ComprasGov** (Dados Abertos Federal) - Priority 4
3. **Portal de Compras Públicas** - Priority 2
4. **Licitar.com** - Priority 5

### Modalidade Support by Source

| Source | Pregão | Concorrência | Concurso | Leilão | Dispensa | Inexig | Diálogo |
|--------|--------|--------------|----------|--------|----------|--------|---------|
| PNCP | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ComprasGov | ✅ | ⚠️ | ❓ | ⚠️ | ✅ | ⚠️ | ❓ |
| Portal Compras | ✅ | ⚠️ | ❓ | ⚠️ | ✅ | ⚠️ | ❓ |
| Licitar | ✅ | ⚠️ | ❓ | ⚠️ | ✅ | ⚠️ | ❓ |

**Legend:**
- ✅ Full support confirmed
- ⚠️ Partial support (needs verification)
- ❓ Unknown (needs research)

## Testing Stack

### Backend Testing
- **pytest** - Main testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **httpx.AsyncClient** - Mock HTTP requests

### Frontend Testing
- **Jest** - Unit testing
- **React Testing Library** - Component testing
- **Playwright** - E2E testing

## Development Tools

### Code Quality
- **black** - Python formatter
- **pylint** - Python linter
- **mypy** - Type checking
- **eslint** - JavaScript/TypeScript linter
- **prettier** - Code formatter

### Version Control
- **Git** - Version control
- **GitHub** - Repository hosting
- **Conventional Commits** - Commit message format

## Legal References

### Documentation Sources
- Lei 14.133/2021 (Planalto.gov.br)
- Decreto 12.807/2025 (DOU)
- TCU Guidelines (licitacoesecontratos.tcu.gov.br)
- PNCP Documentation (gov.br/pncp)

## Architecture Patterns

### Backend Architecture
```
SourceAdapter (ABC)
├── ComprasGovAdapter
├── PortalComprasAdapter
└── LicitarAdapter
    └── normalize() → UnifiedProcurement
        └── modalidade: str (normalized name)
```

### Frontend Architecture
```
ModalidadeFilter (React Component)
├── MODALIDADES: Modalidade[]
│   ├── codigo: number (1-11)
│   ├── nome: string (Lei 14.133 name)
│   ├── descricao: string (Article reference)
│   └── popular: boolean
└── filtrar_por_modalidade(codigos[])
```

### Data Flow
```
User Selection
  → ModalidadeFilter (Frontend)
    → BuscaRequest.modalidades: number[]
      → API /buscar
        → filtrar_por_modalidade()
          → Each SourceAdapter.fetch()
            → normalize(raw_record)
              → UnifiedProcurement.modalidade
                → Client receives filtered results
```

## Modalidade Normalization

### Mapping Strategy
Each source adapter must normalize modalidade names to Lei 14.133 standard names:

```python
MODALIDADE_MAPPING = {
    # Exact matches
    "Pregão Eletrônico": "Pregao Eletronico",
    "Pregão Presencial": "Pregao Presencial",
    "Concorrência": "Concorrencia",
    "Concurso": "Concurso",
    "Leilão": "Leilao",
    "Dispensa de Licitação": "Dispensa de Licitacao",
    "Inexigibilidade": "Inexigibilidade",
    "Diálogo Competitivo": "Dialogo Competitivo",

    # Variations
    "PREGAO ELETRONICO": "Pregao Eletronico",
    "PREGAO PRESENCIAL": "Pregao Presencial",
    "Pregão - Eletrônico": "Pregao Eletronico",
    "Pregão - Presencial": "Pregao Presencial",

    # Legacy (deprecated)
    "Tomada de Preços": "DEPRECATED_TOMADA_PRECOS",
    "Convite": "DEPRECATED_CONVITE",
}
```

## Environment Variables

```bash
# API Endpoints
COMPRAS_GOV_BASE_URL=https://compras.dados.gov.br
PORTAL_COMPRAS_BASE_URL=https://api.portalcompras.gov.br
LICITAR_BASE_URL=https://api.licitar.com

# Timeouts (seconds)
DEFAULT_TIMEOUT=25
HEALTH_CHECK_TIMEOUT=5

# Rate Limits (requests per second)
COMPRAS_GOV_RPS=2.0
PORTAL_COMPRAS_RPS=5.0
LICITAR_RPS=3.0

# Pagination
DEFAULT_PAGE_SIZE=500
MAX_PAGES=100
```

## Performance Targets

### Backend
- **API Response Time:** < 5s for simple queries
- **Source Adapter Timeout:** 25s max
- **Health Check:** < 5s
- **Pagination:** 500 records/page
- **Concurrent Requests:** Rate-limited per source

### Frontend
- **Component Render:** < 100ms
- **Filter Update:** < 50ms
- **Accessibility:** WCAG 2.1 AA compliant

## Compatibility

### Python Version
- **Minimum:** 3.11
- **Recommended:** 3.12+

### Node.js Version
- **Minimum:** 18.x
- **Recommended:** 20.x LTS

### Browser Support
- **Chrome:** Last 2 versions
- **Firefox:** Last 2 versions
- **Safari:** Last 2 versions
- **Edge:** Last 2 versions

## Dependencies

### Backend Critical Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
pydantic = "^2.0.0"
httpx = "^0.24.0"
```

### Frontend Critical Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "next": "^14.0.0",
    "typescript": "^5.0.0"
  }
}
```
