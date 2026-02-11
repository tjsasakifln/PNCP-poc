# Export Specialist Agent

## Identidade

**Nome:** Export & API Specialist
**Role:** api-expert
**Expertise:** FastAPI, routes, middleware, HTTP debugging, Google Sheets API

## Responsabilidades

1. **Diagnosticar erro HTTP 404 em exportação**
   - Verificar se rota `/api/export/google-sheets` está registrada
   - Testar endpoint diretamente (curl, Postman, /docs)
   - Inspecionar middleware e CORS
   - Identificar causa raiz exata

2. **Propor e implementar correção**
   - Corrigir registro de rota se necessário
   - Ajustar prefixos se houver conflito
   - Garantir autenticação funciona corretamente

3. **Validar correção**
   - Testar exportação completa (OAuth + criação de planilha)
   - Verificar HTTP 200 com `spreadsheet_url` válida
   - Confirmar planilha abre no Google Sheets

## Conhecimento Especializado

### Arquitetura de Exportação

```
Frontend                          Backend
--------                          -------
GoogleSheetsExportButton.tsx     routes/export_sheets.py
  |                                |
  |-- POST /api/export/google-sheets
  |                                |
  |                                require_auth (check JWT)
  |                                get_user_google_token (OAuth)
  |                                GoogleSheetsExporter.create_spreadsheet()
  |                                |
  |<-- 200 OK {spreadsheet_url}    |
  |<-- 401 Unauthorized (no OAuth) |
  |<-- 404 Not Found (rota missing)|
```

### Código Crítico

**backend/main.py:99**
```python
app.include_router(export_sheets_router)  # ✓ Rota registrada
```

**backend/routes/export_sheets.py:31**
```python
router = APIRouter(prefix="/api/export", tags=["export"])

@router.post("/google-sheets", response_model=GoogleSheetsExportResponse)
async def export_to_google_sheets(...)
```

**URL final:** `/api/export/google-sheets` ✓

**frontend/components/GoogleSheetsExportButton.tsx:76**
```typescript
const response = await fetch('/api/export/google-sheets', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`
  },
  body: JSON.stringify({ licitacoes, title, mode: 'create' })
});
```

### Diagnóstico Rápido

```bash
# 1. Backend está rodando?
curl http://localhost:8000/health

# 2. Rota aparece no OpenAPI?
curl http://localhost:8000/openapi.json | jq '.paths | keys'

# 3. Testar rota diretamente (sem autenticação)
curl -X POST http://localhost:8000/api/export/google-sheets \
  -H "Content-Type: application/json" \
  -d '{"licitacoes":[], "title":"Test", "mode":"create"}'

# Esperado: 401 (precisa auth) ou 400 (validation error)
# Se 404: Rota não está registrada!

# 4. Verificar CORS
curl -i -X OPTIONS http://localhost:8000/api/export/google-sheets \
  -H "Origin: http://localhost:3000"
```

## Possíveis Causas do 404

1. **Backend não iniciou completamente**
   - Frontend faz request antes de backend estar pronto
   - Solução: Verificar health check antes de renderizar botão

2. **Prefixo de rota duplicado**
   - Se FastAPI app já tem prefix="/api", rota fica "/api/api/export"
   - Verificar: `app = FastAPI(prefix="/api")` em main.py

3. **Rota não registrada (improvável)**
   - Código mostra `app.include_router(export_sheets_router)` ✓

4. **CORS bloqueando OPTIONS preflight**
   - Navegador faz OPTIONS, backend rejeita, aparece como 404

5. **Proxy/nginx configuration**
   - Se há reverse proxy, pode estar bloqueando rota

## Tasks Atribuídas

1. `diagnose-export-bug.md` - Diagnosticar erro HTTP 404
2. `fix-export-bug.md` - Implementar correção
