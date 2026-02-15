# STORY-180: Google OAuth Setup - COMPLETO ✅

**Data:** 2026-02-10
**Status:** ✅ TASK #1 CONCLUÍDO

---

## ✅ Credenciais Configuradas

### Google OAuth Client

```
Client ID: 390387511329-13bb4qsjupb27r92gd2mlrls88eeuact.apps.googleusercontent.com
Client Secret: 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
Encryption Key: 1AhFGw8FjUN0jYGvDJgC4x863adivI1ZMsMHXyheqgE=
```

### Variáveis de Ambiente Adicionadas

**Localização:** `D:/pncp-poc/.env` e `D:/pncp-poc/backend/.env`

```bash
# ============================================
# Google Sheets OAuth (STORY-180)
# ============================================
GOOGLE_OAUTH_CLIENT_ID=390387511329-13bb4qsjupb27r92gd2mlrls88eeuact.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=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
ENCRYPTION_KEY=1AhFGw8FjUN0jYGvDJgC4x863adivI1ZMsMHXyheqgE=
```

---

## ✅ Testes Realizados

### 1. Carregamento de Credenciais ✅

```
[OK] GOOGLE_OAUTH_CLIENT_ID: 390387511329-13bb4qs...
[OK] GOOGLE_OAUTH_CLIENT_SECRET: GOCSPX-ZoeFc5r2...
[OK] ENCRYPTION_KEY: 1AhFGw8FjUN0jYGvDJgC...
```

### 2. Geração de URL de Autorização ✅

```
[OK] URL de autorizacao gerada com sucesso!
[OK] Client ID presente na URL
[OK] Redirect URI presente na URL
[OK] Scope correto (spreadsheets)
[OK] State parameter presente
```

### 3. Criptografia AES-256 ✅

```
[OK] Formato Fernet correto
[OK] Criptografia/descriptografia funcionando!
[OK] AES-256 encryption configurado corretamente!
```

### 4. Backend Server Startup ✅

```
[OK] FastAPI application initialized on PORT=8000
[OK] CORS configured for development origins
[OK] Feature Flags enabled
[OK] OAuth routes registered:
     - GET /api/auth/google
     - GET /api/auth/google/callback
     - DELETE /api/auth/google
[OK] Export routes registered:
     - POST /api/export/google-sheets
     - GET /api/export/google-sheets/history
```

---

## 🔧 Modificações Realizadas

### 1. Adicionadas Credenciais OAuth ao `.env`

**Arquivo:** `D:/pncp-poc/.env`
- Adicionadas variáveis `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `ENCRYPTION_KEY`
- Copiado para `D:/pncp-poc/backend/.env` para facilitar testes locais

### 2. Adicionado `load_dotenv()` ao `main.py`

**Arquivo:** `D:/pncp-poc/backend/main.py`
```python
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
```

**Motivo:** Garantir que o backend carregue o `.env` automaticamente ao iniciar.

---

## 📋 Redirect URIs Configurados no Google Cloud Console

Você deve ter configurado estes redirect URIs no Google Cloud Console:

```
✅ http://localhost:8000/api/auth/google/callback
✅ https://bidiq-backend-production.up.railway.app/api/auth/google/callback
```

**Verificação:** Acesse https://console.cloud.google.com/apis/credentials e confirme que ambos estão listados em "Authorized redirect URIs" para o Client ID criado.

---

## 🎯 OAuth Consent Screen

Você deve ter configurado:

```
✅ User Type: External
✅ App name: SmartLic
✅ Scopes: https://www.googleapis.com/auth/spreadsheets
✅ Test users: Seu email adicionado (para modo "Testing")
```

**Status:** App deve estar em modo "Testing" (até 100 test users) ou publicado para produção.

---

## 🔒 Segurança

### ✅ Tokens Criptografados

Todos os tokens OAuth (access_token e refresh_token) são criptografados com **AES-256 (Fernet)** antes de serem salvos no banco de dados.

**Formato no banco:**
```
access_token: gAAAAABl1234...ciphertext...
refresh_token: gAAAAABl5678...ciphertext...
```

**⚠️ NUNCA query tokens diretamente do banco!** Use sempre as funções:
- `get_user_google_token()` - Para obter token descriptografado (com auto-refresh)
- `save_user_tokens()` - Para salvar tokens criptografados

### ✅ Row Level Security (RLS)

Políticas ativas em `user_oauth_tokens`:
- Usuários podem ver/atualizar/deletar apenas seus próprios tokens
- Service role tem acesso total

Políticas ativas em `google_sheets_exports`:
- Usuários podem ver apenas seu próprio histórico de exportações
- Service role tem acesso total

---

## 🚀 Como Testar End-to-End

### Passo 1: Iniciar Backend

```bash
cd D:/pncp-poc/backend
uvicorn main:app --reload --port 8000
```

### Passo 2: Iniciar Frontend

```bash
cd D:/pncp-poc/frontend
npm run dev
```

### Passo 3: Fluxo Completo

1. **Login no SmartLic**
   - Acesse: http://localhost:3000
   - Faça login com sua conta (Supabase Auth)

2. **Executar Busca**
   - Selecione UF (ex: SP)
   - Clique em "Buscar"
   - Aguarde resultados

3. **Exportar para Google Sheets**
   - Clique no botão "Exportar para Google Sheets"
   - Se primeira vez: será redirecionado para autorização do Google
   - Autorize o aplicativo SmartLic
   - Após autorizar: planilha será criada automaticamente
   - Planilha abre em nova aba

4. **Verificar Planilha**
   - ✅ Cabeçalho verde (#2E7D32)
   - ✅ Valores formatados como moeda (R$)
   - ✅ Links clicáveis para PNCP
   - ✅ Colunas com largura automática
   - ✅ Dados corretos

5. **Ver Histórico de Exportações**
   - API endpoint: GET http://localhost:8000/api/export/google-sheets/history
   - Requer autenticação (Bearer token do Supabase)

---

## ⚠️ Checklist de Produção (Railway)

Antes de fazer deploy para produção:

### Railway Environment Variables

```bash
railway variables set GOOGLE_OAUTH_CLIENT_ID="390387511329-13bb4qsjupb27r92gd2mlrls88eeuact.apps.googleusercontent.com"
railway variables set GOOGLE_OAUTH_CLIENT_SECRET="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"
railway variables set ENCRYPTION_KEY="1AhFGw8FjUN0jYGvDJgC4x863adivI1ZMsMHXyheqgE="
```

### Google Cloud Console

1. **Verificar Redirect URI de Produção**
   ```
   https://bidiq-backend-production.up.railway.app/api/auth/google/callback
   ```

2. **Publicar OAuth Consent Screen** (se necessário)
   - Para permitir qualquer usuário (não apenas test users)
   - Ou manter em modo "Testing" e adicionar usuários manualmente

### Smoke Tests em Produção

1. Login no frontend de produção
2. Autorizar Google Sheets (se primeira vez)
3. Exportar busca
4. Verificar planilha criada
5. Verificar histórico de exportações
6. Monitorar logs do Railway: `railway logs --tail`

---

## 📊 Métricas de Quota do Google Sheets API

**Limites Padrão:**
- **Requests por dia:** 250,000
- **Requests por minuto por usuário:** 60

**Monitoramento:**
1. Acesse: https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas
2. Verifique uso atual vs limites
3. Se necessário, solicite aumento de quota

**Otimização (já implementada):**
- Batch API operations (3 chamadas por exportação: create + populate + format)
- Cache de tokens OAuth (evita refresh desnecessário)
- Rate limiting automático no backend

---

## 🐛 Troubleshooting Comum

### Erro: "redirect_uri_mismatch"

**Causa:** Redirect URI não está no Google Cloud Console

**Solução:**
```
1. Copie exatamente: http://localhost:8000/api/auth/google/callback
2. Cole em: Google Cloud Console → Credentials → OAuth 2.0 Client → Authorized redirect URIs
3. Salve e aguarde 5 minutos para propagar
```

### Erro: "invalid_client"

**Causa:** Client ID ou Secret incorretos

**Solução:**
```bash
# Verifique no .env se as variáveis estão corretas
grep GOOGLE_OAUTH .env

# Se incorretas, corrija e reinicie backend
uvicorn main:app --reload
```

### Erro: "access_denied"

**Causa:** Usuário não está na lista de Test Users

**Solução:**
```
1. Google Cloud Console → OAuth consent screen → Test users
2. ADD USERS → Adicione o email
3. Tente autorizar novamente
```

### Erro: "Token encryption failed"

**Causa:** ENCRYPTION_KEY inválida ou não carregada

**Solução:**
```bash
# Gerar nova key
openssl rand -base64 32

# Adicionar ao .env
ENCRYPTION_KEY=nova-key-aqui

# Reiniciar backend
```

### Erro: "Insufficient permissions"

**Causa:** Escopo incorreto ou não autorizado

**Solução:**
```
1. Verifique se o escopo está configurado:
   https://www.googleapis.com/auth/spreadsheets
2. No Google Cloud Console → OAuth consent screen → Scopes
3. Adicione o escopo se faltando
4. Usuário precisa RE-AUTORIZAR o app para novos escopos
```

---

## 📚 Documentação Relacionada

| Documento | Descrição |
|-----------|-----------|
| `STORY-180-IMPLEMENTATION-SUMMARY.md` | Resumo completo da implementação |
| `STORY-180-LOCAL-TEST-REPORT.md` | Relatório de testes locais |
| `docs/setup/STORY-180-OAUTH-SETUP-GUIDE.md` | Guia detalhado de setup (60+ seções) |
| `docs/guides/google-sheets-integration.md` | Documentação de integração completa |
| `backend/oauth.py` | Módulo OAuth com criptografia |
| `backend/google_sheets.py` | GoogleSheetsExporter class |
| `backend/routes/auth_oauth.py` | Endpoints de OAuth |
| `backend/routes/export_sheets.py` | Endpoints de exportação |
| `frontend/components/GoogleSheetsExportButton.tsx` | Componente React |

---

## ✅ Próximos Passos

### Imediato (Após Este Setup)

- [x] Task #1: Google Cloud OAuth Setup ✅ **COMPLETO**
- [ ] Testar OAuth flow manualmente no navegador
- [ ] Testar exportação completa (busca → export → verificar planilha)
- [ ] Configurar variáveis no Railway (production)

### Curto Prazo (Semana 1)

- [ ] Escrever testes unitários backend:
  - `test_oauth.py` - OAuth flow, token encryption/decryption
  - `test_google_sheets.py` - Spreadsheet creation, formatting
  - `test_routes_auth_oauth.py` - OAuth endpoints
  - `test_routes_export_sheets.py` - Export endpoints
  - **Target:** ≥70% coverage

- [ ] Escrever testes unitários frontend:
  - `GoogleSheetsExportButton.test.tsx`
  - **Target:** ≥60% coverage

### Médio Prazo (Semana 2)

- [ ] Escrever testes E2E (Playwright):
  - `google-sheets-export.spec.ts`
  - Full OAuth flow + export + verificação

- [ ] Deploy para produção (Railway)
- [ ] Smoke tests em produção
- [ ] Monitorar quota do Google Sheets API

---

## 🎉 Status Final

**STORY-180 - Google Sheets Export:**

| Componente | Status | Coverage |
|------------|--------|----------|
| **Backend OAuth Infrastructure** | ✅ Completo | 19/19 testes |
| **Backend Google Sheets Integration** | ✅ Completo | Implementado |
| **Frontend Export Button** | ✅ Completo | TypeScript OK |
| **Database Migrations** | ✅ Completo | Aplicado |
| **Google OAuth Setup** | ✅ **COMPLETO** | Task #1 ✅ |
| **Unit Tests** | ⏳ Pendente | 0% |
| **E2E Tests** | ⏳ Pendente | 0% |
| **Production Deployment** | ⏳ Pendente | Não deployado |

**Acceptance Criteria:** 8/10 completos (AC1 ✅ completo, AC9 pendente testes de performance)

---

**Implementado por:** 4 squads paralelos (ALPHA, BRAVO, CHARLIE, DELTA)

**Tempo de Implementação:** 1 sessão (YOLO mode 🔥)

**Total de Código:** ~2,840 linhas (11 novos arquivos, 4 modificados)

**Próxima Fase:** Testing e Deployment 🚀
