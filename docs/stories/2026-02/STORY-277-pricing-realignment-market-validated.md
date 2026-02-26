# STORY-277: Repricing Fundamentado — R$1.999 → Faixa de Mercado

**Priority:** P0 BLOCKER
**Effort:** 1 day (decisao) + 1 day (implementacao)
**Squad:** @po + @pm + @dev
**Replaces:** STORY-269 (pricing strategy) — agora com dados reais de mercado

## Fundamentacao (Precos Reais dos Concorrentes — Fev 2026)

### Mapeamento Competitivo Validado

| Plataforma | Menor Plano | Plano Premium | AI? | Fonte |
|------------|------------|--------------|-----|-------|
| Alerta Licitacao | R$31/mes (anual) | R$45/mes | Nao | [alertalicitacao.com.br](https://alertalicitacao.com.br/) |
| LicitaIA | R$67/mes | R$247/mes (ilimitado) | Sim (core) | [licitaia.app](https://www.licitaia.app/) |
| Licitei | R$0 (free) | R$393/mes (Premium) | Sim | [licitei.com.br/planos](https://www.licitei.com.br/planos) |
| Portal Compras | R$96-149/mes | R$149/mes | Nao | [conlicitacao.com.br](https://conlicitacao.com.br/) |
| Licita Ja | R$160/mes (3 anos) | R$235/mes | Limitado | [licitaja.com.br](https://www.licitaja.com.br/subscription.php) |
| Siga Pregao | R$208/mes (anual) | R$397/mes | Sim (12-200/dia) | [sigapregao.com.br/p/precos](https://www.sigapregao.com.br/p/precos/) |
| ConLicitacao | Oculto (sales-led) | Oculto | Sim | [conlicitacao.com.br/planos](https://conlicitacao.com.br/planos/) |
| Effecti | Oculto (sales-led) | Oculto | Sim | [effecti.com.br/planos](https://effecti.com.br/planos/) |
| **SmartLic** | — | **R$1.999/mes** | Sim (core) | — |

### Analise de Posicionamento

- **Faixa de mercado para AI + busca:** R$100-400/mes
- **SmartLic a R$1.999 e 5-13x acima do mercado**
- **Maior preco publico do mercado:** Licitei Multiempresas R$1.179/mes (para 3 CNPJs)
- Concorrentes na faixa R$300-400 incluem: robo de lance, automacao de proposta, monitoramento de chat — funcionalidades que SmartLic NAO tem ainda

### O que SmartLic tem de unico
- Classificacao IA por setor (GPT-4.1-nano) — nenhum concorrente faz
- Viability assessment 4 fatores — unico
- Multi-fonte consolidada (PNCP + PCP + ComprasGov) com dedup

### O que SmartLic NAO tem (vs concorrentes a R$300-400)
- Robo de lance automatico
- Automacao de proposta
- Monitoramento de chat/pregoeiro
- Email alerts/digest (STORY-278)
- Multi-CNPJ

## Opcoes de Pricing (Decisao PO — Timebox 24h)

### Opcao 1: Beta Gratuito (RECOMENDADO para GTM)
- **R$0 por 30 dias** (beta aberto, sem cartao)
- Apos beta: SmartLic Pro R$297/mes (anual) / R$397/mes (mensal)
- **Racional:** Posiciona no topo do mercado visivel (par com Siga Pregao/Licitei Premium) mas justificado pela IA unica. Beta gratuito elimina barreira de entrada.
- **Benchmark:** Licitei oferece plano FREE. LicitaIA tem garantia 7 dias.

### Opcao 2: Entry Tier + Premium
- **SmartLic Busca:** R$97/mes (busca + filtro, sem IA, sem pipeline)
- **SmartLic Pro:** R$297/mes (tudo incluso)
- **Racional:** Entrada competitiva com LicitaIA (R$67-117), upsell para Pro
- **Risco:** Dois planos = complexidade de billing/onboarding

### Opcao 3: Credit-Based (modelo LicitaIA)
- **R$67/mes** (30 buscas com IA)
- **R$117/mes** (60 buscas)
- **R$197/mes** (ilimitado)
- **Racional:** Alinha com modelo de mercado emergente
- **Risco:** Requer refactor significativo do quota system

## Acceptance Criteria

### AC1: Decisao de Pricing (Dia 1 — Timebox 24h)
- [x] PO escolhe opcao (1, 2, ou 3) com justificativa
  - **Decisao: Opcao 1 (default)** — Beta Gratuito 30 dias + SmartLic Pro R$397/mes (mensal) / R$357/mes (semestral, -10%) / R$297/mes (anual, -25%)
- [x] Se nenhuma decisao em 24h: **default = Opcao 1** (beta gratuito + R$297-397) ✅ aplicado

### AC2: Implementar Pricing Escolhido (Dia 2)
- [x] Atualizar `billing.py`: novo(s) price_id(s) no Stripe (routes/billing.py lê do DB — Stripe price IDs são configurados no Stripe Dashboard)
- [x] Atualizar `frontend/app/planos/page.tsx`: novos precos e copy (R$397/357/297 + Beta badge)
- [x] Atualizar `frontend/app/termos/page.tsx` secao 3.2: remover phantom plans (E-HIGH-001) — agora reflete planos reais com precos corretos
- [x] Atualizar quota.py: limites do novo plano (PLAN_PRICES atualizado para R$ 397/mês)

### AC3: Remover Phantom Plans do ToS
- [x] Secao 3.2 de `/termos` referencia planos que NAO EXISTEM:
  - ~~"Free: 5 buscas/mes"~~ (já removido em STORY-272)
  - ~~"Professional: buscas ilimitadas"~~ (já removido em STORY-272)
  - ~~"Enterprise: API access, white-label, SLA 24/7"~~ (já removido em STORY-272)
- [x] Reescrever para refletir planos reais — agora mostra "Período de Avaliação (Beta): 30 dias" + "SmartLic Pro: R$397/mês (mensal), R$357/mês (semestral), R$297/mês (anual)"

### AC4: Landing Page Pricing Section
- [x] Atualizar comparativo de precos se visivel na landing (StructuredData, UpgradeModal, TrialConversionScreen, TrialExpiringBanner, QuotaCounter, FinalCTA, InstitutionalSidebar, pricing page, ajuda FAQ, blog posts, signup metadata)
- [x] Adicionar badge "Beta" se Opcao 1 — badge adicionado no planos/page.tsx

## Fontes dos Dados
- Licitei: https://www.licitei.com.br/planos
- Siga Pregao: https://www.sigapregao.com.br/p/precos/
- LicitaIA: https://www.licitaia.app/
- Licita Ja: https://www.licitaja.com.br/subscription.php
- Alerta Licitacao: https://alertalicitacao.com.br/
