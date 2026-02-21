# Postmortem: Frontend Down (smartlic.tech 404)

**Data do incidente:** 2026-02-21
**Duração estimada:** ~9h30 (build at 01:40 UTC, confirmed down at 11:14 UTC)
**Severidade:** P0 — 100% dos usuários afetados
**Resolvido em:** 2026-02-21 ~11:20 UTC (redeploy via `railway up`)

## Timeline

| Hora (UTC) | Evento |
|------------|--------|
| 2026-02-21 01:40 | Build #latest completa com sucesso. Healthcheck passes. Container starts ("Ready in 269ms"). |
| 2026-02-21 ~02:00+ | Container presumivelmente crashou silenciosamente após startup. Logs mostram apenas 2 linhas: "Starting Container" + "Ready in 269ms". Nenhum log de runtime. |
| 2026-02-21 ~02:00+ | Railway `restartPolicyMaxRetries=3` exauriu. Serviço parou de tentar reiniciar. |
| 2026-02-21 11:14 | Confirmado via `curl`: `smartlic.tech` retorna HTTP 404, `X-Railway-Fallback: true`, body: `{"status":"error","code":404,"message":"Application not found"}`. |
| 2026-02-21 11:15 | Backend confirmado healthy: `bidiq-uniformes-production.up.railway.app/health` → 200 OK (uptime: 35979s). |
| 2026-02-21 11:17 | Redeploy triggered via `railway up --detach` from frontend directory. |
| 2026-02-21 11:20 | Frontend confirmed UP: HTTP 200, `Content-Type: text/html`, `Server: cloudflare`, `X-Railway-Fallback` ABSENT. |

## Causa Raiz

**Container crash silencioso pós-startup.** O container Next.js standalone (`node server.js`) iniciou com sucesso (Ready in 269ms) e passou o healthcheck inicial, mas crashou logo depois sem produzir logs de erro. Possíveis causas:

1. **OOM Kill:** Next.js standalone em produção pode exceder a memória alocada durante o primeiro request ou durante background compilation. Railway mata o container sem log adicional.
2. **Uncaught exception na primeira request:** Se um request chega antes que o app esteja totalmente inicializado (SSR de página com dependência de env var runtime), pode crashar o processo Node.
3. **Health check timeout em ciclos subsequentes:** O healthcheck path (`/api/health`) faz probe ao backend. Se o backend timeout causasse o health route a demorar >120s, Railway mataria o container.

**Nota:** Não foi possível determinar a causa exata porque Railway não retém logs de containers que crasharam após exaurir restarts.

## O que fazer se acontecer de novo

### Diagnóstico rápido

```bash
# 1. Verificar se frontend está down
curl -sI https://smartlic.tech/ | grep -E "HTTP/|Server:|X-Railway"
# Se X-Railway-Fallback: true → container não está rodando

# 2. Verificar backend (deve estar OK independente)
curl -sS https://bidiq-uniformes-production.up.railway.app/health | python -m json.tool

# 3. Verificar logs do frontend
railway logs -n 200 --service bidiq-frontend
railway logs -n 200 --service bidiq-frontend --build

# 4. Redeploy
cd frontend && railway up --detach
```

### Prevenções implementadas (GTM-CRIT-001)

1. **Health check lightweight (`/health/ready`):** Não faz I/O, responde em <50ms. Railway não mata o container por health check lento.
2. **`healthcheckTimeout` reduzido para 30s:** Detecta falha mais rápido, mas não mata por lentidão de dependências.
3. **Frontend health retorna 503 quando BACKEND_URL faltando:** Railway detecta misconfiguration.
4. **Startup gate no backend:** Valida Supabase/Redis antes de aceitar tráfego.

## Validação pós-recovery

### AC6 — Todos os domínios

| Domínio | Status | Content-Type |
|---------|--------|-------------|
| `smartlic.tech` | 200 OK | text/html |
| `app.smartlic.tech` | 200 OK | text/html |
| `www.smartlic.tech` | Não configurado (sem resposta) |
| `/login` | 200 OK | text/html |
| `/buscar` | 307 redirect (auth required — expected) |
| `/planos` | 200 OK | text/html |

### AC10 — Headers de serviço

- `Server: cloudflare` (aceitável — Cloudflare CDN)
- `X-Railway-Fallback` **ABSENT** (correto — servido pelo app)
- `x-railway-edge: railway/us-east4-eqdc4a` (presente — routing info, not fallback)

### AC8 — Probes temporais

| Probe | Hora (UTC) | Status | Server | X-Railway-Fallback | Body |
|-------|-----------|--------|--------|-------------------|------|
| 1 | 11:21 | 200 OK | cloudflare | absent | HTML |
| 2 | Pendente (+1h) | | | | |
| 3 | Pendente (+6h) | | | | |

**Nota:** Probes 2 e 3 serão executados manualmente e registrados aqui.

## Lições aprendidas

1. **Railway não retém logs de containers que exauriram restarts** — precisamos de logging externo (Sentry, Datadog) para capturar crashes.
2. **Health check pesado pode matar o container** — GTM-CRIT-001 resolve isso com `/health/ready` lightweight.
3. **`restartPolicyMaxRetries=3` é muito baixo** — considerar aumentar para 5 ou ON_FAILURE sem limite.
4. **Não há alerting automático** — quando o frontend cai, ninguém é notificado até um usuário reclamar.
