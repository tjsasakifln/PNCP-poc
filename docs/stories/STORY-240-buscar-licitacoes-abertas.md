# STORY-240: Buscar Licitações Abertas (Paradigma "Aberto Agora")

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-240 |
| **Priority** | P0 (GTM-critical) |
| **Sprint** | Sprint 2 |
| **Estimate** | 10h |
| **Depends on** | STORY-241 (modalidades corretas primeiro) |
| **Blocks** | STORY-245 (curadoria acionável depende de dados limpos) |

## Problema
Hoje o SmartLic busca por **data de publicação** (dataInicial/dataFinal). Isso retorna licitações que foram publicadas no período, mas muitas já estão **encerradas**. O usuário quer ver **licitações abertas para enviar proposta AGORA**, não licitações publicadas recentemente.

## Solução
Mudar o paradigma de busca: ampliar a janela de publicação para 180 dias e filtrar client-side pelo campo `dataEncerramentoProposta > hoje`. O resultado final mostra apenas licitações com prazo de proposta ainda em aberto.

## Investigação Técnica

### API PNCP
- **Endpoint:** `GET /contratacoes/publicacao` (único endpoint de busca disponível)
- **Parâmetros de data:** `dataInicial`, `dataFinal` — referem-se à data de PUBLICAÇÃO, não de abertura/encerramento
- **Campo de encerramento:** `dataEncerramentoProposta` — presente na resposta, usado para filtro client-side
- **Campo de abertura:** `dataAberturaProposta` — presente na resposta
- **Campo `situacaoCompra`:** Marcado como **unreliable** no codebase (`schemas.py:329-337`), NÃO usar para filtragem primária
- **Nota:** `pncp_client.py:181` já monta a URL com `/contratacoes/publicacao`

### Arquivos a Modificar

| Arquivo | Linhas | Mudança |
|---------|--------|---------|
| `backend/pncp_client.py` | 166-176 | Novo parâmetro `busca_abertas: bool` para ampliar janela de data |
| `backend/pncp_client.py` | 370-410 | `fetch_all()` — lógica de date range quando modo "abertas" |
| `backend/filter.py` | 796-810 | Novo filtro `filtrar_por_prazo_aberto()` — rejeita `dataEncerramentoProposta <= hoje` |
| `backend/schemas.py` | 245-260 | `BuscaRequest` — novo campo `modo_busca: "publicacao" \| "abertas"`, default="abertas" |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | 193-201 | Ampliar default de data para 180 dias quando modo=abertas |
| `frontend/app/buscar/hooks/useSearch.ts` | payload building | Enviar `modo_busca` no POST body |
| `frontend/app/buscar/page.tsx` | UI label | Atualizar label de "Período de publicação" para "Licitações abertas para proposta" |

### Riscos e Mitigações
- **Volume de dados:** 180 dias × múltiplas UFs × múltiplas modalidades = muitos registros. **Mitigação:** O filtro client-side `dataEncerramentoProposta > hoje` elimina a maioria. Manter chunking de 30 dias existente.
- **PNCP rate limiting:** Mais chunks = mais requests. **Mitigação:** Respeitar rate limit existente (100ms entre requests). Indicar progresso real via SSE.
- **Backward compatibility:** Campo `modo_busca` é Optional com default, não quebra API existente.

## Acceptance Criteria

### Backend
- [ ] **AC1:** `BuscaRequest.modo_busca` aceita `"publicacao"` (legado) ou `"abertas"` (novo padrão). Default: `"abertas"`.
- [ ] **AC2:** Quando `modo_busca="abertas"`, o backend calcula `dataInicial = hoje - 180 dias` e `dataFinal = hoje`, ignorando as datas enviadas pelo frontend.
- [ ] **AC3:** Novo filtro `filtrar_por_prazo_aberto()` em `filter.py` rejeita licitações onde `dataEncerramentoProposta <= datetime.now()`. Logs rejection reason.
- [ ] **AC4:** Filtro `filtrar_por_prazo_aberto()` é aplicado ANTES do filtro de keywords (fail-fast: elimina encerradas antes de processamento pesado).
- [ ] **AC5:** Cada licitação no resultado inclui `dias_restantes` (int) calculado como `(dataEncerramentoProposta - hoje).days`.
- [ ] **AC6:** Testes unitários para `filtrar_por_prazo_aberto()`: licitação encerrada ontem → rejeitada; encerra amanhã → aceita; sem data de encerramento → aceita (campo ausente não deve bloquear).

### Frontend
- [ ] **AC7:** `useSearchFilters` default de data é 180 dias quando modo=abertas. Seletor de data fica oculto/desabilitado neste modo.
- [ ] **AC8:** Label muda de "Período de publicação" para contextual: modo abertas → "Mostrando licitações abertas para proposta"; modo publicação → "Período de publicação".
- [ ] **AC9:** Card de resultado mostra badge com dias restantes: verde (>7d), amarelo (3-7d), vermelho (<3d), cinza (sem data).
- [ ] **AC10:** Testes para `useSearchFilters` verificam default de 180 dias e label condicional.

### Regressão
- [ ] **AC11:** Modo `"publicacao"` continua funcionando exatamente como antes (backward compatible).
- [ ] **AC12:** Testes existentes de busca passam sem modificação no modo publicação.

## Definition of Done
- Todos os ACs checked
- `pytest` backend sem regressões vs baseline (21 falhas pré-existentes)
- `npm test` frontend sem regressões vs baseline (70 falhas pré-existentes)
- TypeScript clean (`npx tsc --noEmit`)
