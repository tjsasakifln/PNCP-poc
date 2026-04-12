# STORY-449: Referral In-Context Pós-Busca Bem-Sucedida

**Priority:** P2 — Aquisição viral de baixo custo
**Effort:** S (1-2 dias)
**Squad:** @dev + @qa
**Status:** Ready
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 3 — Semanas 5-8

---

## Contexto

O sistema de referral `/indicar` já existe (1 mês grátis por conversão) mas está enterrado no menu de navegação sem nenhum trigger contextual. O melhor momento para pedir referral é imediatamente após o usuário ter uma busca bem-sucedida — o pico de satisfação.

Um toast não-intrusivo pós-busca converte usuários satisfeitos em embaixadores. Cada referral bem-sucedido tem CAC ~R$750 vs. R$2.400-4.700 via SEO.

**Impacto estimado:** +0.5pp direto + efeito viral compounding.

---

## Acceptance Criteria

### AC1: Toast pós-busca bem-sucedida
- [ ] Após busca retornar ≥ 3 resultados filtrados, exibir toast/snackbar no canto inferior direito
- [ ] Conteúdo: "Encontrou boas oportunidades? Indique um amigo e ganhe 1 mês grátis →"
- [ ] Toast tem botão X para fechar (dismiss)
- [ ] Toast auto-fecha após 8 segundos se não clicado

### AC2: Throttle de exibição (não intrusivo)
- [ ] Toast aparece apenas 1 vez por sessão de browser (estado em `sessionStorage`)
- [ ] Toast aparece no máximo 1 vez a cada 7 dias por usuário (estado em localStorage: `smartlic_referral_shown_at` com timestamp)
- [ ] Lógica: se `Date.now() - localStorage.getItem('smartlic_referral_shown_at') < 7 * 24 * 60 * 60 * 1000` → não mostrar

### AC3: Link para /indicar
- [ ] Click no texto/link do toast abre `/indicar` (página existente) na mesma aba
- [ ] Ao clicar, também salvar timestamp em localStorage (AC2)

### AC4: Dismiss e estado
- [ ] Botão X fecha o toast e salva timestamp em localStorage (não mostrar por 7 dias)
- [ ] Auto-close (8s) também salva o timestamp

### AC5: Condição mínima de resultados
- [ ] Toast SÓ aparece se a busca retornou ≥ 3 resultados com `is_relevant: true` ou equivalente
- [ ] Toast NÃO aparece se busca retornou 0-2 resultados (usuário frustrado não refere)

### AC6: Tracking Mixpanel
- [ ] `referral_prompt_shown` — quando toast aparece
- [ ] `referral_prompt_clicked` — quando usuário clica no link
- [ ] `referral_prompt_dismissed` — quando usuário clica no X ou toast auto-fecha

### AC7: Funcional para trial e pagantes
- [ ] Toast aparece para trial users E usuários pagantes
- [ ] Pagante satisfeito refere mais — não restringir por plano

### AC8: Testes
- [ ] Teste: busca com ≥ 3 resultados → toast visível
- [ ] Teste: busca com < 3 resultados → toast não aparece
- [ ] Teste: toast já mostrado na sessão → não aparece novamente
- [ ] Teste: localStorage com timestamp < 7 dias → toast não aparece
- [ ] Teste: click X → timestamp salvo em localStorage
- [ ] Teste: eventos Mixpanel disparados corretamente

---

## Scope

**IN:**
- Componente `ReferralToast.tsx`
- Lógica de trigger em `buscar/page.tsx` pós-busca
- Throttle via sessionStorage + localStorage
- Tracking Mixpanel

**OUT:**
- Alteração do sistema de referral `/indicar` (existente, sem mudança)
- Referral por WhatsApp ou email direto do toast
- A/B test de mensagem
- Referral automático (sem ação do usuário)

---

## Dependencies

- Página `/indicar` existente (não alterar)
- Resultado de busca deve expor contagem de resultados filtrados (`filteredResults.length`)
- Nenhuma dependência de outras stories deste epic

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| sessionStorage não disponível em SSR | Baixa | Componente é client-side; verificar antes de acessar `window.sessionStorage` |
| Toast interfere com outros toasts/notificações da UI | Média | Verificar sistema de toast existente (Sonner, Radix, etc.) e usar o mesmo sistema |

---

## File List

- [ ] `frontend/app/buscar/components/ReferralToast.tsx` — AC1-AC6: novo componente
- [ ] `frontend/app/buscar/page.tsx` — AC1, AC5: integrar lógica de trigger pós-busca
- [ ] `frontend/__tests__/buscar/ReferralToast.test.tsx` — AC8: testes unitários

---

## Dev Notes

- Verificar qual sistema de toast o projeto usa (Sonner? Radix Toast? shadcn/ui Toast?) e usar o mesmo padrão
- Condição de trigger: verificar quando `buscar/page.tsx` sabe que os resultados chegaram e quantos são filtrados
- Se o projeto usa `react-hot-toast` ou similar, criar `ReferralToast` como componente wrapper
- sessionStorage key: `smartlic_referral_shown_session`
- localStorage key: `smartlic_referral_shown_at` (valor: timestamp ISO string)

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +0.5pp + viral |
