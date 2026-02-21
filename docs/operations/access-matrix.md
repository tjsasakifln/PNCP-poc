# Access Matrix & RACI — SmartLic

**Version:** 1.0
**Created:** 2026-02-21
**Owner:** Tiago Sasaki (tiago.sasaki@gmail.com)
**Next Review:** 2026-05-21 (quarterly)

---

## 1. Service Access Matrix

| Serviço | URL Console | Quem tem acesso | Tipo de acesso | Como revogar |
|---------|-------------|-----------------|----------------|--------------|
| **Railway** | https://railway.app/dashboard | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (full admin) | Settings → Members → Remove member |
| **Supabase** | https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (full admin) | Settings → Team → Remove member |
| **Stripe** | https://dashboard.stripe.com | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (full admin) | Settings → Team and security → Remove team member |
| **Sentry** | https://sentry.io/organizations/confenge/ | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (full admin) | Settings → Members → Remove member |
| **GitHub** | https://github.com/tjsasakifln/PNCP-poc | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (full admin) | Settings → Collaborators → Remove collaborator |
| **OpenAI** | https://platform.openai.com | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (API key holder) | API keys → Revoke key; regenerate in Railway env vars |
| **UptimeRobot** | https://dashboard.uptimerobot.com | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (free plan) | My Settings → Remove account / change email |
| **Dominio (smartlic.tech)** | Registrar where domain was purchased (check WHOIS) | Tiago Sasaki (tiago.sasaki@gmail.com) | Owner (registrant) | Domain registrar dashboard → Transfer / change nameservers |

### 1.1 API Keys in Production

| Chave | Onde está armazenada | Serviço que consome | Como rotacionar |
|-------|---------------------|---------------------|-----------------|
| `OPENAI_API_KEY` | Railway env vars | Backend (LLM classification + summaries) | OpenAI Console → API keys → Create new → Railway env vars → `railway variables set OPENAI_API_KEY=sk-...` → Restart service |
| `STRIPE_SECRET_KEY` | Railway env vars | Backend (billing) | Stripe Dashboard → Developers → API keys → Roll key → Update Railway env var |
| `STRIPE_WEBHOOK_SECRET` | Railway env vars | Backend (webhook verification) | Stripe Dashboard → Webhooks → Signing secret → Roll → Update Railway env var |
| `SUPABASE_SERVICE_ROLE_KEY` | Railway env vars | Backend (admin DB access) | Supabase Dashboard → Settings → API → Generate new key → Update Railway env var |
| `SUPABASE_ANON_KEY` | Railway env vars + Frontend | Frontend + Backend (public client) | Supabase Dashboard → Settings → API → Generate new key → Update both services |
| `SENTRY_DSN` | Railway env vars + Frontend | Both (error tracking) | Sentry → Settings → Client Keys → Generate new → Update both services |
| `RESEND_API_KEY` | Railway env vars | Backend (transactional email) | Resend Dashboard → API Keys → Create new → Update Railway env var |
| `METRICS_TOKEN` | Railway env vars | Backend (/metrics auth) | Generate new random token → Update Railway env var + Grafana scrape config |
| `REDIS_URL` | Railway env vars | Backend (cache + jobs) | Railway Redis addon → Connection string auto-managed; or Upstash dashboard → Reset password |

---

## 2. Credenciais Emergenciais

### Onde encontrar credenciais de backup

| Item | Localização | Acesso |
|------|-------------|--------|
| **Todas as API keys de produção** | Railway Dashboard → Project → Variables | Login Railway com tiago.sasaki@gmail.com |
| **Credenciais Supabase** | Supabase Dashboard → Settings → API | Login Supabase com tiago.sasaki@gmail.com |
| **Stripe keys** | Stripe Dashboard → Developers → API keys | Login Stripe com tiago.sasaki@gmail.com |
| **Recovery codes (2FA)** | Gerenciador de senhas pessoal do owner | Acesso físico ao dispositivo do owner |
| **Backup .env completo** | Arquivo `.env` local no repositório (gitignored) | Acesso ao laptop do owner |

### Procedimento de emergência (owner indisponível)

1. **Railway:** Se o owner configurou acesso de equipe, use as credenciais de equipe. Caso contrário, contate Railway Support (https://railway.app/help) com prova de propriedade do domínio
2. **Supabase:** Contate Supabase Support com prova de propriedade do projeto
3. **Stripe:** Contate Stripe Support (https://support.stripe.com) — requer verificação de identidade do titular da conta
4. **GitHub:** Se configurado com colaboradores, eles mantêm acesso. Caso contrário, contate GitHub Support
5. **Domínio:** Contate o registrar com prova de identidade do titular

> **IMPORTANTE:** Nunca documente credenciais em texto plano neste repositório. Este documento lista apenas ONDE encontrá-las, não as credenciais em si.

---

## 3. Matriz RACI

**Legenda:** R = Responsible (executa), A = Accountable (aprova/responde), C = Consulted, I = Informed

| Operação | Tiago Sasaki |
|----------|-------------|
| **Deploy produção** | R, A |
| **Rollback** | R, A |
| **Resposta a incidente P0** | R, A |
| **Rotação de segredos** | R, A |
| **Migração de banco** | R, A |
| **Monitoramento pós-deploy** | R, A |

### 3.1 RACI expandida (quando time crescer)

A tabela abaixo serve como template para quando novos membros forem adicionados:

| Operação | DevOps Lead | Backend Dev | Frontend Dev | PM | CTO |
|----------|------------|-------------|--------------|-----|-----|
| **Deploy produção** | R | C | C | I | A |
| **Rollback** | R | C | I | I | A |
| **Resposta a incidente P0** | R | C | I | I | A |
| **Rotação de segredos** | R | I | I | I | A |
| **Migração de banco** | R | R | I | I | A |
| **Monitoramento pós-deploy** | R | C | C | I | A |

> **Regra:** Toda operação crítica deve ter pelo menos 1 Responsible e 1 Accountable. Nunca deixe uma operação sem designação.

---

## 4. Mapeamento de Aliases

Aliases usados nos runbooks e documentação de deployment mapeiam para pessoas reais conforme tabela abaixo:

| Alias | Pessoa | Contato | Disponibilidade |
|-------|--------|---------|-----------------|
| @oncall-dev | Tiago Sasaki | tiago.sasaki@gmail.com | 24/7 |
| @devops-lead | Tiago Sasaki | tiago.sasaki@gmail.com | 24/7 |
| @devops | Tiago Sasaki | tiago.sasaki@gmail.com | 24/7 |
| @db-team | Tiago Sasaki | tiago.sasaki@gmail.com | 24/7 |
| @pm | Tiago Sasaki | tiago.sasaki@gmail.com | Horário comercial |
| @architect | Tiago Sasaki | tiago.sasaki@gmail.com | Horário comercial |
| @qa | Tiago Sasaki | tiago.sasaki@gmail.com | Horário comercial |
| @CTO | Tiago Sasaki | tiago.sasaki@gmail.com | 24/7 (P0 apenas) |

> **Nota:** Na fase atual (POC/beta, pre-revenue), todas as funções são exercidas por uma única pessoa. À medida que o time crescer, este mapeamento deve ser atualizado com as pessoas reais de cada função.

### 4.1 Escalation Path (com nomes reais)

```
P3 (Low):     Tiago Sasaki → Cria ticket no backlog (sem escalação)
P2 (Medium):  Tiago Sasaki → Investiga em até 4h
P1 (High):    Tiago Sasaki → Fix em até 1h, war room se necessário
P0 (Critical): Tiago Sasaki → Rollback imediato (< 15 min)
```

---

## 5. Checklist de Onboarding de Novo Membro

Quando um novo membro for adicionado ao time:

- [ ] Adicionar ao GitHub como collaborator (Settings → Collaborators)
- [ ] Adicionar ao Railway como team member (Settings → Members)
- [ ] Adicionar ao Supabase como team member (Settings → Team)
- [ ] Adicionar ao Sentry como team member (Settings → Members)
- [ ] Compartilhar acesso ao UptimeRobot se necessário
- [ ] Criar conta Stripe com role limitada se necessário
- [ ] Atualizar este documento (Access Matrix + RACI + Aliases)
- [ ] Atualizar contatos nos runbooks

## 6. Checklist de Offboarding

Quando um membro sair do time:

- [ ] Remover do GitHub (Settings → Collaborators → Remove)
- [ ] Remover do Railway (Settings → Members → Remove)
- [ ] Remover do Supabase (Settings → Team → Remove)
- [ ] Remover do Sentry (Settings → Members → Remove)
- [ ] Revogar acesso UptimeRobot
- [ ] Remover do Stripe (Settings → Team and security → Remove)
- [ ] Rotacionar todos os segredos que o membro tinha acesso
- [ ] Atualizar este documento
- [ ] Verificar que nenhum deploy/webhook usa credenciais pessoais do membro

---

**Document Version:** 1.0
**Created:** 2026-02-21
**Last Updated:** 2026-02-21
**Owner:** Tiago Sasaki (tiago.sasaki@gmail.com)
**Next Review:** 2026-05-21
