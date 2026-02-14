# STORY-246: Experiência One-Click — Redução de Carga Cognitiva

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-246 |
| **Priority** | P1 |
| **Sprint** | Sprint 3 |
| **Estimate** | 8h |
| **Depends on** | STORY-240 (modo "abertas" simplifica escolha de data), STORY-243 (nomes claros de setor) |
| **Blocks** | Nenhuma |

## Problema
Hoje o usuário precisa: (1) escolher setor, (2) selecionar UFs, (3) definir datas, (4) opcionalmente configurar filtros avançados, (5) clicar buscar. São 5 decisões antes de ver qualquer resultado. Para um novo usuário, isso é intimidante.

## Solução
Criar experiência "one-click": usuário escolhe setor e clica "Buscar" — UFs, datas e modalidades usam defaults inteligentes. Filtros avançados ficam disponíveis mas pré-configurados com valores sensatos.

## Investigação Técnica

### Defaults Atuais vs Propostos

| Filtro | Default Atual | Default Proposto | Justificativa |
|--------|--------------|------------------|---------------|
| UFs | SC, PR, RS (hardcoded, line 191) | **Todas as UFs** (27) | Maximizar cobertura; usuário pode restringir depois |
| Datas | Últimos 7 dias (line 193-201) | **180 dias** (via STORY-240 modo abertas) | Paradigma "abertas agora" |
| Status | recebendo_proposta (line 168) | Mantém | Correto para modo "abertas" |
| Modalidades | [] vazio (line 169) | `[4, 5, 6, 7]` (via STORY-241) | Modalidades competitivas |
| Setor | vestuario (line 161) | **Setor do perfil do usuário** (se logado) ou vestuario | Personalização |

### Fluxo Simplificado

```
ANTES (5 passos):
1. Escolher setor ← obrigatório
2. Selecionar UFs ← obrigatório
3. Definir datas ← obrigatório
4. Configurar filtros ← opcional
5. Clicar Buscar

DEPOIS (1-2 passos):
1. Escolher setor (ou usar setor do perfil) ← obrigatório
2. Clicar Buscar ← usa defaults inteligentes
   → UFs: todas | Datas: 180d | Modalidades: competitivas
   → Filtros avançados disponíveis em accordion colapsado
```

### Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/buscar/hooks/useSearchFilters.ts:161` | Default setorId = setor do perfil (via useAuth) |
| `frontend/app/buscar/hooks/useSearchFilters.ts:190-192` | Default UFs = todas (new Set(UFS)) |
| `frontend/app/buscar/hooks/useSearchFilters.ts:169` | Default modalidades = [4,5,6,7] |
| `frontend/app/buscar/page.tsx` | UI: Setor + botão Buscar prominentes. UFs/Datas em accordion colapsado "Personalizar busca" |
| `frontend/app/buscar/components/FilterPanel.tsx` | Reorganizar: setor no topo, depois CTA, depois accordion com UFs/Datas/Avançados |

### Considerações UX
- Primeiro uso: mostrar tooltip "Buscando em todo o Brasil por padrão. Personalize se necessário."
- Usuário logado com setor no perfil: pre-selecionar setor automaticamente
- Badge "defaults inteligentes ativos" quando accordion está colapsado

## Acceptance Criteria

### Frontend — Defaults
- [x] **AC1:** Default de UFs = todas as 27 UFs (novo usuário ou não-logado).
- [x] **AC2:** Default de modalidades = [4, 5, 6, 7] (competitivas).
- [x] **AC3:** Se usuário logado com setor no perfil, pre-seleciona o setor automaticamente.
- [x] **AC4:** Default de datas = 180 dias (alinhado com STORY-240 modo abertas).

### Frontend — Layout
- [x] **AC5:** Setor selector e botão "Buscar" são os elementos mais prominentes da página.
- [x] **AC6:** UFs, datas e filtros avançados ficam em accordion "Personalizar busca" — colapsado por padrão para novos usuários.
- [x] **AC7:** Accordion mantém estado no localStorage (se usuário abriu, permanece aberto em visitas futuras).
- [x] **AC8:** Badge informativo quando accordion está colapsado: "Buscando em 27 estados, licitações abertas".

### Frontend — Feedback
- [x] **AC9:** Ao clicar Buscar com defaults, progresso mostra "Buscando em todo o Brasil..." (não lista 27 UFs).
- [x] **AC10:** Resultado mostra resumo dos filtros ativos no topo: "27 UFs | Últimos 180 dias | Modalidades competitivas".

### Regressão
- [x] **AC11:** Usuários que já tinham UFs selecionadas via URL params continuam funcionando (URL params override defaults).
- [x] **AC12:** Busca com filtros personalizados funciona igual ao antes.
- [x] **AC13:** Testes existentes de busca atualizados para novos defaults.

## Definition of Done
- Todos os ACs checked
- `npm test` sem regressões
- TypeScript clean
- Testado manualmente: novo usuário → 1 clique → resultados
