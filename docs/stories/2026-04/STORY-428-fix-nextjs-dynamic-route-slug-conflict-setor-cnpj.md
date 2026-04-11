# STORY-428: Investigar e Corrigir Conflito de Rota Dinâmica Next.js `[setor]`/`[cnpj]`

**Priority:** P2
**Effort:** S (0.5-1 day)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
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
- [ ] Listar todos os diretórios com `[param]` em `frontend/app/` via `find frontend/app -type d -name "[*]"`
- [ ] Para cada nível de roteamento, verificar se há dois params diferentes no mesmo nível (ex: `[setor]` e `[cnpj]` como irmãos sob o mesmo pai)
- [ ] Verificar especificamente:
  - `app/blog/` — `[slug]` vs outros params irmãos
  - `app/contratos/` — `[setor]` e `orgao/[cnpj]` em sub-níveis
  - `app/alertas-publicos/[setor]/[uf]` — params aninhados
- [ ] Documentar resultado no Dev Notes: "conflito encontrado em X / nenhum conflito encontrado"

### AC2: Reproduzir o erro (se conflito encontrado)
- [ ] Navegar para a rota conflitante via browser MCP
- [ ] Confirmar que gera InvariantError no console do Next.js
- [ ] Screenshot do erro no Sentry / console

### AC3: Corrigir o conflito
- Se conflito encontrado em AC1:
  - [ ] Renomear um dos params para resolver a ambiguidade (ex: `[cnpjSlug]` ou mover para sub-rota estática)
  - [ ] Alternativa: usar route groups `(...)` para separar contextos sem afetar URL pública
  - [ ] Atualizar links internos / `generateStaticParams` se rota renomeada
- [ ] Confirmar zero erros `InvariantError` no console após fix

### AC4: Testes
- [ ] E2E test (`frontend/e2e-tests/`) cobrindo as rotas afetadas — acesso direto deve retornar 200
- [ ] `npm run build` passa sem warnings de rota conflitante

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

- [ ] AC1 documentado (conflito identificado ou confirmado ausente)
- [ ] Se conflito: zero `InvariantError` de roteamento no Sentry por 24h após fix
- [ ] Se não encontrado: story fechada com nota explicando origem do Sentry alert

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — InvariantError de rota dinâmica identificado em varredura Sentry pós-EPIC-INCIDENT-2026-04-10 |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 7.5/10. GO (condicionado a AC1 confirmar conflito real). Status: Draft → Ready. |
