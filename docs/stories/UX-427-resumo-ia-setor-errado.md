# UX-427: Resumo IA mostra setor errado nos resultados de busca

**Status:** Draft
**Prioridade:** P0 — Critico
**Origem:** UX Audit 2026-03-25 (C2)
**Sprint:** Atual

## Contexto

Ao buscar por "Engenharia, Projetos e Obras" com 4 UFs (SP/PR/RS/SC), o resumo gerado pela IA diz:
> "Foram identificadas 394 licitacoes relacionadas a **uniformes e fardamentos**"

Isso destroi a confianca do usuario na classificacao por IA, que e o principal diferencial do produto.

## Hipotese de Causa

- Cache de resumo stale (resumo de busca anterior sendo reutilizado)
- `gerar_resumo_fallback()` usando setor errado
- ARQ job de resumo processando com parametros incorretos

## Acceptance Criteria

- [ ] AC1: Resumo IA deve mencionar o setor correto da busca realizada
- [ ] AC2: Investigar se resumo vem do ARQ job ou do fallback
- [ ] AC3: Se fallback, verificar se `setor_nome` e passado corretamente
- [ ] AC4: Se ARQ, verificar se job recebe search_id correto e nao reutiliza cache
- [ ] AC5: Adicionar teste que verifica correspondencia setor buscado vs setor no resumo
- [ ] AC6: Testar com pelo menos 3 setores diferentes e confirmar resumo correto

## Arquivos Provaveis

- `backend/llm.py` — `gerar_resumo()`, `gerar_resumo_fallback()`
- `backend/job_queue.py` — ARQ job de resumo
- `backend/search_cache.py` — cache de resultados
- `backend/routes/search.py` — montagem da resposta

## Screenshot

`ux-audit/06-resultados-sucesso.png`
