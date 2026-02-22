# UX-346 — Pagina de Busca: Sobrecarga Cognitiva no Primeiro Uso

**Tipo:** UX / Onboarding
**Prioridade:** Alta (afeta retencao de trial)
**Criada:** 2026-02-22
**Status:** Concluida
**Origem:** Teste de primeiro uso real em producao (UX Expert audit)

---

## Problema

Ao acessar `/buscar` pela primeira vez, o usuario ve:

1. **27 estados selecionados** (todos pressed/azul) — grid de 27 botoes ocupando 3 linhas
2. **"Personalizar busca" expandido** — exibindo UFs, status, modalidades, valor
3. **"Filtros Avancados" expandido** — mostrando status, modalidades (4 checkboxes), slider de valor
4. **Resumo informacional** — "Mostrando licitacoes abertas para proposta / Buscando nos ultimos 10 dias"

**Resultado visual:** A pagina tem ~4 screenfuls de opcoes ANTES do botao "Buscar". O usuario precisa scrollar para entender tudo.

### Contagem de elementos interativos visiveis no primeiro load:
- 1 dropdown de setor
- 2 tabs (Setor / Termos Especificos)
- 5 botoes de regiao (Norte, Nordeste, etc)
- 27 botoes de UF
- 2 botoes (Selecionar todos, Limpar)
- 4 radio buttons (Abertas, Em Julgamento, Encerradas, Todas)
- 4 checkboxes de modalidade + "Mais opcoes"
- 2 sliders de valor
- 6 quick value buttons
- 2 inputs de valor (min/max)
- **= ~55 elementos interativos visiveis simultaneamente**

### Comparacao com padroes de mercado:
- Google: 1 campo de busca
- Comprasnet: dropdown + campo + botao (3 elementos)
- Licitanet: 3 campos + botao (4 elementos)

### Impacto

- Usuario novo fica paralisado: "por onde comeco?"
- Choice overload: pesquisas mostram que >7 opcoes reduzem decisao
- Mobile: situacao ainda pior — precisa scrollar muito
- O setor ja esta pre-selecionado (bom!), mas o resto esta "explodido"

---

## Solucao

### Abordagem: Progressive Disclosure — mostrar o minimo, revelar sob demanda

### Criterios de Aceitacao

#### Estado Inicial (First Paint)

- [x] **AC1:** "Personalizar busca" inicia COLAPSADO para usuarios que NUNCA buscaram
  - Se usuario ja fez busca anterior, manter estado (expandido com ultimos filtros)
  - Usar localStorage para persistir preferencia
  - **Impl:** `smartlic-has-searched` localStorage flag; first-time ignores `smartlic-customize-open`
- [x] **AC2:** "Filtros Avancados" inicia COLAPSADO por padrao (ja e hoje, verificar)
  - **Verificado:** `advancedFiltersOpen` defaults to `false` via localStorage fallback in useSearchFilters.ts
- [x] **AC3:** Resumo compacto abaixo do botao buscar:
  - "27 estados • Abertas • 4 modalidades • Ultimos 10 dias"
  - Clicavel para expandir "Personalizar busca"
  - **Impl:** `data-testid="compact-summary"` button below search button, onclick expands accordion

#### Simplificacao Visual

- [x] **AC4:** Quando colapsado, "Personalizar busca" mostra summary inline:
  - "27 estados | Abertas | 4 modalidades | R$ 0 - Sem limite"
  - Icone de seta para expandir
  - **Impl:** `compactSummary` computed string with UFs/status/modalidades/period
- [x] **AC5:** Primeiro uso: mostrar tooltip ou destaque sutil:
  - "Dica: selecione seu setor e clique Buscar. Personalize depois se quiser."
  - Desaparece apos primeira busca ou dismiss
  - **Impl:** `data-testid="first-use-tip"` with dismiss button; cleared on search or explicit dismiss

#### Botao de Busca

- [x] **AC6:** Botao "Buscar [Setor]" sempre visivel sem scroll (sticky se necessario em mobile)
  - **Verificado:** `sticky bottom-4` on mobile already in place
- [x] **AC7:** Remover footer da pagina de busca (ou move-lo para apos resultados) — hoje o footer aparece abaixo dos filtros antes de qualquer busca, desperdicando viewport
  - **Impl:** Footer has `hidden` class when `!search.result`

#### Testes

- [x] **AC8:** Teste: primeiro acesso tem "Personalizar busca" colapsado
- [x] **AC9:** Teste: apos busca, "Personalizar busca" respeita ultimo estado
- [x] **AC10:** Teste: resumo compacto mostra contagem correta de UFs/modalidades
- [x] **AC11:** Nenhum teste existente quebra (40 fail / 2229 pass = pre-existing baseline)

---

## Arquivos Envolvidos

### Modificar
- `frontend/app/buscar/page.tsx` — AC1 (first-use detection), AC5 (tip state), AC7 (footer visibility)
- `frontend/app/buscar/components/SearchForm.tsx` — AC3/AC4 (compact summary), AC5 (first-use tip)

### Testes
- `frontend/__tests__/search-first-use.test.tsx` — **NOVO**: 15 tests (all pass)

---

## Wireframe (ASCII)

### Antes (hoje):
```
[Setor ▾] [Termos Especificos]
[Vestuario e Uniformes        ▾]
[=== Buscar Vestuario e Uniformes ===]
▼ Personalizar busca                    ← EXPANDIDO
  Estados: [Norte✓] [Nordeste✓] ...
  [AC] [AL] [AP] [AM] [BA] ...         ← 27 botoes
  [CE] [DF] [ES] [GO] [MA] ...
  [MT] [MS] [MG] [PA] [PB] ...
  ℹ Mostrando licitacoes abertas...
  ▼ Filtros Avancados                   ← TAMBEM EXPANDIDO
    Status: (•) Abertas ( ) Julgamento...
    Modalidade: [✓] Concorrencia...
    Valor: [slider] R$0 — Sem limite
--- FOOTER ---                          ← footer aparece aqui!
```

### Depois (implementado):
```
[Setor ▾] [Termos Especificos]
[Vestuario e Uniformes        ▾]
💡 Dica: selecione seu setor e clique Buscar. Personalize depois se quiser. [x]
[=== Buscar Vestuario e Uniformes ===]
  Todo o Brasil • Abertas • Ultimos 10 dias
▸ Personalizar busca                    ← COLAPSADO
                                        ← Footer oculto ate resultados
```

---

## Estimativa

- **Complexidade:** Baixa-Media (logica de estado persistido + CSS collapse)
- **Risco:** Baixo (nenhuma funcionalidade removida, so escondida)
- **Dependencias:** Nenhuma
