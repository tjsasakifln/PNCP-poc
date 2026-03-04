# STORY-404: Tour de resultados bloqueia visualização — reposicionar trigger

**Prioridade:** P1
**Esforço:** S
**Squad:** team-bidiq-frontend

## Contexto
O tour interativo de onboarding (Shepherd.js) dos resultados dispara 1.5s após os resultados aparecerem, cobrindo os cards que o usuário acabou de esperar 30-60s para ver. Isso causa frustração imediata e cria uma experiência anti-usuário: "esperei 1 minuto e a primeira coisa que vejo é um popup".

## Problema (Causa Raiz)
- `frontend/app/buscar/page.tsx:441-458`: `setTimeout(() => startResultsTour(), 1500)` — dispara automaticamente após resultados renderizarem.
- O tour usa overlay escuro que cobre os resultados, impedindo scroll e leitura.

## Critérios de Aceitação
- [ ] AC1: Remover auto-start do tour de resultados via `setTimeout`. Tour de resultados nunca deve iniciar automaticamente.
- [ ] AC2: Substituir por banner discreto (toast ou inline, não modal) abaixo do header de resultados: "Primeira vez vendo resultados? Clique aqui para um tour rápido." com botão "Iniciar tour" e "X" para fechar.
- [ ] AC3: Banner desaparece após 10s ou após o usuário fazer scroll (whichever comes first).
- [ ] AC4: Clicar "Iniciar tour" inicia o Shepherd tour normalmente.
- [ ] AC5: Após o usuário fechar ou completar o tour, marcar como completado (já existe `isResultsTourCompleted()`) e nunca mais mostrar o banner.
- [ ] AC6: O botão de restart tour no `OnboardingTourButton` continua funcionando normalmente para quem quiser revisitar.

## Arquivos Impactados
- `frontend/app/buscar/page.tsx` — Remover `setTimeout` auto-start; adicionar banner inline.
- `frontend/app/buscar/components/SearchResults.tsx` — Renderizar banner de convite ao tour (se não completado).

## Testes Necessários
- [ ] Teste que tour de resultados NÃO inicia automaticamente.
- [ ] Teste que banner aparece quando `isResultsTourCompleted()` retorna false.
- [ ] Teste que banner desaparece após 10s.
- [ ] Teste que clicar "Iniciar tour" chama `startResultsTour()`.
- [ ] Teste que banner não aparece quando tour já completado.

## Notas Técnicas
- O tour de busca (search tour) pode manter o auto-start no primeiro acesso — é menos intrusivo porque não bloqueia resultados esperados.
- Manter tracking de eventos Mixpanel (`onboarding_tour_started`, `onboarding_tour_skipped`).
