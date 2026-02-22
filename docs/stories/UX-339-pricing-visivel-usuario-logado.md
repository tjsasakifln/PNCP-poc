# UX-339 — Mostrar Pricing Completo para Usuario Logado

**Tipo:** Bug / UX Alto
**Prioridade:** Alta (A4 da auditoria UX 2026-02-22)
**Criada:** 2026-02-22
**Status:** Pendente
**Origem:** Auditoria UX — Persona "Seu Carlos" (gestor PME 60 anos, interior BR)

---

## Problema

Quando um usuario logado (com acesso completo — admin, trial ativo ou assinante) acessa `/planos`, a pagina exibe apenas um card centralizado:

> "Voce possui acesso completo"
> "Todas as funcionalidades do SmartLic estao disponiveis para voce, sem restricoes."
> [Iniciar analise]

O pricing real (R$1.999/mes, periodos, features, FAQ) fica completamente oculto.

### Impacto

- Usuario em trial quer ver o preco para decidir se assina → nao consegue
- Usuario precisa deslogar para ver os precos (absurdo)
- Perda direta de conversao trial → paid
- Seu Carlos: "Quero ver quanto custa pra decidir, mas o sistema nao mostra!"

### Evidencia

- Screenshot `ux-audit-06-planos.png` — modal "Voce possui acesso completo" bloqueando todo o conteudo
- DOM snapshot confirma que o conteudo de pricing existe no HTML mas esta visualmente bloqueado pelo overlay

---

## Solucao Proposta

### Para usuario com acesso completo (admin/assinante):

Mostrar o pricing normalmente, com um banner informativo no topo:

```
┌──────────────────────────────────────────────┐
│ ✅ Voce possui acesso completo ao SmartLic   │
│ Sua proxima cobranca: R$ 1.999 em 15/03/2026 │
│ [Gerenciar assinatura]                       │
└──────────────────────────────────────────────┘

[Pricing cards normais abaixo]
```

### Para usuario em trial:

Mostrar o pricing com banner de trial:

```
┌──────────────────────────────────────────────────────┐
│ 🕐 Voce esta no periodo de avaliacao (X dias restantes) │
│ Escolha seu compromisso para continuar apos o trial   │
└──────────────────────────────────────────────────────┘

[Pricing cards normais abaixo — CTA "Assinar agora"]
```

### Para usuario com trial expirado:

Mostrar pricing com urgencia:

```
┌──────────────────────────────────────────────────┐
│ ⚠️ Seu periodo de avaliacao encerrou               │
│ Escolha um compromisso para voltar a ter acesso  │
└──────────────────────────────────────────────────┘

[Pricing cards normais — CTA "Continuar com SmartLic"]
```

---

## Criterios de Aceitacao

- [ ] AC1: Usuario logado (qualquer status) sempre ve o pricing completo na pagina /planos
- [ ] AC2: Banner contextual no topo indica status atual (trial X dias, assinante ativo, trial expirado)
- [ ] AC3: Assinante ativo ve "Gerenciar assinatura" que leva ao billing portal do Stripe
- [ ] AC4: Usuario em trial ve CTA "Assinar agora" nos cards
- [ ] AC5: Usuario com trial expirado ve CTA com urgencia
- [ ] AC6: Toggle mensal/semestral/anual continua funcional
- [ ] AC7: FAQ continua visivel e funcional
- [ ] AC8: Secao ROI ("Uma unica licitacao ganha pode pagar um ano") continua visivel

### Nao-Regressao

- [ ] AC9: Usuario nao-logado ve a pagina de planos normalmente (sem banner)
- [ ] AC10: Nenhum teste existente quebra

---

## Arquivos Envolvidos (Estimativa)

### Modificar
- `frontend/app/planos/page.tsx` — remover bloqueio overlay, adicionar banner contextual

### Testes
- `frontend/__tests__/planos.test.tsx` — atualizar/criar

---

## Estimativa

- **Complexidade:** Baixa (remover overlay + adicionar banner condicional)
- **Risco:** Baixo (pagina isolada, sem side effects)
