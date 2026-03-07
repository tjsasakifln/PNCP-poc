# HARDEN-007: Gunicorn max_requests Worker Recycling

**Severidade:** ALTA
**Esforço:** 2 min
**Quick Win:** Sim
**Origem:** Conselho CTO — Pesquisa de Industria (2026-03-06)

## Contexto

Gunicorn sem `--max-requests` permite acúmulo lento de memória em workers long-running (global dicts, caches in-memory, fragmentação residual). Padrão da indústria para Python ASGI.

## Critérios de Aceitação

- [x] AC1: `--max-requests 1000` adicionado ao Gunicorn config
- [x] AC2: `--max-requests-jitter 50` para evitar restart simultâneo
- [x] AC3: Deploy bem-sucedido no Railway

## Solução

```bash
# start.sh ou gunicorn config
gunicorn main:app --max-requests 1000 --max-requests-jitter 50
```

## Arquivos Afetados

- `backend/start.sh` ou `backend/gunicorn.conf.py`
