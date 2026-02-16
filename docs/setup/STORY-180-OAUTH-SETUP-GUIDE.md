# STORY-180: Google OAuth Setup - Guia Rápido

## Contexto

Vocês já usam **Supabase Auth** para login via Google, mas STORY-180 (Google Sheets Export) precisa de **credenciais OAuth separadas** porque:

- **Supabase Auth:** Login do usuário (escopos: `email`, `profile`)
- **STORY-180:** Acesso à API do Google Sheets (escopos: `spreadsheets`, `drive.file`)

As credenciais são **independentes** e podem coexistir no mesmo projeto Google Cloud.

---

## Passo 1: Acessar Google Cloud Console

1. Vá para: https://console.cloud.google.com
2. Selecione o projeto existente (provavelmente o mesmo usado pelo Supabase Auth)
3. ✅ Confirme que as seguintes APIs estão ativadas:
   - Google Sheets API
   - Google Drive API (opcional, mas útil)

---

## Passo 2: Criar Credenciais OAuth 2.0 (Separadas do Supabase)

### 2.1 Navegar para Credentials

```
Google Cloud Console → APIs & Services → Credentials
```

### 2.2 Criar OAuth Client ID

1. Clique em **"+ CREATE CREDENTIALS"** → **OAuth client ID**

2. **Application type:** Web application

3. **Name:** `SmartLic - Google Sheets Export` (para diferenciar do Supabase Auth)

4. **Authorized JavaScript origins:**
   ```
   http://localhost:8000
   https://bidiq-backend-production.up.railway.app
   ```

5. **Authorized redirect URIs:**
   ```
   http://localhost:8000/api/auth/google/callback
   https://bidiq-backend-production.up.railway.app/api/auth/google/callback
   ```

6. Clique em **CREATE**

### 2.3 Copiar Credenciais

Você receberá:
```
Client ID: 123456789-abc.apps.googleusercontent.com
Client Secret: GOCSPX-xyz123abc456
```

**⚠️ IMPORTANTE:** NÃO confundir com as credenciais do Supabase Auth!

---

## Passo 3: Configurar Variáveis de Ambiente

### 3.1 Backend Local (D:/pncp-poc/.env)

Adicione as seguintes linhas ao arquivo `.env`:

```bash
# ============================================
# Google Sheets OAuth (STORY-180)
# ============================================
# Credenciais SEPARADAS do Supabase Auth
# Usadas exclusivamente para Google Sheets API

GOOGLE_OAUTH_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xyz123abc456

# Encryption key para tokens OAuth (AES-256)
# Gerar com: openssl rand -base64 32
ENCRYPTION_KEY=
```

### 3.2 Gerar ENCRYPTION_KEY

Execute no terminal:

```bash
# Windows (PowerShell)
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))

# Windows (Git Bash / WSL)
openssl rand -base64 32

# Linux / macOS
openssl rand -base64 32
```

Copie o output e cole em `ENCRYPTION_KEY=` no `.env`.

### 3.3 Exemplo Completo

Seu `.env` deve ficar assim:

```bash
# Existing Supabase credentials
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
ADMIN_USER_IDS=your-admin-user-uuid
OPENAI_API_KEY=
SUPABASE_ACCESS_TOKEN=your-supabase-access-token

# Resend SMTP for Supabase Auth emails
RESEND_API_KEY=your-resend-api-key

# ============================================
# Google Sheets OAuth (STORY-180)
# ============================================
GOOGLE_OAUTH_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xyz123abc456
ENCRYPTION_KEY=your-base64-encoded-key-here
```

---

## Passo 4: Configurar Railway (Production)

### 4.1 Acessar Railway Dashboard

```bash
railway status  # Verificar projeto conectado
railway variables  # Listar variáveis existentes
```

### 4.2 Adicionar Variáveis

```bash
railway variables set GOOGLE_OAUTH_CLIENT_ID="123456789-abc.apps.googleusercontent.com"
railway variables set GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-xyz123abc456"
railway variables set ENCRYPTION_KEY="your-base64-key"
```

Ou via Railway Dashboard:
```
Railway → Project → Variables → New Variable
```

---

## Passo 5: Verificar OAuth Consent Screen

### 5.1 Configurar Tela de Consentimento

```
Google Cloud Console → APIs & Services → OAuth consent screen
```

1. **User Type:** External (para permitir qualquer usuário do SmartLic)

2. **App Information:**
   - App name: `SmartLic`
   - User support email: `seu-email@gmail.com`
   - Developer contact: `seu-email@gmail.com`

3. **Scopes:**
   - Adicione: `https://www.googleapis.com/auth/spreadsheets`
   - Adicione: `https://www.googleapis.com/auth/drive.file` (opcional)

4. **Test users (apenas para modo "Testing"):**
   - Adicione emails dos usuários que podem testar
   - ⚠️ Em produção, publique o app para permitir qualquer usuário

### 5.2 Publicar App (Opcional)

Se quiser que qualquer usuário possa usar:
```
OAuth consent screen → PUBLISH APP → Submit for verification
```

**Nota:** Para testes internos, modo "Testing" é suficiente (limite de 100 test users).

---

## Passo 6: Testar Localmente

### 6.1 Iniciar Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6.2 Testar OAuth Flow

1. Acesse: http://localhost:8000/api/auth/google
2. Você deve ser redirecionado para Google OAuth consent screen
3. Autorize o aplicativo
4. Deve retornar para `http://localhost:8000/api/auth/google/callback`
5. Se bem-sucedido, verá mensagem: "Google Sheets conectado com sucesso!"

### 6.3 Testar Export

1. Faça login no SmartLic frontend: http://localhost:3000
2. Execute uma busca
3. Clique no botão "Exportar para Google Sheets"
4. Spreadsheet deve abrir em nova aba

---

## Passo 7: Verificar Tokens Criptografados

### 7.1 Query no Supabase

```sql
SELECT
    id,
    user_id,
    provider,
    expires_at,
    scope,
    created_at
FROM user_oauth_tokens
WHERE provider = 'google';
```

**⚠️ NÃO query `access_token` ou `refresh_token` diretamente** - estão criptografados!

### 7.2 Verificar Criptografia

Os tokens devem parecer assim (exemplo):
```
access_token: gAAAAABl1234...ciphertext...
refresh_token: gAAAAABl5678...ciphertext...
```

Se estiverem em plaintext (ex: `ya29.a0...`), a criptografia **não está funcionando**!

---

## Troubleshooting

### Erro: "redirect_uri_mismatch"

**Causa:** Redirect URI no código ≠ Redirect URI no Google Cloud Console

**Solução:**
1. Verifique `oauth.py` linha ~90:
   ```python
   redirect_uri = "http://localhost:8000/api/auth/google/callback"
   ```
2. Copie exatamente esse URI e adicione em:
   ```
   Google Cloud Console → Credentials → OAuth 2.0 Client → Authorized redirect URIs
   ```

### Erro: "invalid_client"

**Causa:** Client ID ou Client Secret incorretos

**Solução:**
1. Copie novamente as credenciais do Google Cloud Console
2. Verifique se não há espaços extras no `.env`
3. Reinicie o backend: `uvicorn main:app --reload`

### Erro: "access_denied"

**Causa:** Usuário não está na lista de Test Users (app em modo "Testing")

**Solução:**
1. Adicione o email em:
   ```
   OAuth consent screen → Test users → ADD USERS
   ```
2. Ou publique o app para produção

### Erro: "Token encryption failed"

**Causa:** ENCRYPTION_KEY não está configurada ou é inválida

**Solução:**
1. Gerar nova key: `openssl rand -base64 32`
2. Adicionar ao `.env`: `ENCRYPTION_KEY=nova-key`
3. Reiniciar backend

### Erro: "insufficient permissions"

**Causa:** App não tem escopos corretos configurados

**Solução:**
1. Verifique `oauth.py` linha ~85:
   ```python
   scope = "https://www.googleapis.com/auth/spreadsheets"
   ```
2. Adicione esse escopo em:
   ```
   OAuth consent screen → Scopes → ADD OR REMOVE SCOPES
   ```

---

## Checklist Final

- [ ] Google Sheets API ativada no Google Cloud Console
- [ ] Google Drive API ativada (opcional)
- [ ] OAuth 2.0 Client ID criado (tipo: Web application)
- [ ] Redirect URIs configurados corretamente (local + production)
- [ ] `GOOGLE_OAUTH_CLIENT_ID` adicionado ao `.env`
- [ ] `GOOGLE_OAUTH_CLIENT_SECRET` adicionado ao `.env`
- [ ] `ENCRYPTION_KEY` gerado e adicionado ao `.env`
- [ ] OAuth consent screen configurado com escopos corretos
- [ ] Test users adicionados (se app em modo "Testing")
- [ ] Backend reiniciado após mudanças no `.env`
- [ ] OAuth flow testado localmente (http://localhost:8000/api/auth/google)
- [ ] Export testado localmente (frontend → botão "Exportar")
- [ ] Variáveis adicionadas ao Railway (production)
- [ ] Redirect URIs de produção configurados no Google Cloud Console

---

## Comandos Úteis

```bash
# Gerar encryption key
openssl rand -base64 32

# Testar backend local
cd backend && uvicorn main:app --reload --port 8000

# Verificar variáveis Railway
railway variables

# Adicionar variável Railway
railway variables set KEY="value"

# Ver logs Railway
railway logs --tail

# Deploy Railway (após config)
railway up
```

---

## Próximos Passos Após Setup

1. ✅ Task #1: Google Cloud OAuth Setup (COMPLETO)
2. ⏳ Escrever testes unitários (backend + frontend)
3. ⏳ Escrever testes E2E (Playwright)
4. ⏳ Deploy para produção (Railway)
5. ⏳ Smoke tests em produção
6. ⏳ Monitorar quota do Google Sheets API

---

**Documentação Completa:** `docs/guides/google-sheets-integration.md` (60+ páginas)

**Implementação:** `STORY-180-IMPLEMENTATION-SUMMARY.md`

**Testes:** `STORY-180-LOCAL-TEST-REPORT.md`
