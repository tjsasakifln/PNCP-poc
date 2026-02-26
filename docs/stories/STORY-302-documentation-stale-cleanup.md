# STORY-302: Documentation + Stale Cleanup

**Sprint:** 3 — Make It Competitive
**Size:** S (2-4h)
**Root Cause:** Track E (Business Model Audit)

## Contexto

Track E encontrou documentação stale em vários pontos:
1. `CLAUDE.md` referencia pricing R$1,999 (correto é R$397 após STORY-277)
2. `PRD.md` tem specs desatualizadas
3. Código morto e configs stale identificados em Track D
4. Snapshots de teste desatualizados

Esta story é a "faxina final" do sprint de reliability.

## Acceptance Criteria

### Documentation
- [ ] AC1: `CLAUDE.md` atualizado com pricing correto (R$397/mês, R$357 semestral, R$317 anual)
- [ ] AC2: `CLAUDE.md` seção Tech Stack atualizada com versões atuais
- [ ] AC3: `PRD.md` sincronizado com estado atual do produto
- [ ] AC4: `ROADMAP.md` atualizado com Reliability Sprint stories
- [ ] AC5: `CHANGELOG.md` atualizado com todas as mudanças do sprint

### Stale Code Cleanup
- [ ] AC6: Remover código morto identificado em auditorias (dead imports, unused functions)
- [ ] AC7: Remover configs stale (env vars não usadas, feature flags obsoletas)
- [ ] AC8: Atualizar OpenAPI snapshot: `pytest --snapshot-update tests/snapshots/`
- [ ] AC9: Remover arquivos temporários de debug/audit

### Quality
- [ ] AC10: Linting passa sem warnings
- [ ] AC11: Todos os testes passando
- [ ] AC12: `git diff --stat` documentado no PR (para review)

## Files to Change

- `CLAUDE.md` — pricing, tech stack, architecture updates
- `PRD.md` — sync with current state
- `ROADMAP.md` — add reliability sprint
- `CHANGELOG.md` — sprint changelog
- Various backend/frontend files — dead code removal
- `backend/tests/snapshots/` — regenerate

## Definition of Done

- [ ] Zero referências a R$1,999 em documentação
- [ ] Zero dead code warnings no linting
- [ ] Todos os testes passando
- [ ] PR merged
