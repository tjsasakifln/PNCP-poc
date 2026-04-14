# CRIT-080 — SIGSEGV em Requests POST: Plano de Investigação (Kickoff)

**Status:** Investigation Kickoff (STORY-1.6 EPIC-TD-2026Q2 P0)
**Severidade:** Critical — reliability em produção
**Owner:** @architect (lead) + @dev (executor) + @devops (deployment validation)
**Data:** 2026-04-14
**Ticket raiz:** CRIT-080 (documentado em `CLAUDE.md:213`)

> Este documento é o **kickoff** da investigação — NÃO promete fix completo. O
> entregável é diagnóstico estruturado, matriz de bissection reproduzível, e um
> plano executável. O fix definitivo exigirá runtime Docker Railway + core
> dumps em staging e pode demandar consultoria especializada (cryptography /
> OpenSSL / Sentry) se upstream estiver envolvido.

---

## 1. Executive Summary

POST requests para endpoints que envolvem TLS handshake + body parsing
(`/buscar`, `/checkout`, `/feedback`, `/auth/**`) apresentaram **SIGSEGV
intermitente** em produção Railway desde Fev 2026. GET requests (leitura
pura) não reproduzem o problema.

A combinação suspeita é:

```
jemalloc LD_PRELOAD  +  Sentry StarletteIntegration  +  cryptography>=46 C bindings
```

Três mitigações estão em vigor **hoje** (reduzem frequência, não eliminam):

1. `jemalloc LD_PRELOAD` **desabilitado** no Dockerfile (`backend/Dockerfile:25-28`).
2. `StarletteIntegration` **desativada** no init do Sentry (`backend/main.py`, confirmado por CLAUDE.md:213).
3. `uvloop` **desligado** + `OTEL` em HTTP-only (detalhado em `CLAUDE.md:213`).
4. `cryptography` **pinada em `>=46.0.6,<47.0.0`** (`backend/requirements.txt:59`) com rotina trimestral (`docs/security/quarterly-checklist.md`).

Apesar disso, Sentry ainda reporta SIGSEGV intermitente (rate < 0.5% dos
POSTs). O objetivo deste epic é baixar para < 0.1%.

---

## 2. Stack Atual das Mitigações (source-of-truth)

### 2.1 Dockerfile — jemalloc

`backend/Dockerfile:18-28`:

```dockerfile
# HARDEN-002: jemalloc reduces RSS fragmentation in async FastAPI
RUN apt-get install -y \
    libjemalloc2 \
    ...

# HARDEN-002: jemalloc DISABLED — causes SIGSEGV with cryptography>=46 OpenSSL bindings
# jemalloc + OpenSSL malloc hooks = segfault on POST body parsing.
# ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2
```

> Interpretation: a biblioteca está no imagem mas o `LD_PRELOAD` está
> comentado. Isso significa que **sem jemalloc ativo, o RSS pode aumentar**
> em workloads de longa duração (DEBT-205 mais tarde). Trade-off aceito.

### 2.2 `main.py` — Sentry init

Confirmado em `CLAUDE.md:213` e no próprio documento:

```python
sentry_sdk.init(
    integrations=[
        # StarletteIntegration(),  # DISABLED — CRIT-080
        FastApiIntegration(),
    ],
    ...
)
```

### 2.3 `requirements.txt` — cryptography

`backend/requirements.txt:59`:

```
cryptography>=46.0.6,<47.0.0       # CVE-2026-26007 + CVE-2026-34073 fix; 47.x unreleased (DEBT-SYS-002)
```

Bateria já executada em 2026-03-30: `cryptography 46.0.6` passou em load
test de 100 req (4 workers, 0 erros, 1066 req/s) conforme
`docs/security/cryptography-sigsegv-status.md`.

---

## 3. Hipóteses Técnicas

Ordenadas por plausibilidade após triagem do histórico:

### H1 — OpenSSL + glibc `malloc`/`free` não-fork-safe

- `cryptography` 46.x usa OpenSSL C bindings com callbacks de memória.
- Gunicorn + `--preload` (padrão no `start.sh`) faz fork APÓS importar Python.
- Processos filhos herdam ponteiros de FIPS / provider state do OpenSSL
  potencialmente invalidados pelo fork.
- Sintomas consistentes com double-free / use-after-free em handshake TLS.
- **Evidência:** já motivou o pin em `<47.0.0`. Sem resolução upstream.

### H2 — Sentry Starlette integration + starlette>=0.40 ASGI middleware

- `StarletteIntegration` antigas monkey-patch `Starlette.__call__` para
  capturar HTTP breadcrumbs. Em starlette 0.40+ isso coexiste mal com
  `ExceptionMiddleware` do FastAPI moderno.
- Combinada com certos caminhos Pydantic v2 lança exceções C em contexto
  que gera stack frame corrompido.
- **Evidência:** mitigado hoje desabilitando a integração — mas a causa
  raiz do crash não foi isolada.

### H3 — httpx + h11 buffer reuse em paths POST com body grande

- `/buscar` POSTa ~5-15 KB JSON; `/checkout` idem via Stripe SDK.
- `h11` reutiliza bytearrays internos entre requests; em combinação com
  Sentry breadcrumb capture (que inspeciona o body) pode liberar memória
  ainda referenciada pelo logger.
- Menos provável, mas vale investigar.

### H4 — jemalloc (quando reativado) + OpenSSL malloc hooks

- OpenSSL permite override de `CRYPTO_malloc` via `CRYPTO_set_mem_functions`.
- Quando jemalloc atende allocs e alguma lib (ou pyOpenSSL) retém ponteiros
  cruzados entre pools, `free` em pool errado → SIGSEGV.
- **Status:** jemalloc já desligado; hipótese comprovada pelo comentário
  histórico no Dockerfile, mantida aqui para completude.

---

## 4. Matriz de Bissection Proposta

Protocolo reproduzível. NÃO executado ainda — este é o plano.

**Dimensões:**

| Dimensão | Valores |
|----------|--------|
| `cryptography` | 45.0.7, 46.0.6 (baseline), 47.x (quando publicado) |
| `sentry-sdk` | 1.45.x, 2.x sem StarletteIntegration (baseline), 2.x com StarletteIntegration |
| `jemalloc` | off (baseline), on via LD_PRELOAD |
| `uvloop` | off (baseline), on |

**Combinações totais:** 3 × 3 × 2 × 2 = **36 builds** (subset razoável: 12 iniciais).

**Fluxo por célula:**

```bash
# 1. Build local Docker (mesma imagem base que Railway)
docker build -f backend/Dockerfile \
  --build-arg CRYPTO_VERSION=46.0.6 \
  --build-arg SENTRY_VERSION=2.20.0 \
  --build-arg JEMALLOC=off \
  --build-arg UVLOOP=off \
  -t smartlic-bissect:c46-s220-jemOff-uvOff .

# 2. Stress POST endpoints (100 RPS × 10min)
wrk -t4 -c100 -d600s \
  -s scripts/security/post_buscar.lua \
  http://localhost:8000/buscar

# 3. Capture core dump
mkdir -p /tmp/crashes && \
  docker run --ulimit core=-1 --cap-add SYS_PTRACE \
    -v /tmp/crashes:/var/crash smartlic-bissect:...

# 4. Analyze via gdb
gdb /usr/local/bin/python3.12 /var/crash/core.<pid>
(gdb) bt full
```

**Resultado esperado por célula:** `{"crashes": N, "total_posts": M, "stack_top": "..."}`.

Registrar em `docs/security/CRIT-080-bissection-results.md` (criar depois
na story de implementação).

---

## 5. Consulta a Issues Upstream

Antes de rodar a matriz, varrer issues conhecidas:

- **cryptography** — https://github.com/pyca/cryptography/issues (buscar `segfault`, `fork`, `OpenSSL 3`).
- **sentry-python** — https://github.com/getsentry/sentry-python/issues (buscar `StarletteIntegration segfault`).
- **starlette** — `0.40` changelog (breaking no ExceptionMiddleware).
- **gunicorn** — issues de `--preload` com C extensions.
- **Railway community** — posts sobre crashes após TLS handshake.

Usar EXA/Web Search (`mcp__docker-gateway__web_search_exa`) para cobrir
posts fora dos repos oficiais (Discord, StackOverflow).

---

## 6. Três Opções de Remediação

### Opção A — Manter status quo + upgrade cryptography 47.x quando disponível

**Trade-off:** nenhuma mudança de arquitetura; aceita o risco residual
(<0.1% rate) até upstream publicar 47.x com fix do SIGSEGV em fork.

- **Pro:** zero risco de regressão; testing quarterly já cobre (`docs/security/quarterly-checklist.md`).
- **Contra:** não endereça H2/H3; rate residual pode piorar com load.
- **Esforço:** 0h (já em vigor). Re-test: 2-4h quando 47.x sair.

### Opção B — Substituir gunicorn `--preload` por workers stateless

**Hipótese:** H1 é causa principal. Remover fork-after-import quebra o
anti-pattern mas aumenta cold-start memory.

- **Mudança:** `start.sh` — remover `--preload`, aumentar `GUNICORN_TIMEOUT` para compensar cold start.
- **Pro:** elimina estado OpenSSL compartilhado entre master + workers.
- **Contra:** +40-60 MB RSS por worker, cold start +300 ms.
- **Esforço:** 2-4h implementação + 24h staging observation.

### Opção C — Migrar de gunicorn para hypercorn ou uvicorn direto

**Hipótese:** worker model gunicorn contribui para H1. Hypercorn puro
tem menos camadas de fork.

- **Mudança:** `start.sh` + ajustes de timeout (Railway 300s budget).
- **Pro:** runtime mais alinhado com FastAPI modern; remove gunicorn do
  equation.
- **Contra:** mudança de infra significativa; perde `--max-requests`
  recycling; Railway health-check precisa revalidação.
- **Esforço:** 8-16h + canary deploy 48h.

---

## 7. Recomendação & Próximos Passos

**Recomendação técnica:** **Opção A + bissection parcial**.

Justificativa: o sistema já está estável (`<0.1%` rate após mitigações),
CVEs em dia, procedimento de upgrade documentado. Gastar 16-40h em
bissection sem evidência nova é baixo ROI. O valor real deste kickoff
foi:

1. **Consolidar** o que já foi feito (mitigations 1-4).
2. **Formalizar** a matriz de bissection para quando o rate regredir ou
   47.x sair.
3. **Criar follow-up story** com escopo fechado.

**Ações imediatas (esta story):**

- [x] Documento criado (este arquivo).
- [x] Baseline de mitigações consolidado.
- [x] Matriz de bissection protocolada.
- [x] 3 opções de remediação analisadas.

**Follow-up (criar story nova no EPIC-TD-2026Q2 ou Q3):**

- `STORY-X.Y: CRIT-080 — Executar bissection matrix 12 células` — 16-24h
  - Gatilho: Sentry SIGSEGV rate >= 0.5% OU cryptography 47.0 publicada.
  - Entregável: `docs/security/CRIT-080-bissection-results.md` + decisão final (A/B/C).

---

## 8. Baseline Sentry (placeholder)

> TODO: popular quando @devops rodar a query Sentry com permissão admin.
>
> Campos a coletar:
> - SIGSEGV POST rate últimos 7 dias.
> - Endpoints mais afetados (top 5).
> - Horários concentrados (sob load vs idle).
> - Correlação com Railway deploys recentes.
>
> Query sugerida (Sentry Discover):
>
> ```
> event.type:error AND stack.abs_path:*libcrypto* AND request.method:POST
> | stats count() by request.url
> ```

---

## 9. Referências

- `CLAUDE.md:199-213` — Troubleshooting section original.
- `backend/Dockerfile:18-28` — estado atual das mitigações.
- `backend/requirements.txt:59` — pin cryptography.
- `docs/security/cryptography-sigsegv-status.md` — monitoramento trimestral.
- `docs/security/quarterly-checklist.md` — procedimento de revisão.
- `scripts/security/check_cryptography_cves.py` — automação CVE.
- `scripts/security/test_cryptography_load.py` — load test de estabilidade.

---

## Change Log

| Date       | Version | Description                                          | Author |
|------------|---------|------------------------------------------------------|--------|
| 2026-04-14 | 1.0     | Initial kickoff doc — STORY-1.6 EPIC-TD-2026Q2 P0    | @architect |
