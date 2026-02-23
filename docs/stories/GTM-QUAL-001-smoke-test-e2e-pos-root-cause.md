# GTM-QUAL-001: Smoke Test E2E Pos-Root Cause

## Epic
Root Cause — Qualidade (EPIC-GTM-ROOT)

## Sprint
Executar apos cada Tier completo (nao so no final)

## Prioridade
P1

## Estimativa
4h

## Descricao

As 12 stories de root cause alteram 30+ arquivos incluindo o fluxo principal de busca (ARCH-001 muda POST sincrono para async job). Cada story tem testes unitarios, mas nenhuma valida o fluxo completo de ponta a ponta: signup → onboarding → busca → resultado → pipeline → pagamento → confirmacao.

Esta story cria um smoke test suite em Playwright que valida a jornada completa do trial user apos cada Tier de implementacao, garantindo que mudancas arquiteturais nao quebraram a experiencia integrada.

### Justificativa

| Risco | Sem esta story | Com esta story |
|-------|----------------|----------------|
| ARCH-001 quebra SSE | Descoberto em producao | Descoberto em CI |
| PROXY-001 esquece 1 proxy | Trial user ve erro ingles | Capturado por grep |
| UX-001 remove banner mas nao substitui | Informacao perdida | Fluxo completo validado |
| ARCH-002 cache global nao popula | Trial user sem protecao | Teste simula trial cold start |

## Criterios de Aceite

### Suite Playwright

- [ ] AC1: Teste E2E "Trial User First 5 Minutes": signup → onboarding (setor+UFs) → busca automatica → resultados em tela → download Excel
- [ ] AC2: Teste E2E "Post-Payment": login pagante → busca → resultado → pipeline drag-and-drop → dashboard com dados
- [ ] AC3: Teste E2E "Error Recovery": busca com backend offline simulado → error state visivel → backend volta → retry funciona → resultados aparecem

### Validacoes Automaticas

- [ ] AC4: Assertion: zero texto em ingles em qualquer elemento visivel durante os fluxos (grep DOM por patterns: /Invalid|Error|Failed|unauthorized|not found/i excluindo termos tecnicos)
- [ ] AC5: Assertion: maximo 1 banner informativo visivel em qualquer momento (nunca 2+ empilhados)
- [ ] AC6: Assertion: nenhum botao desabilitado sem tooltip explicando por que
- [ ] AC7: Assertion: trial user recebe resultado em <30s (busca completa, nao apenas parcial)

### Execucao por Tier

- [ ] AC8: Executar suite apos Tier 1 completo (ARCH-001 + ARCH-002 + PROXY-001) — validar busca async + cache + erros PT
- [ ] AC9: Executar suite apos Tier 2 completo (UX-001/002/003/004) — validar banner unico + error states + retry + subscription
- [ ] AC10: Executar suite apos Tier 3 completo (INFRA-001/002/003) — validar resiliencia sob falha simulada
- [ ] AC11: Executar suite completa pre-GTM launch — validacao final

### CI Integration

- [ ] AC12: Suite integrada ao GitHub Actions — executa em PR para `main` quando stories GTM-ROOT tocam arquivos afetados
- [ ] AC13: Failure na suite bloqueia merge (quality gate)

## Testes (a propria story E os testes)

```bash
cd frontend && npm run test:e2e -- --grep "smoke"
```

- [ ] T1: Fluxo trial signup→busca→resultado completa em <60s
- [ ] T2: Zero texto ingles em erros durante fluxo
- [ ] T3: Maximo 1 banner visivel simultaneamente
- [ ] T4: Recovery funciona apos erro simulado

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/e2e-tests/smoke-gtm-root-cause.spec.ts` | Criar — suite de smoke tests |
| `.github/workflows/e2e.yml` | Modificar — adicionar trigger para stories GTM-ROOT |
| `frontend/playwright.config.ts` | Modificar — adicionar project "smoke" se necessario |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Executa apos | Cada Tier (1, 2, 3) | Validacao incremental |
| Nao bloqueia | Nenhuma | Pode rodar em paralelo com inicio do proximo Tier |
