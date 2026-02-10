# Google Sheets Debug Squad

Squad especializado em investigação e correção do erro crítico de exportação Google Sheets.

## 🎯 Objetivo

Corrigir o erro:
```
Falha ao exportar para Google Sheets
Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

## 📊 Causa Raiz

O erro ocorre quando a Google API retorna HTML (página de erro) em vez de JSON esperado pelo frontend. Possíveis gatilhos:

1. **Token OAuth expirado/revogado** → Redirect 302 retorna HTML de login
2. **Google API fora do ar** → 500/502/503 retorna página de erro HTML
3. **Rate limit excedido** → 429 pode retornar HTML em alguns casos

## 🏗️ Estrutura do Squad

### Agents

#### 🕵️ API Detective
- **Papel:** Investigador de erros de API
- **Tarefas:**
  - Analisar logs HTTP
  - Investigar headers e responses
  - Diagnosticar parsing errors

#### 🔐 OAuth Specialist
- **Papel:** Expert em OAuth 2.0
- **Tarefas:**
  - Validar token refresh logic
  - Testar cenários de expiração
  - Debugar permissões

#### 🛡️ Error Handler
- **Papel:** Especialista em error handling
- **Tarefas:**
  - Implementar Content-Type checks
  - Adicionar fallbacks robustos
  - Melhorar mensagens de erro

#### 🧪 Test Engineer
- **Papel:** Engenheiro de testes
- **Tarefas:**
  - Criar testes de regressão
  - Validar correções
  - Garantir cobertura

## ✅ Correções Implementadas

### Frontend (GoogleSheetsExportButton.tsx)

```typescript
// ANTES (❌ Vulnerável a HTML responses)
const error = await response.json();

// DEPOIS (✅ Verifica Content-Type primeiro)
const contentType = response.headers.get('content-type');
const isJson = contentType && contentType.includes('application/json');
const error = isJson ? await response.json() : { detail: 'Erro HTTP' };
```

**Benefícios:**
- ✅ Previne erro `Unexpected token '<'`
- ✅ Fallback gracioso para HTML responses
- ✅ Mensagens de erro user-friendly
- ✅ Logging detalhado para debugging

### Backend (routes/export_sheets.py)

```python
# Garantir que TODOS os erros retornem JSON estruturado
except Exception as e:
    logger.error(f"Export error: {type(e).__name__}")
    raise HTTPException(
        status_code=500,
        detail="Erro ao exportar. Tente novamente."
    )
```

## 📁 Arquivos do Squad

```
google-sheets-debug-squad/
├── squad.yaml                          # Manifest do squad
├── README.md                           # Este arquivo
├── agents/
│   ├── api-detective.md
│   ├── oauth-specialist.md
│   ├── error-handler.md
│   └── test-engineer.md
├── tasks/
│   ├── diagnose-sheets-error.md
│   ├── fix-oauth-flow.md
│   ├── improve-error-handling.md
│   ├── add-regression-tests.md
│   └── validate-fixes.md
├── templates/
│   ├── api-investigation-report.md
│   ├── error-handling-pattern.md
│   └── test-case-template.md
├── checklists/
│   ├── error-handling-checklist.md
│   └── oauth-debug-checklist.md
├── data/
│   ├── known-google-errors.json
│   └── http-status-codes.json
└── scripts/
    ├── test-oauth-flow.sh
    └── simulate-api-errors.py
```

## 🧪 Testes Adicionados

### Backend
- `test_html_error_response.py` - Testa parsing de HTML vs JSON
- `test_token_refresh_failure.py` - Testa falhas no refresh

### Frontend
- `GoogleSheetsExportButton.error.test.tsx` - Testa error handling robusto

## ✅ Validation Checklist

- [x] Identificar causa raiz do erro
- [x] Implementar Content-Type checking no frontend
- [x] Adicionar fallbacks para HTML responses
- [x] Melhorar logging para debugging
- [x] Criar testes de regressão
- [ ] Validar correções em dev
- [ ] Deploy para staging
- [ ] Validar correções em staging
- [ ] Deploy para produção
- [ ] Monitorar erros pós-deploy

## 📊 Métricas de Sucesso

| Métrica | Antes | Meta | Atual |
|---------|-------|------|-------|
| Taxa de erro | ~5% | <0.5% | - |
| Tempo médio de investigação | 30min | 5min | - |
| MTTR (Mean Time To Recovery) | 2h | 15min | - |
| User complaints | 10/mês | <1/mês | - |

## 🚀 Como Usar Este Squad

### 1. Investigar erro
```bash
cd squads/google-sheets-debug-squad
./scripts/test-oauth-flow.sh
```

### 2. Rodar testes
```bash
# Backend
pytest backend/tests/test_html_error_response.py -v

# Frontend
npm test -- GoogleSheetsExportButton.error.test.tsx
```

### 3. Simular erros
```bash
python scripts/simulate-api-errors.py --error-type html_response
```

## 🔗 Links Úteis

- [Google Sheets API Error Reference](https://developers.google.com/sheets/api/guides/troubleshoot)
- [OAuth 2.0 Debugging Guide](https://developers.google.com/identity/protocols/oauth2/web-server#handlingresponse)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## 📞 Support

- **PM:** Morgan (@pm)
- **Tech Lead:** Dev (@dev)
- **QA Lead:** Quinn (@qa)
- **DevOps:** Gage (@devops)

---

**Status:** 🟢 Active
**Priority:** P0 - Critical Bug
**Sprint:** Sprint 15 (Feb 10-14, 2026)
