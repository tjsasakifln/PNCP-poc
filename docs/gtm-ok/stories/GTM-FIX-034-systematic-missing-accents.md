# GTM-FIX-034: Acentos faltando sistematicamente em toda a UI

**Priority:** P1 (credibilidade profissional comprometida)
**Effort:** S (2-3h)
**Origin:** Teste de produção manual 2026-02-18
**Status:** PENDENTE
**Assignee:** @dev
**Tracks:** Frontend (4 ACs), Tests (2 ACs)

---

## Problem Statement

Pelo menos **20 instâncias** de textos em português sem acentos na UI de produção. Para um produto B2B brasileiro a R$1.999/mês, isso causa percepção de amadorismo e erode confiança.

### Inventário Completo de Acentos Faltando

#### Página de Busca (`/buscar`)

| Local | Texto Atual | Texto Correto |
|-------|-------------|---------------|
| Info banner | "Buscando nos últimos 15 dias" | "Buscando nos últimos **10** dias" (também é bug de copy) |
| Accordion | "Filtragem por Localizacao" | "Filtragem por Localiza**ção**" |
| Accordion | "Filtros Avancados" | "Filtros Avan**ç**ados" |
| Label | "Status da Licitacao:" | "Status da Licita**ção**:" |
| Dica | "licitacoes que ainda aceitam propostas" | "licita**ções** que ainda aceitam propostas" |
| Tooltip | "licitacoes abertas para enviar propostas" | "licita**ções** abertas para enviar propostas" |
| Label | "Modalidade de Contratacao:" | "Modalidade de Contrata**ção**:" |
| Checkbox | "Concorrencia Eletronica" | "Concorr**ê**ncia Eletr**ô**nica" |
| Checkbox | "Concorrencia Presencial" | "Concorr**ê**ncia Presencial" |
| Checkbox | "Pregao Eletronico" | "Preg**ão** Eletr**ô**nico" |
| Checkbox | "Pregao Presencial" | "Preg**ão** Presencial" |
| Button | "Mais opcoes" | "Mais op**ções**" |
| Label | "Minimo:" | "M**í**nimo:" |
| Label | "Maximo:" | "M**á**ximo:" |
| Button | "Ate 50k" | "At**é** 50k" |
| Hint | "Deixe 'Maximo' vazio..." | "Deixe 'M**á**ximo' vazio..." |
| Slider | "Valor minimo" / "Valor maximo" | "Valor m**í**nimo" / "Valor m**á**ximo" |

#### Página de Signup (`/signup`)

| Local | Texto Atual | Texto Correto |
|-------|-------------|---------------|
| Link | "Ja tem conta?" | "J**á** tem conta?" |
| Placeholder | "Min. 8 caracteres, 1 maiuscula, 1 numero" | "Min. 8 caracteres, 1 mai**ú**scula, 1 n**ú**mero" |
| Validação | "Minimo 8 caracteres" | "M**í**nimo 8 caracteres" |
| Validação | "1 letra maiuscula" | "1 letra mai**ú**scula" |
| Validação | "As senhas nao coincidem" | "As senhas n**ão** coincidem" |

---

## Acceptance Criteria

### Frontend

- [ ] **AC1**: Corrigir 9 labels de modalidade em `components/ModalidadeFilter.tsx:33-57` + botão "opcoes" na linha 253
- [ ] **AC2**: Corrigir labels em `components/StatusFilter.tsx:18,25,56-57,68,83` (incluindo aria-label e type name)
- [ ] **AC3**: Corrigir 7 strings de validação em `app/signup/page.tsx:108,113,332,365,368,426,442`
- [ ] **AC4**: Fazer grep global por padrões sem acento (`Licitacao`, `opcoes`, `Pregao`, `Concorrencia`, `Avancad`, `Localizacao`, `Contratacao`, `Minimo`, `Maximo`, `maiuscula`, `numero`) e corrigir qualquer instância adicional em todo o frontend

### Tests

- [ ] **AC5**: Atualizar assertions em `__tests__/pages/SignupPage.test.tsx` (linhas 78, 112, 160, 201, 207-208, 215, 223, 411, 418, 435) para refletir strings corrigidas
- [ ] **AC6**: Adicionar smoke test que valide que labels de filtro contêm acentos corretos (previne regressão)

---

## Technical Notes

- As strings de modalidade estão definidas em `ModalidadeFilter.tsx:33-57` como dados estáticos — são labels de display, não vindos do backend
- O radiogroup `aria-label` "Status da licitacao" em `StatusFilter.tsx:18,68` também deve ser corrigido para acessibilidade
- A validação de signup está diretamente em `signup/page.tsx` (não usa lib externa de validação)
- Testes em `SignupPage.test.tsx` fazem assertions em strings sem acento (linhas 78, 112, 160, 201, 207-208, 215, 223, 411, 418, 435) — devem ser atualizados junto

## Arquivos Exatos

| Arquivo | Linhas | Strings afetadas |
|---------|--------|------------------|
| `frontend/components/ModalidadeFilter.tsx` | 33-57, 253 | 9 modalidades + "Mais opcoes" |
| `frontend/components/StatusFilter.tsx` | 18, 25, 56-57, 68, 83 | "Licitacao", type `StatusLicitacao` |
| `frontend/app/signup/page.tsx` | 108, 113, 332, 365, 368, 426, 442 | 7 validações + "Ja tem conta" |
| `frontend/__tests__/pages/SignupPage.test.tsx` | 78, 112, 160, 201, 207-208, 215, 223, 411, 418, 435 | Assertions a atualizar |
| `frontend/app/buscar/components/SearchForm.tsx` | 491 | "15 dias" (cross-ref GTM-FIX-036) |
