# UX-432: Resultados de busca perdidos ao navegar entre paginas

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I1)
**Sprint:** Próximo

## Contexto

Ao sair de /buscar (clicar em Dashboard, Pipeline, etc.) e voltar, todos os resultados são perdidos. O usuário precisa refazer a busca (~60s). Isso impede fluxos naturais como "ver resultado → abrir pipeline → voltar para o resultado".

O hook `useSearchPersistence.ts` já existe no projeto — verificar se está sendo usado corretamente ou se está desabilitado.

## Acceptance Criteria

- [ ] AC1: `useSearchPersistence` persiste os resultados da busca ativa em `sessionStorage` com TTL de 30 minutos
- [ ] AC2: Ao retornar para `/buscar`, restaurar automaticamente resultados persistidos se TTL não expirou
- [ ] AC3: Banner "Resultados da busca anterior — [setor] em [UFs]" exibido no topo quando restaurando, com botão "Nova busca"
- [ ] AC4: Se TTL expirou ou dados corrompidos, limpar sessionStorage e mostrar formulário em branco (sem erro)
- [ ] AC5: Persistência não armazena dados sensíveis além de resultados de editais públicos (sem tokens, sem PII)

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

- Navegar de `/buscar` para `/dashboard` e voltar: resultados de 394 oportunidades restaurados sem refazer a busca
- Banner "Resultados da busca anterior" visível com opção de nova busca
- sessionStorage limpo após 30 minutos ou ao clicar "Nova busca"
- `npm test` passa sem regressões

## Arquivos Prováveis

- `frontend/app/buscar/hooks/useSearchPersistence.ts` — lógica de persistência (já existe)
- `frontend/app/buscar/page.tsx` — restauração ao montar
- `frontend/app/buscar/hooks/useSearchState.ts` — estado dos resultados
- `frontend/app/buscar/hooks/useSearchOrchestration.ts` — coordenação do fluxo
