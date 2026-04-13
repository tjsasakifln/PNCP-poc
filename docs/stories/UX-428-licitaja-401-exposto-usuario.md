# UX-428: LICITAJA retornando 401 — API key invalida/expirada

**Status:** Ready
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C3)
**Sprint:** Atual

## Contexto

LICITAJA e uma fonte de dados que deve funcionar. Durante a busca, um badge vermelho "X LICITAJA" aparece com "HTTP 401: Authentication failed". O problema e que a API key esta invalida ou expirada — nao e para ocultar, e para **corrigir a autenticacao**.

A mensagem exposta ao usuario ("check LICITAJA_API_KEY") tambem e inadequada — deve ser amigavel.

## Acceptance Criteria

- [ ] AC1: Diagnosticar por que LICITAJA_API_KEY retorna 401 (expirada? rotacionada? env var errada?) — Operacional: LICITAJA não tem client implementado no codebase. Verificar Railway vars se/quando integração for adicionada.
- [ ] AC2: Corrigir/renovar API key e validar que LICITAJA retorna resultados — Operacional: depende de integração com vendor LICITAJA (fora do escopo desta story).
- [x] AC3: Sanitizar mensagens de erro expostas ao usuario — nao mostrar nomes de env vars — `_sanitize_source_error()` em `backend/progress.py` mapeia erros técnicos → mensagens amigáveis antes de emitir SSE.
- [x] AC4: Badge de erro deve mostrar "LICITAJA indisponivel" (nao detalhes internos de auth) — `sanitizeErrorForDisplay()` em `SourceStatusGrid.tsx` + label `LICITAJA: "LicitaJá"` adicionado.
- [x] AC5: Adicionar health check para LICITAJA no endpoint /health/cache ou similar — `GET /health/sources` adicionado em `backend/routes/health.py` usando `source_health_registry`.
- [ ] AC6: Confirmar que busca retorna resultados LICITAJA apos fix — Operacional: depende de AC1/AC2 (integração com vendor).

## Arquivos Provaveis

- `backend/clients/licitaja_client.py` ou similar — client LICITAJA
- `backend/config.py` — LICITAJA_API_KEY
- Railway env vars — verificar valor atual
- `frontend/app/buscar/page.tsx` — sanitizacao da mensagem de erro

## Escopo

**IN:** `backend/clients/licitaja_client.py`, `backend/config.py`, Railway env vars, `frontend/app/buscar/page.tsx` (sanitização de mensagens de erro), `backend/routes/health.py` (health check LICITAJA)  
**OUT:** Mudanças na lógica de busca multi-fonte, alteração de prioridade de fontes, modificações no circuito breaker de outras fontes

## Complexidade

**S** (< 1 dia) — diagnóstico de credencial + sanitização de mensagem de erro + health check opcional

## Riscos

- **API key expirada vs rotacionada:** Se a chave expirou por inatividade, renovação pode exigir contato com LICITAJA — fora do controle da equipe. Ter fallback (removendo a fonte temporariamente) como contingência.
- **Dados sensíveis em logs:** A sanitização deve se estender aos logs de backend, não apenas à resposta ao frontend

## Critério de Done

- Busca retorna resultados LICITAJA sem badge de erro vermelho
- Console do browser não exibe "check LICITAJA_API_KEY" ou qualquer nome de env var
- Badge de erro (se LICITAJA cair novamente) exibe "LICITAJA indisponível" em linguagem amigável
- `/health/cache` ou endpoint equivalente reporta status da fonte LICITAJA

## Screenshot

`ux-audit/04-busca-loading.png`

## File List

- `backend/progress.py` — `_sanitize_source_error()` helper + uso em `emit_source_error` (AC3)
- `frontend/app/buscar/components/SourceStatusGrid.tsx` — `sanitizeErrorForDisplay()` + `LICITAJA` em SOURCE_LABELS + tooltip sanitizado (AC4)
- `backend/routes/health.py` — `GET /health/sources` endpoint (AC5)
- `backend/tests/test_ux428_error_sanitization.py` — 14 testes unitários + 2 testes de integração

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-13 | @dev | AC3: `_sanitize_source_error` em `progress.py` — sanitiza erros antes do SSE |
| 2026-04-13 | @dev | AC4: `sanitizeErrorForDisplay` em `SourceStatusGrid.tsx` + label LICITAJA |
| 2026-04-13 | @dev | AC5: `GET /health/sources` em `routes/health.py` |
| 2026-04-13 | @dev | Testes criados em `tests/test_ux428_error_sanitization.py` |
