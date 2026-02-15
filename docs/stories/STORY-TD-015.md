# STORY-TD-015: Testes de Pipeline, Onboarding e Middleware

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 3: Qualidade e Cobertura

## Prioridade
P2-P3

## Estimativa
24h

## Descricao

Esta story cria suites de testes para tres areas do frontend que atualmente nao possuem nenhum teste automatizado, completando a campanha de cobertura (Cluster G.5 do assessment) e atingindo o threshold de 60%.

1. **Testes de Pipeline drag-and-drop (FE-10, MEDIUM, 8h)** -- `app/pipeline/page.tsx` implementa Kanban com @dnd-kit. Interacao complexa de drag-and-drop sem teste. Criar testes que verificam: drag entre colunas, persistencia de movimentacao, estado visual durante drag, empty state de colunas.

2. **Testes de Onboarding wizard flow (FE-11, MEDIUM, 8h)** -- `app/onboarding/page.tsx` implementa formulario multi-step sem teste. Criar testes que verificam: progressao entre steps, validacao de campos, skip/back navigation, conclusao do wizard, persistencia de dados entre steps.

3. **Testes de Middleware route protection (FE-12, MEDIUM, 8h)** -- `frontend/middleware.ts` protege rotas autenticadas. Logica de auth guard sem teste. Criar testes que verificam: redirect para login quando nao autenticado, acesso permitido quando autenticado, redirect correto apos login, protecao de rotas especificas.

**Meta de cobertura:** Atingir 60%+ no frontend (threshold do Jest), habilitando o quality gate no CI.

## Itens de Debito Relacionados
- FE-10 (MEDIUM): Sem testes para pipeline drag-and-drop
- FE-11 (MEDIUM): Sem testes para onboarding wizard flow
- FE-12 (MEDIUM): Sem testes para middleware.ts route protection
- SYS-01 (LOW): Frontend test coverage abaixo de 60% (meta: atingir threshold)

## Criterios de Aceite

### Pipeline Tests
- [ ] Teste: renderiza 5 colunas do Kanban
- [ ] Teste: drag de item entre colunas atualiza estado
- [ ] Teste: item movido persiste apos reload (mock de API)
- [ ] Teste: empty state de coluna mostra mensagem
- [ ] Teste: novo item adicionado aparece na coluna correta

### Onboarding Tests
- [ ] Teste: step 1 renderiza corretamente
- [ ] Teste: validacao de campos obrigatorios
- [ ] Teste: progressao para proximo step
- [ ] Teste: botao voltar retorna ao step anterior
- [ ] Teste: conclusao do wizard salva dados (mock)
- [ ] Teste: dados preenchidos persistem entre steps

### Middleware Tests
- [ ] Teste: usuario nao autenticado em rota protegida -> redirect para /login
- [ ] Teste: usuario autenticado em rota protegida -> acesso permitido
- [ ] Teste: usuario autenticado em /login -> redirect para /buscar
- [ ] Teste: rotas publicas acessiveis sem auth (/, /planos, /login, /signup)
- [ ] Teste: redirect reason preservado na URL

### Metricas
- [ ] Frontend test coverage >= 60% (threshold atingido)
- [ ] CI quality gate de coverage habilitado e passando
- [ ] Diretorio `quarantine/` vazio (se todos os testes restantes foram reescritos)

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| PERF-T05 | Pipeline page com 50 items < 3s | E2E timing | P2 |
| -- | Middleware redirect funciona corretamente | Unitario | P2 |
| -- | Pipeline DnD funciona corretamente | Unitario + E2E | P3 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (testes sao aditivos, mas idealmente apos TD-012 para consistencia)

## Riscos
- Testes de DnD podem ser flaky por natureza (timing, animations).
- Middleware tests podem requerer mocking complexo de NextRequest/NextResponse.
- Se coverage nao atingir 60% apos esta story, items adicionais de TD-013 ou TD-019 podem ser necessarios.

## Rollback Plan
- Testes sao aditivos. Se flaky, marcar como skip e investigar.
- Quality gate pode ser habilitado gradualmente (warning -> failure).

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + E2E)
- [ ] CI/CD green
- [ ] Frontend test coverage >= 60% (threshold atingido)
- [ ] Quality gate de coverage habilitado no CI
- [ ] Diretorio `quarantine/` inventariado (idealmente vazio)
