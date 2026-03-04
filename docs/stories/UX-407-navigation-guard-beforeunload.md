# STORY-407: Corrigir navigation guard ativo sem busca em andamento

**Prioridade:** P1
**Esforço:** S
**Squad:** team-bidiq-frontend

## Contexto
O dialog "Você tem resultados de busca que serão perdidos. Deseja sair?" aparece ao tentar navegar mesmo quando não há busca em andamento — basta ter resultados exibidos. Isso é especialmente irritante quando o usuário já analisou os resultados e quer ir para Pipeline ou Dashboard. O guard só desativa após download do Excel, mas a maioria dos usuários não baixa Excel.

## Problema (Causa Raiz)
- `frontend/hooks/useNavigationGuard.ts:31`: `const shouldGuard = hasResults && !hasDownloaded` — ativo sempre que há resultados, independente de interação.
- `frontend/app/buscar/page.tsx:580-583`: `useNavigationGuard({ hasResults: !!search.result && total > 0, hasDownloaded })` — `hasDownloaded` só vira true após download.

## Critérios de Aceitação
- [x] AC1: O navigation guard só deve ativar durante uma busca em andamento (`search.loading === true`).
- [x] AC2: Após os resultados aparecerem, o guard deve se desativar automaticamente após 30 segundos.
- [x] AC3: Clicar em links internos do SmartLic (Pipeline, Dashboard, Histórico, Conta) nunca deve exibir o dialog de confirmação.
- [x] AC4: O `beforeunload` (fechar aba/reload) pode permanecer ativo enquanto `loading === true` (protege contra perda de busca em andamento).
- [x] AC5: Remover a dependência de `hasDownloaded` como único mecanismo de desativação.

## Arquivos Impactados
- `frontend/hooks/useNavigationGuard.ts` — Ajustar lógica: guard ativo apenas durante loading + 30s após resultado.
- `frontend/app/buscar/page.tsx` — Ajustar parâmetros passados ao hook.

## Testes Necessários
- [x] Teste que guard está ativo durante `loading=true`.
- [x] Teste que guard desativa 30s após `loading` mudar para `false`.
- [x] Teste que links internos (mesmo origin) não acionam dialog.
- [x] Teste que `beforeunload` ativa apenas durante loading.
- [x] Teste que guard NÃO ativa quando resultados estão exibidos mas busca terminou há mais de 30s.

## Notas Técnicas
- A distinção é: links internos nunca devem perguntar (usuário pode voltar via browser back). Apenas `beforeunload` (fechar aba) é relevante, e apenas durante busca ativa.
- Considerar usar `router.events` do Next.js App Router para interceptar apenas navegação "destrutiva" (sair do app), não navegação interna.
