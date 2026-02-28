# STORY-333: Paginação de resultados + sticky bar Excel/PDF/Sheets + fix histórico

**Prioridade:** P0 (UX crítico — 100+ resultados em página única é inutilizável)
**Complexidade:** M (Medium)
**Sprint:** CRIT-SEARCH

## Problema

Três problemas de usabilidade relacionados à exibição de resultados:

### 1. Sem paginação (100+ resultados em página única)
A busca retorna 50-200+ resultados filtrados em uma única lista contínua. Com 100+ cards renderizados de uma vez:
- Scroll infinito sem referência de posição
- Performance degradada (DOM com 100+ cards complexos)
- Impossível navegar ou comparar oportunidades distantes
- Usuário perde contexto ao scrollar

### 2. Botões Excel/PDF invisíveis durante busca travada
Os botões "Baixar Excel" e "Relatório PDF" ficam invisíveis quando a busca trava no loading infinito (consequência dos bugs SSE das STORY-326/327). Mesmo quando a busca completa, os botões ficam abaixo de 100+ resultados — o usuário nunca os vê sem scrollar até o final.

### 3. Google Sheets export quebrado
O botão "Exportar Google Sheets" (`GoogleSheetsExportButton.tsx`) existe no UI mas o fluxo OAuth + export está quebrado em produção. O endpoint `POST /api/export/google-sheets` (proxy → backend `export_sheets.py`) depende de OAuth Google token armazenado no Supabase (`get_user_google_token`). Possíveis causas: token expirado/revogado, callback OAuth desconfigurado, ou erro silencioso no proxy.

### 4. Botão "Próximo" ilegível no histórico
O botão de paginação em `/historico` usa `border-[var(--border)]` com `disabled:opacity-30` — contraste insuficiente, texto praticamente invisível.

## Estado Atual

### Paginação
- **Backend**: Schema `BuscaRequest` JÁ aceita `pagina` (default 1) e `itens_por_pagina` (default 20, range 10-100) — mas o pipeline **IGNORA** esses parâmetros e retorna TODOS os resultados
- **Frontend**: `SearchResults.tsx` → `LicitacoesPreview.tsx` renderiza tudo com `slice(0, previewCount)` (visible) + blur overlay (rest) para free tier. ZERO paginação
- **Sem lazy loading**: Todos os cards renderizados no DOM simultaneamente

### Excel/PDF
- **Excel**: Botão existe em `SearchResults.tsx:975-1030`, funcional (3-state: processing/retry/active)
- **PDF**: Botão existe em `SearchResults.tsx:1137-1165`, funcional (abre `PdfOptionsModal`)
- **Problema**: Ambos ficam NO FINAL da lista de resultados — com 100+ cards acima, são invisíveis

### Histórico
- **Paginação existe** em `historico/page.tsx:416-438`
- **Botões**: `Anterior` / `Próximo` com `text-sm border border-[var(--border)]`
- **disabled:opacity-30** — quase invisível quando desabilitado

## Critérios de Aceite

### Bloco 1: Paginação client-side dos resultados de busca

- [ ] AC1: Adicionar componente `Pagination` em `frontend/components/ui/Pagination.tsx` reutilizável: botões Anterior/Próximo + indicador "Página X de Y" + seletor de itens por página (10/20/50)
- [ ] AC2: `SearchResults.tsx` pagina os resultados client-side: `licitacoes.slice(offset, offset + pageSize)` onde `pageSize` default = 20
- [ ] AC3: O componente `Pagination` aparece ACIMA e ABAIXO da lista de resultados (topo para acesso rápido, rodapé para quem scrollou)
- [ ] AC4: Scroll automático para o topo da lista ao mudar de página (`scrollIntoView({ behavior: 'smooth' })`)
- [ ] AC5: O seletor de itens por página oferece 10, 20, 50 com persistência em `localStorage` (chave `smartlic_page_size`)
- [ ] AC6: A paginação reseta para página 1 quando o usuário faz uma nova busca ou muda a ordenação
- [ ] AC7: O header da lista mostra "Exibindo X-Y de Z oportunidades" (ex: "Exibindo 21-40 de 109 oportunidades")
- [ ] AC8: Paginated state é preservado na URL como query param (`?page=2`) para permitir compartilhamento/bookmark

### Bloco 2: Reposicionar botões Excel/PDF

- [ ] AC9: Mover os botões Excel e PDF para uma **barra de ações fixa** (sticky) no topo dos resultados, junto com o seletor de ordenação e contagem total
- [ ] AC10: A barra de ações contém: `[Ordenar por ▼] [Baixar Excel] [Google Sheets] [Relatório PDF] [X de Y oportunidades]`
- [ ] AC11: A barra fica `sticky top-0` com `z-index` adequado — sempre visível ao scrollar
- [ ] AC12: Em mobile (< 640px), os botões Excel/PDF ficam em row abaixo da ordenação (2 linhas)
- [ ] AC13: Se a busca está em loading (`isLoading=true`), a barra mostra skeleton/disabled state mas permanece visível

### Bloco 3: Fix Google Sheets export

- [ ] AC14: Diagnosticar o erro atual do Google Sheets export em produção: testar `POST /api/export/google-sheets` com token válido e capturar o erro exato (401? 403? 500? timeout?)
- [ ] AC15: Se o problema é OAuth token expirado/revogado: verificar que o fluxo `GET /auth/google` → callback → `get_user_google_token()` funciona end-to-end. Se token revogado, exibir mensagem "Reconecte sua conta Google" com botão de re-autorização
- [ ] AC16: Se o problema é proxy 404/502: verificar que `frontend/app/api/export/google-sheets/route.ts` roteia corretamente para `BACKEND_URL/api/export/google-sheets`
- [ ] AC17: Adicionar tratamento de erro user-friendly no `GoogleSheetsExportButton.tsx`: em vez de falha silenciosa, exibir toast com mensagem específica por código de erro (401→"Reconecte Google", 403→"Permissão revogada", 429→"Limite Google atingido", 500→"Erro interno")
- [ ] AC18: O botão Google Sheets deve aparecer na sticky bar de ações (AC10) junto com Excel e PDF
- [ ] AC19: Teste: mock export com sucesso → verifica toast de sucesso + abertura de nova aba com URL do spreadsheet
- [ ] AC20: Teste: mock export com 401 → verifica toast "Reconecte sua conta Google"

### Bloco 5: Fix botão histórico

- [ ] AC21: No `historico/page.tsx`, atualizar estilo dos botões Anterior/Próximo para usar o mesmo componente `Pagination` do AC1 (consistência visual)
- [ ] AC22: Se não usar componente compartilhado, pelo menos corrigir: `disabled:opacity-30` → `disabled:opacity-50` e adicionar `disabled:cursor-not-allowed`
- [ ] AC23: Aumentar tamanho do texto: `text-sm` → `text-base` e padding: `px-3 py-1` → `px-4 py-2`
- [ ] AC24: Adicionar `font-medium` para melhorar legibilidade
- [ ] AC25: Testar em tema Light e Dark — botões devem ser legíveis em ambos

### Bloco 6: Testes

- [ ] AC26: Teste de `Pagination` component: renderiza, navega, reseta, persiste pageSize
- [ ] AC27: Teste de `SearchResults` com paginação: 100 items → mostra 20, navega para página 2 → mostra items 21-40
- [ ] AC28: Teste que botões Excel/PDF/Sheets estão visíveis no viewport sem scroll (dentro da sticky bar)
- [ ] AC29: Teste de acessibilidade: `Pagination` tem `aria-label`, `aria-current="page"`, botões disabled com `aria-disabled`
- [ ] AC30: Teste de histórico: botão "Próximo" é visível e legível (contrast ratio check)

## Arquivos Afetados

- `frontend/components/ui/Pagination.tsx` (novo — componente reutilizável)
- `frontend/app/buscar/components/SearchResults.tsx` (paginação + sticky bar)
- `frontend/app/buscar/components/LicitacoesPreview.tsx` (receber slice paginado)
- `frontend/app/buscar/page.tsx` (state de paginação, query param)
- `frontend/components/GoogleSheetsExportButton.tsx` (fix error handling + re-auth flow)
- `frontend/app/api/export/google-sheets/route.ts` (verificar proxy)
- `backend/routes/export_sheets.py` (verificar OAuth flow)
- `backend/oauth.py` (verificar `get_user_google_token`)
- `frontend/app/historico/page.tsx` (fix botões, usar Pagination)
- `frontend/__tests__/components/Pagination.test.tsx` (novo)
- `frontend/__tests__/components/SearchResults-pagination.test.tsx` (novo)
- `frontend/__tests__/components/GoogleSheetsExport-errors.test.tsx` (novo)

## Decisão Técnica: Client-side vs Server-side

**Client-side pagination** (recomendado para fase 1):
- Backend já retorna todos os resultados filtrados (50-200 items)
- Navegação instantânea entre páginas (sem HTTP request)
- Simples de implementar (slice no array existente)
- Params `pagina`/`itens_por_pagina` do schema ficam reservados para fase 2

**Server-side (fase 2, se necessário)**:
- Só se result sets ultrapassarem 500+ items regularmente
- Backend já tem schema preparado (`pagina`, `itens_por_pagina`)

## Notas

- O componente `Pagination` deve ser genérico o suficiente para reusar em `/historico`, `/pipeline`, `/mensagens`
- Não alterar a lógica de blur/paywall para free tier — paginação é independente
- Excel/PDF/Sheets geram arquivo com TODOS os resultados (não apenas a página atual)
- Google Sheets depende de OAuth Google — pode precisar de re-autorização se credenciais expiraram
- Fluxo OAuth: `GET /auth/google` → Google consent → callback → token salvo no Supabase → usado em export
