# DEBT-05: Database Integrity (Backup + FK + Soft-delete)

**Epic:** EPIC-TD-2026
**Fase:** 2 (Foundation)
**Horas:** 7h
**Agente:** @data-engineer + @devops
**Prioridade:** P1

## Debitos Cobertos

| TD | Item | Horas |
|----|------|-------|
| TD-034 | pg_dump semanal para S3 (backup independente) | 2h |
| TD-021 | profiles.plan_type CHECK -> FK (integridade referencial) | 4h |
| TD-020 + TD-NEW-002 | Investigar pattern is_active vestigial (0 rows inactive) | 1h |

## Acceptance Criteria

- [x] AC1: GitHub Actions workflow para pg_dump semanal para S3 bucket
- [x] AC2: FK migration em 3 steps: DROP CHECK, ADD FK NOT VALID, VALIDATE
- [x] AC3: Verificar zero orphan plan_types antes da FK migration
- [x] AC4: Documentar decisao sobre is_active: manter ou remover coluna
- [x] AC5: Execucao off-peak para FK validation (lock breve)

## Notas

- TD-020: Confirmado 0 rows com is_active=false (medido 2026-04-08). Pattern possivelmente vestigial.
- TD-021: plan_type definido em 2 lugares (plans table + CHECK constraint). FK unifica.
