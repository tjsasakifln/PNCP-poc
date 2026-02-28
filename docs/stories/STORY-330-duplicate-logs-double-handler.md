# STORY-330: Eliminar logs duplicados — double handler no Gunicorn

**Prioridade:** P1 (infra — contribui para breach rate limit)
**Complexidade:** S (Small)
**Sprint:** CRIT-SEARCH

## Problema

Cada linha de log aparece **DUAS vezes** na produção Railway. Isso **dobra** o volume de logs e contribui para o breach do rate limit Railway de 500 logs/s (252 mensagens dropadas). Mensagens críticas podem estar sendo descartadas.

**Evidência:** Logs Railway 2026-02-28 — toda linha duplicada. "Railway rate limit of 500 logs/sec reached. Messages dropped: 252".

## Causa Raiz

Gunicorn configura o root logger via `logconfig_dict` em `gunicorn_conf.py` (handler "stdout"). Quando cada worker carrega o app FastAPI, `main.py` chama `setup_logging()` que executa `root_logger.addHandler(handler)` SEM limpar handlers existentes → root logger fica com 2 handlers → cada log emitido 2x.

## Critérios de Aceite

- [ ] AC1: `setup_logging()` em `config.py` limpa handlers existentes ANTES de adicionar: `root_logger.handlers.clear()` ou verifica duplicata
- [ ] AC2: Em modo dev (sem Gunicorn), `setup_logging()` continua funcionando (1 handler)
- [ ] AC3: Teste: chamar `setup_logging()` 2x → root logger tem exatamente 1 StreamHandler
- [ ] AC4: Após deploy, volume de logs reduz ~50% (monitorar Railway)
- [ ] AC5: Zero mensagens dropadas em condições normais (< 250 logs/s)

## Arquivos Afetados

- `backend/config.py` (`setup_logging()`, ~linhas 165-172)
- `backend/tests/test_config.py` (expandir)
