# Configuração do Google OAuth - SmartLic

## URLs para Google Cloud Console

### 1. OAuth Consent Screen

Acesse: https://console.cloud.google.com/apis/credentials/consent

### Configuração do App Name

| Campo | Valor |
|-------|-------|
| **App name** | `SmartLic` |
| **User support email** | `tiago.sasaki@gmail.com` |
| **Application homepage** | `https://smartlic.tech` |
| **Application privacy policy** | `https://smartlic.tech/privacidade` |
| **Application terms of service** | `https://smartlic.tech/termos` |

### Authorized Domains

Adicione os seguintes domínios autorizados:

1. `smartlic.tech`
2. `supabase.co`
3. `fqqyovlzdzimiwfofdjk.supabase.co` (projeto Supabase)

### Logo do Aplicativo (Opcional)

- Tamanho recomendado: 120x120px
- Formato: PNG ou JPG
- Localização: `frontend/app/icon.png`

---

## 2. Configuração das Credenciais OAuth

Acesse: https://console.cloud.google.com/apis/credentials

### Authorized JavaScript origins

```
https://smartlic.tech
https://bidiq-frontend-production.up.railway.app
https://fqqyovlzdzimiwfofdjk.supabase.co
http://localhost:3000 (desenvolvimento)
```

### Authorized redirect URIs

```
https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback
https://smartlic.tech/auth/callback
http://localhost:3000/auth/callback (desenvolvimento)
```

---

## 3. Verificação no Supabase

Acesse o Supabase Dashboard:
https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk/auth/providers

### Configuração do Google Provider

1. **Enabled:** ✅ Ativado
2. **Client ID:** (colar do Google Cloud Console)
3. **Client Secret:** (colar do Google Cloud Console)
4. **Redirect URL:** (já preenchido automaticamente)
   - `https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback`

---

## 4. Páginas Legais Criadas

### Política de Privacidade
- **URL Produção:** https://smartlic.tech/privacidade
- **URL Desenvolvimento:** http://localhost:3000/privacidade
- **Arquivo:** `frontend/app/privacidade/page.tsx`

### Termos de Serviço
- **URL Produção:** https://smartlic.tech/termos
- **URL Desenvolvimento:** http://localhost:3000/termos
- **Arquivo:** `frontend/app/termos/page.tsx`

---

## 5. Resultado Esperado

Após a configuração, a tela de login do Google deve exibir:

**Antes:**
```
Prosseguir para fqqyovlzdzimiwfofdjk.supabase.co
```

**Depois:**
```
Prosseguir para SmartLic
```

---

## 6. Verificação e Testes

### 6.1 Testar localmente

```bash
cd frontend
npm run dev
```

Acesse: http://localhost:3000/login

### 6.2 Testar em produção

Acesse: https://smartlic.tech/login

### 6.3 Verificar OAuth Consent Screen

1. Clique em "Login com Google"
2. Verificar se aparece "Prosseguir para SmartLic"
3. Verificar se os links de Privacidade e Termos estão funcionando

---

## 7. Troubleshooting

### Erro: "redirect_uri_mismatch"

**Causa:** A URL de callback não está registrada no Google Cloud Console

**Solução:** Adicionar a URL exata em "Authorized redirect URIs"

### Erro: "invalid_client"

**Causa:** Client ID ou Client Secret incorretos

**Solução:** Verificar se as credenciais no Supabase coincidem com o Google Cloud Console

### Ainda aparece "fqqyovlzdzimiwfofdjk.supabase.co"

**Causa:** O OAuth Consent Screen ainda não foi configurado

**Solução:**
1. Acessar https://console.cloud.google.com/apis/credentials/consent
2. Preencher "App name" com "SmartLic"
3. Preencher "Application homepage" com "https://smartlic.tech"
4. Salvar alterações
5. Aguardar até 10 minutos para propagação

---

## 8. Comandos Úteis (CLI)

### Verificar configuração do Supabase

```bash
# Listar projetos
npx supabase projects list

# Ver detalhes do projeto
npx supabase projects api-keys --project-ref fqqyovlzdzimiwfofdjk
```

### Verificar variáveis de ambiente (Railway)

```bash
railway variables
```

---

## 9. Checklist de Configuração

- [ ] App name configurado no OAuth Consent Screen
- [ ] Homepage URL configurada (https://smartlic.tech)
- [ ] Privacy Policy URL configurada (https://smartlic.tech/privacidade)
- [ ] Terms of Service URL configurada (https://smartlic.tech/termos)
- [ ] Authorized domains adicionados (smartlic.tech, supabase.co)
- [ ] Authorized JavaScript origins configurados
- [ ] Authorized redirect URIs configurados
- [ ] Client ID e Secret copiados para Supabase
- [ ] Google Provider ativado no Supabase
- [ ] Teste local realizado
- [ ] Teste em produção realizado
- [ ] Verificado "Prosseguir para SmartLic" na tela de login

---

## 10. Contatos e Referências

### Documentação Oficial

- **Google Cloud Console:** https://console.cloud.google.com/
- **Supabase Auth:** https://supabase.com/docs/guides/auth
- **Google OAuth 2.0:** https://developers.google.com/identity/protocols/oauth2

### Suporte

- **E-mail:** tiago.sasaki@gmail.com
- **Projeto Supabase:** fqqyovlzdzimiwfofdjk
- **Google Cloud Project:** (verificar no Console)

---

**Última atualização:** 07 de fevereiro de 2026
