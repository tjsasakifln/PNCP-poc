# Revisão adversarial do backlog — #1262

**Data:** 2026-08-13  
**Universo:** todas as issues **abertas** em `tjsasakifln/SmartLic` no momento da auditoria.  
**Método:** cada issue foi lida contra ADR-STRAT-001 e o critério econômico (demanda CONFENGE > preservar ativos > eliminar duplicação > reduzir legado > reduzir babysitting > qualidade > orgânico > conversão > expansão).

Fonte: `gh issue list --state open` → 12 issues. PRs Dependabot/pSEO antigos não são issues de produto.

## Resultado

Nenhuma issue aberta propõe novo billing, SaaS, DataLake ou crawler próprio. Nenhuma P0/P1 precisa ser encerrada como `not_planned`. Prioridades históricas de MRR já tinham sido removidas do tracker em 2026-08-13; esta revisão **confirma** e documenta o critério, em vez de preservar inércia.

## Tabela

| Issue | Problema econômico/operacional | Pertence à nova arquitetura? | Prioridade correta? | Dependências | Conflito? | Ação |
|-------|--------------------------------|------------------------------|---------------------|--------------|-----------|------|
| **#1262** | Ambiguidade estratégica (SaaS vs inbound) | Sim — é a decisão | P0 / `roadmap:now` | extra-cli#354 referenciada, não bloqueia a decisão | Não | Manter; fechar quando os docs canônicos e esta revisão estiverem no `main` |
| **#2111** | Operação e copy ainda vendem assinatura | Sim — sunset | P0 / now | #1262; SEO #2113 para URLs; #2114 para copy | Não | Manter; executar em ondas após #1262 |
| **#2113** | Perder indexação destrói o ativo | Sim — preservar patrimônio | P0 / now | Inventário paralelo a #2111; bloqueia delete de URL | Não | Manter |
| **#2108** | Dois DataLakes / crawler próprio | Sim — consumer | P0 / now | extra-cli#354, #289, #273 | Não | Manter; não executar antes do contrato |
| **#2112** | Sem superfície MVP não há inbound | Sim — MVP público | P0 / now | #2108, #2113 | Não | Manter |
| **#2116** | Tráfego público pode derrubar o truth plane | Sim — isolamento | P0 / now | Após #2108 para promoção | Não | Manter |
| **#2115** | Railway/Supabase caros e não canônicos | Sim — runtime mínimo | P0 / now | #2116 | Não | Manter |
| **#2114** | CTA SaaS impede conversão consultiva | Sim — marca/funil | P0 / now | #1262, #2112 para rollout | Não | Manter |
| **#2117** | Sem atribuição o inbound não é mensurável | Sim — handoff | P0 / now | #2114 | Não | Manter; Warmbly **não** é dependência |
| **#2109** | Ferramentas públicas extras | Sim, como expansão | P1 / `roadmap:next` | Após P0 | Não | Manter next |
| **#2118** | Mais pSEO sem dado único | Sim, com gate | P1 / next | Após P0 | Não | Manter next; não expandir agora |
| **#2107** | Assessment privado multi-cliente | Fora do go-live | P2 / `roadmap:later` | Após validar inbound | Não — já DEFER | Manter later |

## Issues históricas da #1262 (escopo antigo B2GOPS)

A #1262 nasceu como "Sistema Operacional B2G / Terminal do Operador" (workspace, war-room). As child issues #1277–#1282, #1293, #1294 estão **fechadas**. Esse escopo de workspace privado **não** é o caminho crítico. A epic foi reutilizada como decisão de reposicionamento. Workspace colaborativo = `SUNSET`/`DEFER`, não P0.

## O que foi deliberadamente **não** reaberto

Issues fechadas de billing, founders, viral K-factor, microtransações e cache warming permanecem fechadas. Reabrir seria restaurar a tese SaaS.

## Labels e milestones

- `roadmap:now` = somente caminho crítico (as 10 issues P0 acima, incluindo #1262).
- `roadmap:next` = #2109, #2118.
- `roadmap:later` = #2107.
- Label `Paused-Revenue-Dependent` (MRR) não se aplica a nenhuma issue aberta; descrição atualizada para não implicar meta de assinatura.
- Milestone **CONFENGE inbound — caminho crítico** agrupa as P0.

## P0/P1 inválidas (regra contínua)

Uma issue nova P0/P1 é inválida se propuser:

- plano de assinatura, billing, Stripe, quota, trial;
- DataLake ou crawler próprio no SmartLic;
- login wall em conteúdo público;
- Warmbly como blocker de go-live;
- expansão pSEO antes dos gates P0.

Ação: recusar ou rebaixar para later/`not_planned` com referência a este documento.
