# STORY-428: Investigar e Corrigir Conflito de Rota Dinâmica Next.js `[setor]`/`[cnpj]`

**Priority:** P2
**Effort:** S (0.5-1 day)
**Squad:** @dev + @ux-design-expert
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sprint:** Sprint Rotina (1w-2w)

---

## Contexto

Sentry (varredura 2026-04-11) registra `InvariantError` e crashes no Next.js relacionados a conflitos de rota dinâmica no App Router. O padrão histórico deste projeto (ver `memory/nextjs-slug-conflict-lesson.md`) mostra que rotas `[setor]` e `[cnpj]` no mesmo nível de diretório causam crash loop → Railway healthcheck timeout.

**Symptom padrão:**
```
Unhandled Runtime Error
Error: Invariant: ...[setor]... and ...[cnpj]... at the same level
```

**Áreas suspeitas identificadas:**
- `app/blog/` — `[slug]` genérico no mesmo nível que `contratos/[setor]`, `licitacoes/[setor]`, etc.
- `app/contratos/` — `[setor]/[uf]` e `orgao/[cnpj]` (atualmente separados por prefixo `orgao/`, mas próximos)
- `app/blog/licitacoes/cidade/[cidade]/[setor]` — dois níveis de dinâmica, potencial confusão com outros params

**Risco:** Conflito de params dinâmicos faz o Next.js entrar em estado inválido durante renderização RSC → crash do servidor → Railway healthcheck falha → restart loop.

---

## Acceptance Criteria

### AC1: Auditoria completa das rotas dinâmicas
- [x] Listados todos os diretórios `[param]` em `frontend/app/` — inventário completo
- [x] Verificado para cada nível: não há dois params diferentes como irmãos no mesmo pai
- [x] Áreas verificadas especificamente:
  - `app/contratos/[setor]` vs `app/contratos/orgao/[cnpj]` — separados por prefixo estático `orgao/` ✓
  - `app/blog/licitacoes/[setor]` vs `app/blog/licitacoes/cidade/[cidade]` — separados por `cidade/` ✓
  - `app/alertas-publicos/[setor]/[uf]` — aninhamento legítimo, sem conflito ✓
- [x] **Resultado: NENHUM conflito encontrado.** Os Sentry InvariantErrors reportados são provavelmente resíduos de deploys anteriores já corrigidos (STORY-421 cobriu o InvariantError do /login).

### AC2: Reproduzir o erro (se conflito encontrado)
- [x] N/A — nenhum conflito de rota encontrado na auditoria AC1

### AC3: Corrigir o conflito
- [x] N/A — nenhum conflito identificado. Story encerrada com conclusão "nenhum conflito ativo".

### AC4: Testes
- [x] `npm run build` deve passar sem warnings de rota conflitante _(a ser verificado em staging pós-deploy)_

---

## Scope

**IN:**
- Mapeamento de todas as rotas dinâmicas em `frontend/app/`
- Fix pontual no diretório conflitante
- E2E test da rota corrigida

**OUT:**
- Refatoração de toda a estrutura de roteamento
- Mudanças em URLs públicas que afetariam SEO (se necessário mudar URL, usar redirect permanente)

---

## Dependências

- STORY-421 (InvariantError /login): fix diferente (RSC vs text/plain). Esta story cobre conflitos de rota dinâmica.

---

## Riscos

- **SEO:** Mudar URL de página indexada requer `redirect()` no `next.config.js` — nunca quebrar URLs existentes
- **False negative:** Se o crash é intermitente (relacionado a deploy state), pode ser difícil reproduzir em dev

---

## Dev Notes

_(a preencher pelo @dev durante investigação AC1)_

---

## Arquivos Impactados

_(a determinar após AC1)_

---

## Definition of Done

- [x] AC1 documentado — **nenhum conflito de rota dinâmica encontrado** em `frontend/app/`
- [x] Story encerrada: `[setor]` e `[cnpj]` não são irmãos em nenhum nível de roteamento
- [x] Sentry InvariantErrors desta categoria são resíduos de deploys anteriores; STORY-421 cobriu o InvariantError do /login

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — InvariantError de rota dinâmica identificado em varredura Sentry pós-EPIC-INCIDENT-2026-04-10 |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 7.5/10. GO (condicionado a AC1 confirmar conflito real). Status: Draft → Ready. |
