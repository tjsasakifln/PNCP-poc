# Relatorio de Debito Tecnico — SmartLic

**Projeto:** SmartLic (smartlic.tech)
**Empresa:** CONFENGE Avaliacoes e Inteligencia Artificial LTDA
**Data:** 2026-03-23
**Versao:** 3.0
**Preparado por:** @analyst (Alex) — Phase 9, Brownfield Discovery

---

## Executive Summary

### Situacao Atual

O SmartLic esta em um estagio saudavel para um produto POC v0.5 em producao. A plataforma funciona, atende usuarios em trial, e os pilares fundamentais — busca multi-fonte, classificacao por IA, cache resiliente, pipeline de oportunidades — estao operacionais. Seis problemas tecnicos que haviam sido identificados ja foram resolvidos em sprints anteriores, incluindo o unico item critico de banco de dados (padronizacao de chaves estrangeiras). Isso demonstra que a equipe tem historico de tratar divida tecnica com eficacia.

No entanto, 54 debitos tecnicos permanecem abertos, sendo 1 critico e 9 de alta prioridade. O problema mais urgente e um vazamento de memoria no sistema de cobranca que pode derrubar o servidor sob alto volume de usuarios — exatamente o cenario de sucesso que se espera atingir com a conversao de trials. Alem disso, uma vulnerabilidade no roteamento de webhooks do Stripe pode estar causando processamento duplicado de eventos de pagamento, o que representa risco direto a receita.

O custo de inacao e desproporcional ao custo de resolucao. Enquanto a correcao completa representa ~196 horas de trabalho (R$ 29.400), os riscos nao tratados incluem perda de receita por falha de cobranca, degradacao de performance que afeta conversao de visitantes, e acumulo de complexidade que vai desacelerar progressivamente a entrega de novas funcionalidades. Para um produto pre-revenue buscando product-market fit, velocidade de iteracao e sobrevivencia sao sinonimos.

### Numeros Chave

| Metrica | Valor |
|---------|-------|
| Total de debitos abertos | 54 |
| Debitos CRITICOS | 1 |
| Debitos de alta prioridade | 9 |
| Debitos de media prioridade | 27 |
| Debitos de baixa prioridade | 17 |
| Esforco total estimado | ~196 horas |
| Custo total estimado (R$150/h) | R$ 29.400 |
| Items ja resolvidos em sprints anteriores | 6 |
| Taxa de erro do assessment inicial (corrigida) | 18% (10 de 56 items) |

### Recomendacao

Executar a resolucao em 6 batches ao longo de 10-12 semanas, comecando imediatamente pelo Batch 0 (auditoria de seguranca de cobranca, 3 horas) e Batch 1 (quick wins, 5 horas). Estes dois batches sozinhos eliminam o unico item critico, corrigem a vulnerabilidade de cobranca, e resolvem 8 debitos com apenas R$ 1.200 de investimento. Os batches subsequentes devem ser intercalados com feature work, priorizando performance da landing page (Batch 2) para maximizar conversao de visitantes em trials.

---

## Analise de Custos

### Custo de RESOLVER

| Categoria | Items | Horas | Custo (R$150/h) |
|-----------|-------|-------|------------------|
| Sistema (Backend) | 18 | ~82h | R$ 12.300 |
| Frontend/UX | 22 | ~74h | R$ 11.100 |
| Cross-cutting | 6 | ~38h | R$ 5.700 |
| Database | 8 | ~2,3h | R$ 345 |
| **TOTAL** | **54** | **~196h** | **R$ 29.400** |

Para contexto: R$ 29.400 equivale a 74 assinaturas mensais do SmartLic Pro (R$ 397/mes). Com a base de usuarios crescendo, esse investimento se paga com a retencao de poucos clientes que seriam perdidos por problemas de performance ou cobranca.

### Custo de NAO RESOLVER (Risco Acumulado)

| Risco | Probabilidade | Impacto | Custo Potencial |
|-------|---------------|---------|-----------------|
| **Falha de cobranca por webhook duplicado** (DEBT-324) | Media (40%) | Clientes cobrados 2x, chargebacks, perda de confianca | R$ 5.000-20.000/incidente (chargebacks + suporte + dano reputacional) |
| **Queda do servidor por vazamento de memoria** (DEBT-323) | Alta (70% em 6 meses com crescimento) | Downtime, perda de trials ativos, dados de busca perdidos | R$ 2.000-10.000/incidente (receita perdida + recuperacao) |
| **Landing page lenta afasta visitantes** (TD-M07) | Certa (100%) | Cada 1s adicional de carregamento reduz conversao em ~7%* | R$ 500-2.000/mes em trials nao convertidos |
| **Inacessibilidade impede venda para governo** (XC-06) | Media (30% se expandir para governo) | Bloqueio de contratos publicos que exigem WCAG 2.1 AA | R$ 10.000-50.000/ano em contratos perdidos |
| **Complexidade desacelera desenvolvimento** (XC-02) | Certa (100%) | 6 arquivos com >1.500 linhas cada = onboarding lento, bugs mais frequentes | R$ 1.000-3.000/mes em produtividade perdida |
| **ComprasGov timeout desperdicado** (DEBT-313) | Certa (100%) | Fonte fora do ar consome budget de timeout em cada busca | R$ 200-500/mes em experiencia degradada |

*Fonte: Google/Deloitte, "Milliseconds Make Millions", 2020.

**Custo anualizado de inacao estimado: R$ 40.000 - 120.000**, considerando cenario de crescimento moderado (50-200 usuarios pagantes).

---

## Impacto no Negocio

### Performance — A Porta de Entrada Esta Lenta

A landing page do SmartLic (smartlic.tech) e o primeiro contato de potenciais clientes. Atualmente, 13 componentes sao carregados no navegador do usuario quando apenas 3 precisam disso. Os outros 10 poderiam ser renderizados no servidor, reduzindo o JavaScript enviado ao visitante em 40-60KB e melhorando significativamente o tempo de carregamento.

Para um produto B2G onde decisores frequentemente acessam de redes corporativas ou dispositivos moveis em campo, cada segundo conta. Um LCP (Largest Contentful Paint) acima de 2,5 segundos penaliza o posicionamento no Google e aumenta a taxa de rejeicao.

**Resolucao:** Batch 2 (10h, R$ 1.500) — conversao para Server Components com islands pattern.

### Seguranca — O Sistema de Cobranca Tem Dois Riscos

**Risco 1 — Processamento duplicado de webhooks (DEBT-324):** O Stripe envia notificacoes de pagamento ao SmartLic via webhooks. Atualmente, o sistema registra o receptor de webhooks em DOIS enderecos diferentes (`/v1/` e root). Se ambos estiverem ativos no Stripe Dashboard, cada evento de pagamento pode ser processado duas vezes — resultando em assinaturas duplicadas, cobrancas duplas, ou estados inconsistentes.

**Risco 2 — Vazamento de memoria no cache de planos (DEBT-323):** O sistema que verifica se um usuario tem plano ativo armazena resultados em um dicionario sem limite. Com o crescimento da base de usuarios, esse dicionario cresce indefinidamente ate consumir toda a memoria do servidor, causando queda.

**Resolucao:** Batch 0 (3h, R$ 450) para auditoria + Batch 1 (1h, R$ 150) para correcao do cache.

### Experiencia do Usuario — Acessibilidade Incompleta

Tres problemas de acessibilidade foram identificados:
1. **IDs duplicados na pagina** quebram navegacao por teclado (afeta usuarios com deficiencia motora)
2. **Indicadores de viabilidade usam apenas cor** — ~8% dos homens tem algum grau de daltonismo e nao conseguem distinguir "Alta" de "Baixa" viabilidade
3. **Pipeline kanban sem anuncios para leitores de tela** — usuarios de tecnologia assistiva nao conseguem usar o arrasta-e-solta

Para expansao no mercado governamental, conformidade com WCAG 2.1 AA pode ser exigencia contratual (Lei 13.146/2015 — Lei Brasileira de Inclusao).

**Resolucao:** Batch 3 (17h, R$ 2.550) — correcoes de acessibilidade + seguranca.

### Manutenibilidade — A Velocidade de Desenvolvimento Vai Cair

Seis arquivos no backend ultrapassam 1.500 linhas de codigo cada. O maior (filter/core.py) tem 3.871 linhas. Arquivos desse tamanho sao:

- **Dificeis de entender** — um novo desenvolvedor precisa de dias para se orientar
- **Dificeis de testar** — 14 arquivos de teste com 3.704 linhas dependem apenas do filter/core.py
- **Dificeis de modificar** — qualquer mudanca no filtro de busca (funcionalidade central) tem alto risco de regressao

Isso nao e critico hoje com uma equipe pequena onde todos conhecem o codigo. Mas se torna bloqueante no momento de contratar, terceirizar, ou acelerar entregas para aproveitar uma janela de mercado.

**Resolucao:** Batch 4 (32h, R$ 4.800) — decomposicao arquitetural com preservacao de interfaces.

---

## Timeline Recomendado

### Batch 0: Auditoria de Cobranca — 1 dia (3h)

**Investimento:** R$ 450
**Items:** DEBT-324 (auditoria + correcao de webhook duplicado do Stripe)
**Objetivo:** Verificar se houve processamento duplicado de pagamentos em producao.
**Acoes:** Verificar URL configurada no Stripe Dashboard, analisar logs de producao buscando event_ids duplicados, verificar chaves de idempotencia, remover registro duplicado.
**ROI:** Elimina risco de cobranca dupla. Se um unico incidente for evitado, paga o investimento 10x.

### Batch 1: Quick Wins — 1 semana (5h)

**Investimento:** R$ 750
**Items:** DEBT-323 (cache ilimitado), DB-H04 (integridade de timestamps), DB-M04/M05 (constraints), DA-01 (cache eviction), DEBT-322 (configs deslocadas), DEBT-325 (taxa de cambio hardcoded), TD-NEW-01 (IDs duplicados)
**Objetivo:** Eliminar o unico item CRITICO e 7 correcoes rapidas.
**ROI:** O item DEBT-323 sozinho previne queda do servidor. As correcoes de banco previnem corrupcao silenciosa de dados. Total: 8 debitos eliminados em ~5 horas.

### Batch 2: Performance da Landing Page — 2 semanas (10h)

**Investimento:** R$ 1.500
**Items:** TD-M07 (conversao de 10 componentes para Server Components)
**Objetivo:** Reduzir JavaScript da landing page em 40-60KB, atingir LCP < 2.5 segundos.
**ROI:** A landing page e o funil de aquisicao. Cada melhoria de velocidade impacta diretamente a taxa de conversao visitante-para-trial. Melhora tambem o SEO organico (Core Web Vitals sao fator de ranking do Google).

### Batch 3: Seguranca e Acessibilidade — 2 semanas (17h)

**Investimento:** R$ 2.550
**Items:** DEBT-307 (decomposicao de webhooks), TD-H04 (screen reader no pipeline), TD-NEW-02 (indicadores de viabilidade), TD-H02 (autenticacao unificada)
**Pre-requisito:** Instalar jest-axe (4h) para testes automatizados de acessibilidade.
**Objetivo:** Webhook handlers auditoraveis + conformidade basica de acessibilidade.
**ROI:** Webhooks decompostos permitem auditar logica de billing com confianca. Acessibilidade habilita venda para setor publico e demonstra compromisso com inclusao.

### Batch 4: Arquitetura — 3-4 semanas (32h)

**Investimento:** R$ 4.800
**Items:** DEBT-301 (filter/core.py 3.871 LOC), DEBT-304 (68 arquivos top-level), DEBT-302 (schemas.py 2.121 LOC), DEBT-305 (job_queue + cron_jobs 4.370 LOC combinados)
**Objetivo:** Nenhum arquivo com mais de 1.500 linhas. Estrutura de packages no backend.
**ROI:** Reducao de 30-50% no tempo de onboarding de novos desenvolvedores. Reduz risco de regressao em mudancas no filtro de busca. Viabiliza contratacao e terceirizacao.

### Batch 5: Melhoria Continua — 2-3 semanas (~47h)

**Investimento:** R$ 7.050
**Items:** 12 items de media prioridade (decomposicao de quota/cache, RSC em paginas protegidas, eliminacao de tipos `any`, padronizacao de proxies, limpeza de fonte morta ComprasGov, auditoria de feature flags)
**Objetivo:** Polimento geral e reducao de atrito no desenvolvimento.
**ROI:** Produtividade incremental. Pode ser intercalado com feature work.

### Batch 6: Polimento — Backlog continuo (~27h)

**Investimento:** R$ 4.050
**Items:** 13 items de baixa prioridade (skeletons, error boundaries, documentacao, lazy loading)
**Objetivo:** Items oportunisticos, priorizados quando ha capacidade ociosa ou quando coincidem com feature work na mesma area.
**ROI:** Marginal individualmente, cumulativo no longo prazo.

---

## ROI da Resolucao

| | Valor |
|---|-------|
| **Investimento total** | R$ 29.400 (196h x R$ 150/h) |
| **Risco anual evitado (conservador)** | R$ 40.000 |
| **Risco anual evitado (otimista)** | R$ 120.000 |
| **Payback no cenario conservador** | ~9 meses |
| **Payback no cenario otimista** | ~3 meses |

| Investimento | Retorno Esperado |
|--------------|------------------|
| R$ 450 (Batch 0) | Elimina risco de cobranca dupla — protege receita e confianca |
| R$ 750 (Batch 1) | Elimina risco de queda por memoria + integridade de dados |
| R$ 1.500 (Batch 2) | Melhora conversao da landing page — mais trials, mais receita |
| R$ 2.550 (Batch 3) | Habilita venda para governo + webhook auditavel |
| R$ 4.800 (Batch 4) | Reduz tempo de onboarding 30-50% — viabiliza crescimento da equipe |
| R$ 7.050 (Batch 5) | Produtividade incremental — features entregues mais rapido |
| R$ 4.050 (Batch 6) | Polimento — reduz atrito acumulado |

**Nota sobre priorizacao:** Os Batches 0, 1 e 2 representam apenas R$ 2.700 (9% do custo total) mas eliminam os maiores riscos (seguranca de cobranca, estabilidade do servidor, performance de aquisicao). Se o orcamento for limitado, estes tres batches sao o investimento minimo recomendado.

---

## Proximos Passos

1. [ ] **Aprovar Batch 0 + 1** — R$ 1.200, 8 horas, execucao imediata
2. [ ] **Executar auditoria de webhook do Stripe** (Batch 0) — verificar se houve double-processing
3. [ ] **Aplicar quick wins** (Batch 1) — correcao de memoria, integridade de banco, IDs duplicados
4. [ ] **Agendar Batch 2** para proxima sprint — landing page performance
5. [ ] **Aprovar orcamento completo** (R$ 29.400) ou definir limite por quarter
6. [ ] **Criar epic de resolucao** com stories por batch no backlog
7. [ ] **Definir cadencia de revisao** — reavaliar progresso a cada 2 semanas
8. [ ] **Estabelecer metricas de baseline** — Lighthouse score da landing, tempo medio de deploy, cobertura de testes

---

## Anexos

- **Assessment Tecnico Completo:** `docs/prd/technical-debt-assessment.md` (54 items, dependencias, criterios de sucesso, riscos e mitigacoes)
- **Inventario de Banco de Dados:** Secao 2.2 do assessment (8 items, 2.3h, saude geral 7/10)
- **Revisao de Frontend/UX:** Secao 2.3 do assessment (22 items, 74h, saude geral 7/10)
- **Items Ja Resolvidos:** Secao 8 do assessment (6 items confirmados como corrigidos, incluindo o unico CRITICAL de DB)
- **Gaps Conhecidos:** Secao 9 do assessment (4 areas nao cobertas: Redis resilience, error handling em jobs, security headers em proxies, rollback strategy)

---

*Este relatorio foi preparado com base na avaliacao tecnica conduzida por 4 especialistas (@architect, @data-engineer, @ux-design-expert, @qa) ao longo das Phases 4-7 do Brownfield Discovery. A taxa de erro de 18% identificada no draft inicial foi corrigida antes da publicacao, resultando em estimativas confiaveis e acionaveis.*
