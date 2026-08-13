# Plano Fundadores — Política Interna

> **ARQUIVO HISTÓRICO — NÃO EXECUTAR.** Oferta encerrada (deadline 2026-06-30).
> As seções 7 (Go-Live) e 8 (Rollback) descrevem um procedimento **não vigente**.
> Não habilitar `FOUNDERS_OFFER_ENABLED`, não criar Price Stripe, não aplicar as migrations deste arquivo como go-live, não publicar checkout.
> Posicionamento vigente: [ADR-STRAT-001](adr/ADR-STRAT-001-smartlic-confenge-inbound.md) · sunset [#2111](https://github.com/tjsasakifln/SmartLic/issues/2111).

**Versão:** 1.0 | **Data:** 2026-05-07 | **Status:** Histórico (não vigente como tese de produto)  
**Oferta:** R$997 one-time vitalício | **Deadline:** 30/06/2026 | **Cap:** 50 vagas

---

## 1. O que é o Plano Fundadores

Acesso vitalício ao plano self-service **atual** do SmartLic em troca de financiamento antecipado da próxima fase do produto. Preço único R$997 (sem recorrência). Vagas limitadas a 50 ou até 30/06/2026, o que ocorrer primeiro.

| Campo | Valor |
|-------|-------|
| Preço | R$997 one-time (sem recorrência) |
| Deadline | 2026-06-30T23:59:59-03:00 |
| Cap | 50 vagas |
| Offer mode | `lifetime` |
| Offer version | `v2_lifetime` |
| Stripe Price | `FOUNDING_ONE_TIME_PRICE_ID` (env var) |

---

## 2. Incluído — Escopo permanente

O Plano Fundadores garante acesso vitalício ao **escopo self-service atual**:

- ✅ Busca multi-fonte de licitações (PNCP + ComprasGov + PCP v2)
- ✅ Classificação IA por setor (20 setores, GPT-4.1-nano)
- ✅ Análise de viabilidade (4 fatores)
- ✅ Pipeline Kanban de oportunidades
- ✅ Exportação Excel estilizado
- ✅ Resumo executivo com IA
- ✅ Histórico de buscas e sessões
- ✅ Acesso a todos os setores disponíveis na plataforma
- ✅ Desconto de 50% em serviços de **consultoria própria SmartLic** (contratos formais)

---

## 3. NÃO incluído

Comunicar claramente para evitar passivo operacional perpétuo:

- ❌ Features premium/enterprise futuras (sem previsão de escopo)
- ❌ Suporte prioritário vitalício ou SLA enterprise
- ❌ Customizações ilimitadas
- ❌ Garantia de êxito em licitações
- ❌ Parceria oficial com PNCP, ComprasNet, TCU, governo
- ❌ Consultoria de terceiros com desconto (apenas serviços SmartLic)
- ❌ Uso sem limites operacionais (rate limit e fair use aplicam)

---

## 4. Limitações Operacionais (Fair Use)

As seguintes restrições aplicam mesmo para fundadores:

- Rate limit de buscas (mesmo tier que plano Pro)
- Anti-abuse: revenda, scraping massivo, automação que degrada o serviço = suspensão
- Compute fair use: sem SLA enterprise de uptime

---

## 5. Política de Desconto Consultoria

- **50%** nos serviços de consultoria **próprios SmartLic** (contratos formais)
- Válido enquanto: o cliente mantiver status de fundador E o serviço de consultoria existir
- NÃO se aplica a serviços de terceiros, parceiros ou assessorias externas
- Forma de ativação: contato direto com time SmartLic para emissão de contrato

---

## 6. Comunicação Permitida

### ✅ Pode dizer
- "Acesso vitalício ao plano self-service atual do SmartLic"
- "Ajude a financiar a próxima fase do SmartLic"
- "Vagas limitadas: 50 ou até 30/06/2026"
- "Sem mensalidade — pague uma vez, use para sempre"
- "50% de desconto em consultoria SmartLic"
- "Dados de licitações de todas as fontes oficiais"

### ❌ Não pode dizer
- "Acesso vitalício a TUDO que o SmartLic lançar"
- "Suporte prioritário para sempre"
- "Garantia de ganhar licitações"
- "Parceria oficial com o governo"
- "Nunca vai mudar"
- "Desconto em qualquer consultoria"

---

## 7. Checklist Go-Live

> **NÃO EXECUTAR.** Checklist histórico. O go-live desta oferta está cancelado. Não habilitar `FOUNDERS_OFFER_ENABLED` nem configurar Stripe/Railway a partir deste arquivo.

Antes de habilitar `FOUNDERS_OFFER_ENABLED=true` em produção (procedimento **histórico**, não vigente):

- [ ] Stripe Price one-time R$997 criada via `scripts/create_founding_lifetime_price.py` (idempotente)
- [ ] `FOUNDING_ONE_TIME_PRICE_ID` setado em Railway prod (bidiq-backend)
- [ ] Migration `founding_policy_lifetime_pivot` aplicada (`supabase db push`)
- [ ] Migration `profiles_founder_fields` aplicada
- [ ] `FOUNDERS_OFFER_ENABLED=true` em Railway prod
- [ ] Webhook handler testado em staging (checkout.session.completed com mode=payment)
- [ ] Página `/fundadores` publicada e acessível
- [ ] Termos `/termos/fundadores` publicados
- [ ] Email welcome founders testado (Resend staging)
- [ ] Banner global QA em mobile + desktop
- [ ] Lighthouse pSEO sem regressão (≥80)
- [ ] Sentry sem novos erros nas 24h em staging
- [ ] Backup DB pré go-live (`pg_dump` manual)

---

## 8. Checklist Rollback

> **NÃO EXECUTAR.** Checklist histórico. Não usar estes passos como runbook vigente de billing.

Se necessário reverter a oferta após ativação (procedimento **histórico**, não vigente):

1. `railway variables set FOUNDERS_OFFER_ENABLED=false` (imediato, sem deploy)
2. Desativar Price no Stripe Dashboard (impede novos checkouts)
3. Rollback migrations se necessário: `supabase db push` com `.down.sql`
4. Comunicar fundadores ativos por email (não remover acesso retroativamente)

Ver `docs/runbooks/founders-rollback.md` para o procedimento completo de rollback.

---

## 9. Comunicação de Mudanças Futuras

Se o escopo do Plano Fundadores mudar materialmente (ex.: descontinuação de feature incluída):

1. Email para todos os fundadores com 90 dias de antecedência
2. Opção de reembolso proporcional (CDC art. 49 e-commerce para casos graves)
3. Registro em `CHANGELOG.md` com justificativa

---

## 10. Histórico de Versões

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-05-07 | Criação — pivot BIZ-FOUND-002 v1 (subscription -50%) → v2 (one-time R$997) |
