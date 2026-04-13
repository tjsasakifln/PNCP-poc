# UX-432: Resultados de busca perdidos ao navegar entre paginas

**Status:** Done
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I1)
**Sprint:** Próximo

## Contexto

Ao sair de /buscar (clicar em Dashboard, Pipeline, etc.) e voltar, todos os resultados são perdidos. O usuário precisa refazer a busca (~60s). Isso impede fluxos naturais como "ver resultado → abrir pipeline → voltar para o resultado".

O hook `useSearchPersistence.ts` já existe no projeto — verificar se está sendo usado corretamente ou se está desabilitado.

## Acceptance Criteria

- [x] AC1: `useSearchPersistence` persiste os resultados da busca ativa em `sessionStorage` com TTL de 30 minutos
- [x] AC2: Ao retornar para `/buscar`, restaurar automaticamente resultados persistidos se TTL não expirou
- [x] AC3: Banner "Resultados da busca anterior — [setor] em [UFs]" exibido no topo quando restaurando, com botão "Nova busca"
- [x] AC4: Se TTL expirou ou dados corrompidos, limpar sessionStorage e mostrar formulário em branco (sem erro)
- [x] AC5: Persistência não armazena dados sensíveis além de resultados de editais públicos (sem tokens, sem PII)

## Escopo

**IN:** `frontend/app/buscar/hooks/useSearchPersistence.ts` (habilitar ou corrigir persistência), `frontend/app/buscar/page.tsx` (restaurar estado ao montar), `frontend/app/buscar/hooks/useSearchState.ts` (integração com estado global)
**OUT:** Persistência entre sessões de browser (apenas sessionStorage, não localStorage nem banco), mudanças no backend, persistência de histórico de buscas (feature separada já existente)

## Complexidade

**S** (1–2 dias) — `useSearchPersistence` já existe; provável que só precise ser habilitado/corrigido + banner de restauração

## Dependências

Nenhuma dependência de outras stories.

## Riscos

- **Tamanho do payload:** 394 resultados serializados podem exceder limite do sessionStorage (~5MB) — verificar e limitar a primeiros 100 resultados se necessário, com aviso ao restaurar
- **Estado inconsistente:** Se o usuário tem dois tabs abertos, a persistência pode conflitar — aceitar como limitação conhecida (sessionStorage é por tab)

## Critério de Done

- [x] Navegar de `/buscar` para `/dashboard` e voltar: resultados de 394 oportunidades restaurados sem refazer a busca
- [x] Banner "Resultados da busca anterior" visível com opção de nova busca
- [x] sessionStorage limpo após 30 minutos ou ao clicar "Nova busca"
- [x] `npm test` passa sem regressões

## Arquivos Prováveis

- `frontend/app/buscar/hooks/useSearchPersistence.ts` — lógica de persistência (já existe)
- `frontend/app/buscar/page.tsx` — restauração ao montar
- `frontend/app/buscar/hooks/useSearchState.ts` — estado dos resultados
- `frontend/app/buscar/hooks/useSearchOrchestration.ts` — coordenação do fluxo

## File List

### Novos
- `frontend/lib/navSearchCache.ts` — utilitário de cache de navegação (30-min TTL, sessionStorage, não auto-clear)
- `frontend/app/buscar/components/RestoredResultsBanner.tsx` — banner "Resultados da busca anterior"
- `frontend/__tests__/lib/navSearchCache.test.ts` — 16 unit tests

### Modificados
- `frontend/app/buscar/hooks/useSearchPersistence.ts` — auto-save em result change, restore do nav cache, `isRestoredFromNav`, `handleNovaBusca`
- `frontend/app/buscar/hooks/useSearch.ts` — expõe `isRestoredFromNav`, `restoredNavMeta`, `handleNovaBusca`
- `frontend/app/buscar/page.tsx` — renderiza `RestoredResultsBanner` quando `isRestoredFromNav`
- `frontend/__tests__/hooks/useSearchPersistence-isolation.test.ts` — +9 testes UX-432

## Dev Notes

- Auth-flow cache (`searchStatePersistence.ts`) preservada e tem prioridade sobre nav cache — sem alteração na semântica existente
- Nav cache usa chave `smartlic_nav_search_state` (diferente de `smartlic_pending_search_state`)
- Payload limitado a 100 licitacoes via `trimResult()` para evitar QuotaExceededError
- sessionStorage é por tab — conflito entre tabs aceito como limitação conhecida
- `useEffect` auto-save escuta apenas `result` (não `filters`) para evitar re-saves desnecessários; filters capturados via closure

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-13 | @dev | Implementação completa — 57 testes passando, zero regressões |
