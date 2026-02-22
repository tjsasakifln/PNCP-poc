# UX-343 — Fix: Exibicao de Nome de Plano Legacy ("Sala de Guerra" → "SmartLic Pro")

**Tipo:** Bug / UX
**Prioridade:** Alta
**Criada:** 2026-02-22
**Status:** Pendente
**Origem:** Auditoria UX 2026-02-22 — Menu do usuario mostra "Sala de Guerra" (plano legacy)

---

## Problema

No menu do usuario (dropdown do avatar), o plano exibido e "Sala de Guerra" com badge dourado "S". Este era o nome do plano mais alto no modelo antigo de 3 tiers (Consultor Agil / Maquina de Licitacoes / Sala de Guerra).

Apos GTM-002, o SmartLic migrou para plano unico "SmartLic Pro" com 3 periodos de faturamento. Os planos legados foram mantidos funcionais mas deveriam exibir "(legacy)" no nome conforme documentado.

### Evidencia

- Screenshot `ux-audit-10-user-menu.png` — badge "S Sala de Guerra >" no menu do usuario
- GTM-002 documenta: Legacy plans kept with "(legacy)" suffix in PLAN_NAMES

### Impacto

- Incoerencia: landing page e pricing falam "SmartLic Pro", mas o menu mostra "Sala de Guerra"
- Confusao para usuario: "O que e Sala de Guerra? Nao era SmartLic Pro?"
- Para novos usuarios que verao outros com planos diferentes, gera duvida

---

## Solucao

### 1. Frontend: Mapear nomes legados para exibicao

No componente que renderiza o plano no menu do usuario, mapear:

```typescript
const DISPLAY_PLAN_NAMES: Record<string, string> = {
  'smartlic_pro': 'SmartLic Pro',
  'sala_guerra': 'SmartLic Pro',        // legacy → mostrar como Pro
  'maquina': 'SmartLic Pro',            // legacy → mostrar como Pro
  'consultor_agil': 'SmartLic Pro',     // legacy → mostrar como Pro
  'free_trial': 'Avaliacao',
};
```

Ou, se o backend ja retorna `plan_type` normalizado, garantir que a UI consome o nome correto.

### 2. Backend: Verificar profiles.plan_type

Verificar na tabela `profiles` se o campo `plan_type` do admin e `sala_guerra` e se deveria ter sido migrado para `smartlic_pro` apos GTM-002.

Se nao migrado: criar migration ou script que atualiza planos legados para `smartlic_pro` (se a subscription Stripe foi migrada).

---

## Criterios de Aceitacao

- [ ] AC1: Menu do usuario exibe "SmartLic Pro" (nunca "Sala de Guerra", "Maquina" ou "Consultor Agil")
- [ ] AC2: Badge usa icone/cor consistente com o branding SmartLic Pro
- [ ] AC3: Pagina /conta exibe "SmartLic Pro" na secao de plano
- [ ] AC4: Se o backend retorna plano legacy, o frontend mapeia para "SmartLic Pro"
- [ ] AC5: Verificar e corrigir `profiles.plan_type` no banco se necessario

### Nao-Regressao

- [ ] AC6: Funcionalidades do plano continuam identicas (nao mudar permissoes, so nome)
- [ ] AC7: Nenhum teste existente quebra

---

## Arquivos Envolvidos (Estimativa)

### Investigar
- `backend/routes/user.py` — endpoint /me que retorna plan_type
- `backend/config.py` ou `billing.py` — PLAN_NAMES mapping

### Modificar
- Frontend: componente que renderiza o badge de plano no header/menu
- Frontend: `/conta/page.tsx` — secao "Gerenciar SmartLic Pro"

### Possivelmente
- `supabase/migrations/` — migration para atualizar plan_type de legados

---

## Estimativa

- **Complexidade:** Baixa
- **Risco:** Baixo (so renomeia exibicao)
