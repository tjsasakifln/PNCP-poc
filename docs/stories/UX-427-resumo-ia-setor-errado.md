# UX-427: Resumo IA mostra setor errado nos resultados de busca

**Status:** Ready
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

- [x] AC1: Resumo IA deve mencionar o setor correto da busca realizada
- [x] AC2: Investigar se resumo vem do ARQ job ou do fallback
- [x] AC3: Se fallback, verificar se `setor_nome` e passado corretamente
- [x] AC4: Se ARQ, verificar se job recebe search_id correto e nao reutiliza cache
- [x] AC5: Adicionar teste que verifica correspondencia setor buscado vs setor no resumo
- [x] AC6: Testar com pelo menos 3 setores diferentes e confirmar resumo correto

## Arquivos Provaveis

- `backend/llm.py` — `gerar_resumo()`, `gerar_resumo_fallback()`
- `backend/job_queue.py` — ARQ job de resumo
- `backend/search_cache.py` — cache de resultados
- `backend/routes/search.py` — montagem da resposta

## Escopo

**IN:** `backend/llm.py`, `backend/job_queue.py`, `backend/search_cache.py`, `backend/routes/search.py`  
**OUT:** Mudanças no modelo LLM, alteração de prompts de classificação setorial, frontend (exceto se mensagem de erro precisar ajuste)

## Complexidade

**S** (1–2 dias) — diagnóstico + fix pontual em passagem de parâmetro

## Riscos

- **Cache compartilhado:** Se o resumo vem de cache com chave incorreta, a correção pode invalidar cache de buscas existentes — verificar impacto antes de deploy
- **ARQ job assíncrono:** Job pode estar lendo parâmetros do contexto errado se search_id foi reutilizado — garantir que cada job tem snapshot dos params no momento do enfileiramento

## Critério de Done

- Buscar "Engenharia, Projetos e Obras" com SP/PR/RS/SC → resumo menciona "engenharia" ou "obras", nunca "uniformes"
- Testar 3 setores distintos (saúde, TI, limpeza) → resumo sempre coerente com setor buscado
- Nenhum teste existente quebrado

## Screenshot

`ux-audit/06-resultados-sucesso.png`
