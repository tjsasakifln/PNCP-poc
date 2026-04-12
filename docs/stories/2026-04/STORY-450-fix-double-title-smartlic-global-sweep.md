# STORY-450: Fix — Double Title `| SmartLic` Global Sweep

**Priority:** P1 (bug SEO — ~30 páginas indexáveis com título duplicado no SERP)
**Effort:** S (< 1 dia — patch mecânico, sem lógica nova)
**Squad:** @dev
**Status:** Draft
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Hotfix paralelo

---

## Contexto

O `root layout` (`frontend/app/layout.tsx`) define um template de título:

```ts
title: {
  default: 'SmartLic — Filtre Licitações por Viabilidade Real',
  template: '%s | SmartLic',
}
```

Quando uma página filha retorna `title: 'Minha Página | SmartLic'`, o Next.js
aplica o template e gera `'Minha Página | SmartLic | SmartLic'` — duplicando o
sufixo no `<title>` HTML e no SERP do Google.

**Impacto confirmado em produção (2026-04-12):**
- `/observatorio` → `"Observatório de Licitações | SmartLic | SmartLic"` (48 chars)
- `/indice-municipal` → `"Índice de Transparência Municipal em Compras Públicas | SmartLic | SmartLic"` (75 chars)
- `/licitacoes/informatica` → `"Licitações de Hardware e Equipamentos de TI | SmartLic | SmartLic"` (65 chars)

Parcialmente corrigido em commits `8b4d32c2` (indice-municipal) e `315cd9a3`
(observatorio + calculadora/embed). Restam **21 arquivos** com o mesmo padrão.

---

## Acceptance Criteria

### AC1: Remover `| SmartLic` hardcoded dos títulos de metadata

Para cada arquivo listado na seção **Arquivos Afetados**, remover o sufixo
`| SmartLic` (e variantes `| SmartLic.tech`) das strings de título na função
`generateMetadata()` ou no objeto `export const metadata`.

- [x] Apenas o sufixo é removido — o restante do título permanece intacto
- [x] Títulos dinâmicos com template string também corrigidos
- [x] `openGraph.title` e `twitter.title` NÃO devem ser alterados (já são
  absolute — não sofrem do bug e precisam do nome da marca para compartilhamento)
- [x] `rss.xml/route.ts` NÃO deve ser alterado (não é page metadata)

### AC2: Não introduzir regressão nos títulos já corretos

- [x] Páginas que NÃO têm `| SmartLic` hardcoded permanecem intactas
- [x] Páginas que usam `title: { absolute: '...' }` permanecem intactas

### AC3: TypeScript e testes passando

- [x] `npx tsc --noEmit` sem erros em `frontend/`
- [x] `npm test` sem novas falhas

### AC4: Verificação spot-check pós-deploy

Buscar no HTML raw de 3 páginas que o título aparece apenas com 1x `SmartLic`:

```bash
curl -s https://smartlic.tech/observatorio | grep -o '<title>[^<]*</title>'
# Esperado: <title>Observatório de Licitações | SmartLic</title>

curl -s https://smartlic.tech/licitacoes/informatica | grep -o '<title>[^<]*</title>'
# Esperado: <title>Licitações de Hardware e Equipamentos de TI | SmartLic</title>

curl -s https://smartlic.tech/glossario | grep -o '<title>[^<]*</title>'
# Esperado: <title>Glossário de Licitações: 50 Termos Essenciais | SmartLic</title>
```

---

## Arquivos Afetados (21 arquivos restantes)

```
frontend/app/alertas-publicos/[setor]/[uf]/page.tsx
frontend/app/alertas-publicos/page.tsx
frontend/app/analise/[hash]/page.tsx
frontend/app/casos/[slug]/page.tsx
frontend/app/casos/page.tsx
frontend/app/compliance/[cnpj]/page.tsx
frontend/app/compliance/page.tsx
frontend/app/dados/page.tsx
frontend/app/estatisticas/embed/page.tsx
frontend/app/estatisticas/page.tsx
frontend/app/fornecedores/[cnpj]/page.tsx
frontend/app/glossario/[termo]/page.tsx
frontend/app/glossario/page.tsx
frontend/app/itens/[catmat]/page.tsx
frontend/app/itens/page.tsx
frontend/app/licitacoes/[setor]/page.tsx
frontend/app/licitacoes/page.tsx
frontend/app/municipios/[slug]/page.tsx
frontend/app/municipios/page.tsx
frontend/app/perguntas/[slug]/page.tsx
frontend/app/perguntas/page.tsx
```

**Comando para encontrar ocorrências:**
```bash
grep -rn "title.*| SmartLic\b" frontend/app --include="*.tsx" --include="*.ts" \
  | grep -v "__tests__\|test\|spec\|rss.xml\|openGraph\|twitter\|// \|iframe\|<title\|label\|aria\|absolute:"
```

---

## Escopo

### IN
- Remover `| SmartLic` de strings de `title` em `generateMetadata()` e `export const metadata`
- Cobrir os 21 arquivos listados acima

### OUT
- NÃO alterar `openGraph.title`, `twitter.title`, `rss.xml`
- NÃO alterar páginas autenticadas (dashboard, pipeline, conta) — não são indexáveis
- NÃO alterar comprimentos de título ou descrição (issue separada)
- NÃO criar novos testes — o padrão é trivial e coberto pelo spot-check AC4

---

## Dependências

- Nenhuma — patch independente

---

## Risco

**Baixo.** A mudança é puramente de string em metadata; não altera lógica, componentes
ou comportamento em runtime. O template do root layout já está em produção e funcionando
corretamente para as páginas corrigidas em `8b4d32c2` + `315cd9a3`.

---

## Dev Notes

Forma eficiente de aplicar o fix em batch (revisar manualmente cada arquivo após):

```bash
# Preview (sem alterar)
grep -rn "| SmartLic'" frontend/app --include="*.tsx" --include="*.ts" \
  | grep -v "openGraph\|twitter\|rss\|__tests__"

# Aplicar com sed (revisar diff antes de commitar)
# sed -i "s/ | SmartLic'$/'/g" arquivo.tsx
```

Atenção: alguns arquivos têm múltiplas ocorrências (ex: `licitacoes/[setor]/page.tsx`
tem 3 title branches — todas precisam ser corrigidas).

---

## File List

- [ ] `frontend/app/alertas-publicos/[setor]/[uf]/page.tsx`
- [ ] `frontend/app/alertas-publicos/page.tsx`
- [ ] `frontend/app/analise/[hash]/page.tsx`
- [ ] `frontend/app/casos/[slug]/page.tsx`
- [ ] `frontend/app/casos/page.tsx`
- [ ] `frontend/app/compliance/[cnpj]/page.tsx`
- [ ] `frontend/app/compliance/page.tsx`
- [ ] `frontend/app/dados/page.tsx`
- [ ] `frontend/app/estatisticas/embed/page.tsx`
- [ ] `frontend/app/estatisticas/page.tsx`
- [ ] `frontend/app/fornecedores/[cnpj]/page.tsx`
- [ ] `frontend/app/glossario/[termo]/page.tsx`
- [ ] `frontend/app/glossario/page.tsx`
- [ ] `frontend/app/itens/[catmat]/page.tsx`
- [ ] `frontend/app/itens/page.tsx`
- [ ] `frontend/app/licitacoes/[setor]/page.tsx`
- [ ] `frontend/app/licitacoes/page.tsx`
- [ ] `frontend/app/municipios/[slug]/page.tsx`
- [ ] `frontend/app/municipios/page.tsx`
- [ ] `frontend/app/perguntas/[slug]/page.tsx`
- [ ] `frontend/app/perguntas/page.tsx`

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-12 | @sm | Story criada — bug detectado via validação Playwright em produção |
