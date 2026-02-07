# Checklist de Configuração OAuth no Supabase

## 🎯 Objetivo

Garantir que o Google OAuth esteja configurado corretamente no Supabase para exibir "SmartLic" na tela de login.

---

## 📋 Checklist de Verificação

### 1. Acessar Supabase Dashboard

**URL:** https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk/auth/providers

**Login:** tiago.sasaki@gmail.com

---

### 2. Verificar Configuração do Google Provider

#### ✅ Configurações Obrigatórias

| Campo | Status | Valor Esperado |
|-------|--------|----------------|
| **Enabled** | [ ] | ✅ Ativado (toggle verde) |
| **Client ID** | [ ] | (valor do Google Cloud Console) |
| **Client Secret** | [ ] | (valor do Google Cloud Console) |
| **Authorized Client IDs** | [ ] | (mesmo Client ID acima) |

#### 📝 Redirect URL (Automático)

O Supabase gera automaticamente a redirect URL:

```
https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback
```

✅ **Essa URL deve estar registrada no Google Cloud Console** em "Authorized redirect URIs"

---

### 3. Verificar Site URL

**Localização:** https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk/auth/url-configuration

| Campo | Valor Correto |
|-------|---------------|
| **Site URL** | `https://smartlic.tech` |
| **Redirect URLs** | `https://smartlic.tech/**` |

> **Importante:** O Site URL deve ser o domínio principal da aplicação, não o domínio do Supabase.

---

### 4. Verificar Email Templates (Opcional)

**Localização:** https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk/auth/templates

Se você usar autenticação por email também, personalize os templates:

- [ ] Confirm signup
- [ ] Invite user
- [ ] Magic Link
- [ ] Change Email Address
- [ ] Reset Password

**Personalização sugerida:**
- Nome da empresa: SmartLic
- From email: noreply@smartlic.tech (se configurado)
- Support email: suporte@smartlic.tech

---

### 5. Verificar Auth Settings

**Localização:** https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk/auth/settings

#### Configurações Recomendadas

| Setting | Valor Recomendado | Descrição |
|---------|-------------------|-----------|
| **Enable email confirmations** | ✅ Habilitado | Requer confirmação de email |
| **Enable email change confirmation** | ✅ Habilitado | Confirmar mudança de email |
| **Secure email change** | ✅ Habilitado | Requer senha para mudar email |
| **JWT expiry limit** | 3600 (1 hora) | Tempo de expiração do token |
| **Refresh token time limit** | 86400 (24 horas) | Tempo para refresh token |
| **Enable manual linking** | ❌ Desabilitado | Evita linking manual |
| **Disable signup** | ❌ Desabilitado | Permitir novos cadastros |

---

### 6. Verificar Policies do Database

**Localização:** https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk/editor

Verificar se as tabelas relacionadas a usuários têm Row Level Security (RLS) configurado:

#### Tabelas Críticas

- [ ] `users` - RLS habilitado
- [ ] `user_plans` - RLS habilitado
- [ ] `subscriptions` - RLS habilitado
- [ ] `searches` - RLS habilitado

#### Policy Exemplo (users)

```sql
-- Usuários podem ver apenas seus próprios dados
CREATE POLICY "Users can view own data"
ON users FOR SELECT
USING (auth.uid() = id);

-- Usuários podem atualizar apenas seus próprios dados
CREATE POLICY "Users can update own data"
ON users FOR UPDATE
USING (auth.uid() = id);
```

---

### 7. Testar Configuração

#### 7.1 Teste Local

```bash
cd frontend
npm run dev
```

1. Acesse: http://localhost:3000/login
2. Clique em "Login com Google"
3. **Verificar se aparece:** "Prosseguir para SmartLic"
4. Completar login
5. Verificar se o usuário é criado no Supabase (tabela `auth.users`)

#### 7.2 Teste em Produção

1. Acesse: https://smartlic.tech/login
2. Clique em "Login com Google"
3. **Verificar se aparece:** "Prosseguir para SmartLic"
4. Completar login
5. Verificar se o usuário é redirecionado corretamente

---

### 8. Troubleshooting

#### ❌ Ainda aparece "fqqyovlzdzimiwfofdjk.supabase.co"

**Causa:** OAuth Consent Screen não configurado no Google Cloud Console

**Solução:**
1. Acessar: https://console.cloud.google.com/apis/credentials/consent
2. Preencher "App name" com "SmartLic"
3. Preencher URLs de privacidade e termos
4. Salvar e aguardar 10 minutos

#### ❌ Erro: "redirect_uri_mismatch"

**Causa:** Redirect URI não registrada no Google Cloud Console

**Solução:**
1. Copiar exatamente: `https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback`
2. Adicionar em "Authorized redirect URIs" no Google Cloud Console
3. Incluir também: `https://smartlic.tech/auth/callback`

#### ❌ Erro: "invalid_client"

**Causa:** Client ID ou Secret incorretos

**Solução:**
1. Verificar no Google Cloud Console: https://console.cloud.google.com/apis/credentials
2. Copiar Client ID e Secret
3. Atualizar no Supabase Dashboard
4. Salvar e testar novamente

#### ❌ Login funciona mas usuário não é salvo

**Causa:** RLS (Row Level Security) muito restritivo

**Solução:**
1. Verificar policies da tabela `auth.users`
2. Adicionar policy para permitir INSERT de novos usuários
3. Verificar se o trigger `on_auth_user_created` está ativo

---

### 9. Comandos Úteis (CLI)

#### Verificar configuração do Supabase

```bash
# Listar projetos
npx supabase projects list

# Ver API keys
npx supabase projects api-keys --project-ref fqqyovlzdzimiwfofdjk

# Inspecionar schema
npx supabase db pull
```

#### Logs do Supabase (Auth)

1. Acessar: https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk/logs/edge-logs
2. Filtrar por: `auth.callback`
3. Verificar erros de OAuth

---

### 10. Próximos Passos Após Configuração

Depois que tudo estiver funcionando:

- [ ] Testar fluxo completo de signup/login
- [ ] Verificar se os planos são atribuídos corretamente (FREE trial)
- [ ] Configurar email transacional (SendGrid/AWS SES) se necessário
- [ ] Adicionar mais providers (Microsoft, LinkedIn) se desejado
- [ ] Configurar MFA (Multi-Factor Authentication) para segurança extra
- [ ] Monitorar logs de autenticação para detectar problemas

---

### 11. Recursos e Documentação

#### Supabase Auth

- **Dashboard:** https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk
- **Docs:** https://supabase.com/docs/guides/auth
- **Google OAuth:** https://supabase.com/docs/guides/auth/social-login/auth-google

#### Google Cloud

- **Console:** https://console.cloud.google.com/
- **OAuth Consent:** https://console.cloud.google.com/apis/credentials/consent
- **Credentials:** https://console.cloud.google.com/apis/credentials

#### SmartLic

- **Produção:** https://smartlic.tech
- **Railway:** https://railway.app/project/bidiq-uniformes
- **GitHub:** https://github.com/tjsasakifln/PNCP-poc

---

### 12. Contatos de Suporte

| Tipo | Contato |
|------|---------|
| **Supabase Support** | support@supabase.com |
| **Google Cloud Support** | https://cloud.google.com/support |
| **SmartLic Admin** | tiago.sasaki@gmail.com |

---

**Última atualização:** 07 de fevereiro de 2026

---

## ✅ Checklist Rápido (Quick Start)

```
[ ] 1. Supabase → Auth → Providers → Google (Enabled ✅)
[ ] 2. Client ID e Secret copiados do Google Cloud Console
[ ] 3. Google Cloud Console → OAuth Consent Screen → App name = "SmartLic"
[ ] 4. Google Cloud Console → Credentials → Authorized redirect URIs
        → https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback
[ ] 5. Supabase → Auth → URL Configuration → Site URL = https://smartlic.tech
[ ] 6. Teste: https://smartlic.tech/login → "Prosseguir para SmartLic" ✅
```

---

Se ainda tiver problemas, compartilhe screenshots ou mensagens de erro!
