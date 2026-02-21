# Runbook: Outage Genérico — SmartLic

**Version:** 1.0
**Created:** 2026-02-21
**Owner:** Tiago Sasaki (tiago.sasaki@gmail.com)
**Severity:** Todos os níveis (P0–P3)

---

## Primeiros 5 Minutos — Checklist Imediato

Ao receber alerta de outage ou relato de usuário, execute estes 5 passos na ordem:

### 1. Verificar logs do Railway

```bash
railway logs --tail
```

Ou acesse: https://railway.app/dashboard → Projeto SmartLic → Deployments → Logs

### 2. Verificar UptimeRobot

Acesse: https://dashboard.uptimerobot.com

Monitores ativos:
- **SmartLic Backend Health:** `https://bidiq-backend-production.up.railway.app/health`
- **SmartLic Frontend Health:** `https://smartlic.tech/api/health`

Se ambos estão UP → problema pode ser parcial ou intermitente. Prossiga para diagnóstico.

### 3. Verificar Sentry para erros recentes

Acesse: https://sentry.io/organizations/confenge/

Procure por:
- Novos erros nas últimas 1h
- Spike de error rate (> 5%)
- Erros em `webhooks/stripe.py` (revenue-critical)

### 4. Health check manual do backend

```bash
curl -s https://bidiq-backend-production.up.railway.app/health | python3 -m json.tool
```

Resposta esperada:
```json
{
  "status": "ok",
  "version": "vX.Y.Z",
  "timestamp": "..."
}
```

Se retornar erro ou timeout → backend está down.

### 5. Decidir: Rollback vs. Fix Forward

| Situação | Ação |
|----------|------|
| Deploy recente causou o problema | **Rollback** → Seção "Rollback Rápido" abaixo |
| Problema em third-party (Supabase, OpenAI, etc.) | **Aguardar + Mitigar** → Seção "Third-Party Failures" |
| Bug sem deploy recente | **Fix Forward** → Investigar, corrigir, deploy |
| Não consegue identificar causa em 5 min | **Rollback preventivo** → Investigar depois |

---

## Fluxo Decisório Completo

### Passo 1: É o sistema ou é o usuário?

```
Usuário relata problema
    │
    ├── Consegue acessar https://smartlic.tech ?
    │   ├── SIM → Problema pode ser parcial. Verifique funcionalidade específica.
    │   └── NÃO → Verifique:
    │       ├── DNS: `nslookup smartlic.tech` (resolve?)
    │       ├── Sua rede: Tente de outro device/rede (celular 4G)
    │       └── Se SÓ o usuário não acessa → Problema de rede/DNS do usuário
    │
    └── UptimeRobot alerta DOWN → Confirmado: sistema fora do ar
```

### Passo 2: Classificar o tipo de outage

| Tipo | Sintomas | Verificação |
|------|----------|-------------|
| **Backend down** | Frontend carrega, buscas falham, API retorna 502/503 | `curl /health` falha |
| **Frontend down** | Página não carrega, erro 500 no navegador | `curl https://smartlic.tech` falha |
| **Ambos down** | Nada funciona | Ambos os health checks falham |
| **Parcial** | Algumas funcionalidades falham (ex: busca ok, pipeline falha) | Health check OK mas funcionalidade específica falha |
| **Third-party** | Sistema funciona parcialmente, erros em operações que dependem de serviço externo | Ver seção "Third-Party Failures" |

### Passo 3: Diagnosticar

#### Backend down

```bash
# 1. Ver logs recentes
railway logs --tail

# 2. Ver último deploy
railway deployments

# 3. Verificar se há crash loop
# Procure por: "Application failed to start", "ModuleNotFoundError", "SyntaxError"

# 4. Verificar memória/CPU no Railway Dashboard
# https://railway.app/dashboard → Metrics
```

**Causas comuns:**
- Erro de sintaxe em deploy recente → Rollback
- Dependência faltando → `pip install` no requirements.txt
- Variável de ambiente removida → `railway variables` para verificar
- Limite de memória atingido → Verificar metrics no Railway

#### Frontend down

```bash
# 1. Verificar se build falhou
# Railway Dashboard → Frontend service → Deployments → Build logs

# 2. Verificar se Next.js inicia
# Procure por: "ready on http://0.0.0.0:3000"

# 3. Testar localmente
cd frontend && npm run build && npm start
```

**Causas comuns:**
- Build falhou (TypeScript error) → Fix + redeploy
- Variável de ambiente NEXT_PUBLIC_* faltando → `railway variables`
- Erro em runtime (SSR crash) → Sentry + logs

### Passo 4: Agir

#### Rollback Rápido

```bash
# Opção 1: Rollback via Railway (revert to previous deployment)
# Railway Dashboard → Deployments → Selecionar deployment anterior → Redeploy

# Opção 2: Rollback via Git
git log --oneline -5                    # Identificar último commit bom
git revert HEAD                         # Reverter último commit
git push origin main                    # Triggera novo deploy

# Opção 3: Rollback completo (ver runbook detalhado)
# → docs/runbooks/rollback-procedure.md
```

#### Restart do Serviço

```bash
# Railway Dashboard → Service → Settings → Restart
# Ou: redeploy o commit atual
# Railway Dashboard → Deployments → Latest → Redeploy
```

### Passo 5: Comunicar

#### Template de comunicação para stakeholders

```
[INCIDENTE] SmartLic — {Backend/Frontend/Parcial} {Down/Degradado}

Status: {Investigando / Identificado / Mitigando / Resolvido}
Início: {HH:MM UTC-3}
Impacto: {Descrever o que está afetado — ex: "Buscas não retornam resultados"}
Causa: {Se identificada}
Ação: {O que está sendo feito}
ETA: {Estimativa de resolução}

Próxima atualização em {15/30/60} minutos.
```

---

## Third-Party Failures

### Supabase Down

**Sintomas:**
- Login/signup falha
- Buscas retornam erro de autenticação
- Pipeline não carrega
- Histórico não carrega
- Erro: "Could not connect to database" ou "JWT expired" nos logs

**Verificação:**

```bash
# Status page oficial
# https://status.supabase.com

# Teste de conectividade
curl -s "https://fqqyovlzdzimiwfofdjk.supabase.co/rest/v1/" \
  -H "apikey: $SUPABASE_ANON_KEY" | head -c 200

# Se Supabase CLI disponível
npx supabase status
```

**Impacto:**
- **Auth:** Login/signup totalmente indisponível
- **Data:** Pipeline, histórico, perfil inacessíveis
- **Cache L2:** Cache persistente (Supabase) indisponível; InMemory (L1) e Redis continuam funcionando

**Mitigação:**
1. Cache L1 (InMemory) + Redis continuam servindo buscas com dados em cache
2. Buscas novas funcionam (PNCP/PCP/ComprasGov não dependem de Supabase)
3. Feature flags não afetadas (defaults hardcoded no código)
4. **Ação:** Monitorar status page. Sem ação necessária além de comunicar aos usuários que login está temporariamente indisponível
5. **Duração típica:** Incidentes Supabase resolvem em 15-60 min

---

### OpenAI Down

**Sintomas:**
- Resumos executivos não são gerados (ou retornam fallback genérico)
- Classificação LLM zero-match falha (bids são REJEITADAS por padrão)
- Logs: "OpenAI API error", timeout em `/v1/chat/completions`

**Verificação:**

```bash
# Status page oficial
# https://status.openai.com

# Teste de API
curl -s https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | head -c 200
```

**Impacto:**
- **Classificação LLM:** Zero-match classification falha → fallback = REJECT (zero noise philosophy). Bids que só seriam aprovadas por LLM são rejeitadas temporariamente
- **Resumos:** `gerar_resumo_fallback()` (Python puro, sem LLM) gera resumo imediato. Resumo IA não é gerado
- **Busca funciona:** Keyword matching + density scoring funcionam normalmente sem LLM

**Mitigação:**
1. O sistema já tem fallback automático:
   - Zero-match → REJECT (sem noise, perde recall temporariamente)
   - Resumos → `gerar_resumo_fallback()` gera resumo básico
2. **Se prolongado (>1h):** Desabilitar LLM classification via feature flag:

```bash
railway variables set LLM_ARBITER_ENABLED=false
railway variables set LLM_ZERO_MATCH_ENABLED=false
```

3. **Ao voltar:** Reabilitar:

```bash
railway variables set LLM_ARBITER_ENABLED=true
railway variables set LLM_ZERO_MATCH_ENABLED=true
```

---

### Redis Down

**Sintomas:**
- Buscas mais lentas (sem cache L1 via Redis)
- Rate limiting não funciona (todas as requests passam)
- Circuit breaker state perdido (resets para fechado)
- ARQ job queue não processa (LLM/Excel em background falham)
- Logs: "Redis connection error", "ConnectionRefusedError"

**Verificação:**

```bash
# Se usando Upstash
# https://console.upstash.com → Database → Status

# Se Railway addon
railway logs  # Verificar Redis service logs

# Teste de conectividade
railway run python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

**Impacto:**
- **Cache:** InMemoryCache (in-process dict) continua funcionando como L1. Supabase cache (L2) continua funcionando
- **Rate limiting:** Degradado — requests não são limitadas (risco de abuso temporário)
- **Circuit breaker:** Estado perdido, reseta para CLOSED (pode causar requests a APIs instáveis)
- **ARQ jobs:** LLM summaries e Excel generation ficam inline (mais lento, mas funciona)
- **Background revalidation:** Não funciona (sem dedup key)

**Mitigação:**
1. O sistema funciona sem Redis (graceful fallback automático)
2. InMemoryCache + Supabase cache absorvem a maioria dos requests
3. **Se prolongado:** Monitorar uso de memória do backend (InMemory cache cresce sem eviction do Redis)
4. **Ação:** Verificar se é problema de rede (Railway interno) ou do provedor (Upstash). Geralmente auto-resolve
5. **Se Upstash:** Verificar quota/limits no dashboard

---

### Stripe Down

**Sintomas:**
- Página de planos não carrega preços
- Checkout não completa
- Webhooks não chegam (assinaturas não são ativadas)
- Portal de billing não abre
- Logs: "Stripe API error", timeout em requests Stripe

**Verificação:**

```bash
# Status page oficial
# https://status.stripe.com

# Teste de API
curl -s https://api.stripe.com/v1/prices \
  -u "$STRIPE_SECRET_KEY:" | head -c 200
```

**Impacto:**
- **Novos pagamentos:** Checkout indisponível
- **Assinaturas existentes:** Continuam funcionando (grace period de 3 dias — `SUBSCRIPTION_GRACE_DAYS`)
- **Plano do usuário:** Frontend usa localStorage cache (1h TTL). Backend usa `profiles.plan_type` como fallback
- **Buscas:** Funcionam normalmente (quota check usa plan_type local, não Stripe)
- **Webhooks atrasados:** Stripe reenvia webhooks automaticamente por até 3 dias

**Mitigação:**
1. **Nenhuma ação imediata necessária** — sistema funciona normalmente para usuários existentes
2. Grace period de 3 dias protege contra gaps de assinatura
3. `profiles.plan_type` mantém o plano ativo mesmo sem consultar Stripe
4. **Se prolongado (>24h):** Comunicar aos usuários que novos pagamentos estão temporariamente indisponíveis
5. **Ao voltar:** Webhooks atrasados são processados automaticamente pelo Stripe (retry automático)

---

## Troubleshooting Adicional

### Serviço reinicia em loop (crash loop)

```bash
# 1. Ver logs do crash
railway logs --tail

# 2. Causas comuns:
#    - Import error → Dependência faltando em requirements.txt
#    - Syntax error → Erro no último commit
#    - Env var missing → Variável removida acidentalmente
#    - Port binding → Outra instância usando a porta

# 3. Resolução rápida: rollback para deployment anterior
# Railway Dashboard → Deployments → Anterior → Redeploy
```

### Busca retorna 0 resultados (mas deveria retornar)

```bash
# 1. Verificar se PNCP está respondendo
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20260220&dataFinal=20260221&pagina=1&tamanhoPagina=5" | head -c 500

# 2. Verificar circuit breaker
curl -s https://bidiq-backend-production.up.railway.app/health | python3 -m json.tool

# 3. Se PNCP retorna 400 → Pode ser mudança na API
# CRÍTICO: tamanhoPagina máximo = 50 (>50 retorna 400 silenciosamente)

# 4. Verificar logs de busca
railway logs | grep "buscar_licitacoes"
```

### Deploy não sobe

```bash
# 1. Verificar build logs no Railway Dashboard
# 2. Causas comuns:
#    - requirements.txt com versão inválida
#    - package.json com dependência quebrada
#    - Dockerfile syntax error
#    - Limite de recursos Railway atingido

# 3. Verificar status Railway
# https://status.railway.app
```

---

## Contatos

| Role | Nome | Contato | Disponibilidade |
|------|------|---------|-----------------|
| **Primary On-Call** | Tiago Sasaki | tiago.sasaki@gmail.com | 24/7 |

**Suporte externo:**
- Railway: https://railway.app/help
- Supabase: https://supabase.com/support
- Stripe: https://support.stripe.com
- Sentry: https://sentry.io/support
- OpenAI: https://help.openai.com
- UptimeRobot: https://uptimerobot.com/help

**Runbooks relacionados:**
- Rollback detalhado: `docs/runbooks/rollback-procedure.md`
- PNCP-specific: `docs/runbooks/PNCP-TIMEOUT-RUNBOOK.md`
- Monitoring setup: `docs/runbooks/monitoring-alerting-setup.md`
- Access matrix: `docs/operations/access-matrix.md`

---

**Document Version:** 1.0
**Created:** 2026-02-21
**Last Updated:** 2026-02-21
**Owner:** Tiago Sasaki (tiago.sasaki@gmail.com)
**Next Review:** After first production incident using this runbook
