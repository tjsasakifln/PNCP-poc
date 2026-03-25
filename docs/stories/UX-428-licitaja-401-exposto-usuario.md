# UX-428: LICITAJA retornando 401 — API key invalida/expirada

**Status:** Draft
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C3)
**Sprint:** Atual

## Contexto

LICITAJA e uma fonte de dados que deve funcionar. Durante a busca, um badge vermelho "X LICITAJA" aparece com "HTTP 401: Authentication failed". O problema e que a API key esta invalida ou expirada — nao e para ocultar, e para **corrigir a autenticacao**.

A mensagem exposta ao usuario ("check LICITAJA_API_KEY") tambem e inadequada — deve ser amigavel.

## Acceptance Criteria

- [ ] AC1: Diagnosticar por que LICITAJA_API_KEY retorna 401 (expirada? rotacionada? env var errada?)
- [ ] AC2: Corrigir/renovar API key e validar que LICITAJA retorna resultados
- [ ] AC3: Sanitizar mensagens de erro expostas ao usuario — nao mostrar nomes de env vars
- [ ] AC4: Badge de erro deve mostrar "LICITAJA indisponivel" (nao detalhes internos de auth)
- [ ] AC5: Adicionar health check para LICITAJA no endpoint /health/cache ou similar
- [ ] AC6: Confirmar que busca retorna resultados LICITAJA apos fix

## Arquivos Provaveis

- `backend/clients/licitaja_client.py` ou similar — client LICITAJA
- `backend/config.py` — LICITAJA_API_KEY
- Railway env vars — verificar valor atual
- `frontend/app/buscar/page.tsx` — sanitizacao da mensagem de erro

## Screenshot

`ux-audit/04-busca-loading.png`
