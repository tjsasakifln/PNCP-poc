# Task: Diagnosticar Erro HTTP 404 em Exportação Google Sheets

**Assigned to:** export-specialist
**Priority:** P0
**Estimated Time:** 15 min
**Elicit:** false

## Objetivo

Identificar causa raiz exata do erro "Falha ao exportar para Google Sheets - Erro HTTP 404" e confirmar se rota está acessível.

## Contexto

**Erro relatado:** "Falha ao exportar para Google Sheets - Erro HTTP 404"

**Código verificado:**
- ✅ Rota registrada: `backend/main.py:99` - `app.include_router(export_sheets_router)`
- ✅ Prefixo correto: `backend/routes/export_sheets.py:31` - `router = APIRouter(prefix="/api/export")`
- ✅ Endpoint definido: `@router.post("/google-sheets")`
- ✅ Frontend chama URL correta: `fetch('/api/export/google-sheets')`

**Status:** Configuração parece correta no código. Precisa verificar runtime.

## Steps

### 1. Verificar Backend Está Rodando

```bash
# Testar health check
curl http://localhost:8000/health
# Esperado: 200 OK {"status": "healthy"}

# Se falhar: Backend não está rodando!
# Iniciar backend:
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Verificar Rota no OpenAPI Spec

```bash
# Listar todas as rotas registradas
curl http://localhost:8000/openapi.json | jq '.paths | keys' | grep export

# Esperado: "/api/export/google-sheets"

# Se NÃO aparecer: Rota não foi registrada no runtime!
```

### 3. Testar Rota Diretamente

```bash
# Teste 1: POST sem autenticação (deve retornar 401, não 404)
curl -i -X POST http://localhost:8000/api/export/google-sheets \
  -H "Content-Type: application/json" \
  -d '{"licitacoes": [], "title": "Test", "mode": "create"}'

# Esperado: HTTP 401 Unauthorized (require_auth bloqueando)
# Se 404: Rota não existe!

# Teste 2: OPTIONS preflight (CORS)
curl -i -X OPTIONS http://localhost:8000/api/export/google-sheets \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"

# Esperado: HTTP 200 com headers CORS
# Se 404: CORS middleware pode estar bloqueando
```

### 4. Inspecionar Network Tab no Navegador

```
1. Abrir DevTools (F12) → Network tab
2. Tentar exportar pelo botão na UI
3. Localizar request para /api/export/google-sheets
4. Verificar:
   - Status code (404?)
   - Request URL (está correto?)
   - Request Headers (Authorization presente?)
   - Response body (mensagem de erro?)
```

### 5. Verificar Logs do Backend

```bash
# Ver logs do backend durante a tentativa de exportação
tail -f backend/logs/app.log

# Procurar por:
# - "POST /api/export/google-sheets" (request chegou?)
# - Erros de autenticação
# - Stack traces
```

### 6. Verificar Prefixo Duplicado

```python
# Verificar se FastAPI app tem prefix global
# backend/main.py

app = FastAPI(
    title="SmartLic API",
    # prefix="/api"  ← Se tiver isso, rota fica /api/api/export!
)

# Se tiver prefix="/api", remover e adicionar manualmente em cada router
```

### 7. Testar via /docs (Swagger UI)

```
1. Abrir http://localhost:8000/docs
2. Procurar endpoint "POST /api/export/google-sheets"
3. Expandir e clicar "Try it out"
4. Preencher payload mínimo:
   {
     "licitacoes": [],
     "title": "Test",
     "mode": "create"
   }
5. Execute

Esperado: 401 (sem token) ou 422 (validation error)
Se 404: Endpoint não está registrado!
```

## Acceptance Criteria

- [ ] Causa raiz exata identificada
- [ ] Bug reproduzido (404 confirmado)
- [ ] Evidências coletadas:
  - Screenshot do Network tab mostrando 404
  - Output do curl mostrando 404
  - Screenshot do /docs mostrando se rota existe ou não
  - Logs do backend mostrando se request chegou
- [ ] Solução técnica proposta
- [ ] Relatório de diagnóstico preenchido

## Expected Findings (Hipóteses)

**Hipótese 1: Backend não iniciado completamente**
- Evidência: `curl http://localhost:8000/health` falha
- Solução: Garantir backend está rodando antes de frontend fazer request

**Hipótese 2: Prefixo duplicado (/api/api/export)**
- Evidência: OpenAPI spec mostra `/api/api/export/google-sheets`
- Solução: Remover prefix duplicado

**Hipótese 3: CORS bloqueando OPTIONS**
- Evidência: OPTIONS request retorna 404 ou sem headers CORS
- Solução: Adicionar `/api/export/google-sheets` ao CORS whitelist

**Hipótese 4: Proxy/nginx bloqueando rota**
- Evidência: curl direto para :8000 funciona, mas via :3000 dá 404
- Solução: Configurar proxy no next.config.js

**Hipótese 5: Frontend chamando URL errada**
- Evidência: Network tab mostra URL diferente de `/api/export/google-sheets`
- Solução: Corrigir URL no GoogleSheetsExportButton.tsx

## Diagnostic Commands Checklist

```bash
# ✅ 1. Backend health
curl http://localhost:8000/health

# ✅ 2. Rota no OpenAPI
curl http://localhost:8000/openapi.json | jq '.paths | keys'

# ✅ 3. POST direto (deve ser 401, não 404)
curl -i -X POST http://localhost:8000/api/export/google-sheets \
  -H "Content-Type: application/json" \
  -d '{"licitacoes":[],"title":"Test","mode":"create"}'

# ✅ 4. OPTIONS preflight
curl -i -X OPTIONS http://localhost:8000/api/export/google-sheets

# ✅ 5. Logs do backend
tail -f backend/logs/app.log | grep "export"

# ✅ 6. Testar via Swagger
open http://localhost:8000/docs
```

## Deliverables

1. **Bug Diagnosis Report** (`docs/bug-reports/export-404-bug.md`)
   - Root cause
   - Evidence (screenshots, curl outputs)
   - Proposed solution

2. **Curl test results** (saved to file)
   ```bash
   bash tools/test-export-endpoint.sh > logs/export-endpoint-test.log
   ```

3. **Network tab export** (HAR file ou screenshot)

## Next Task

Após completar diagnóstico, executar: `fix-export-bug.md`
