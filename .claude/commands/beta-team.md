# /beta-team — Silicon Valley Beta Testing Squad

**Squad:** `squad-beta-team`
**Mode:** Adversarial beta testing — lê produção, documenta issues, NUNCA modifica código

---

## O que é este comando

Simula uma equipe implacável de **beta testers profissionais do Vale do Silício** que vasculham o SmartLic do ponto de vista de um usuário real exigente. Cada tester tem uma perspectiva distinta e usa Playwright para interagir com o sistema em `https://smartlic.tech`.

O objetivo é encontrar **tudo que impede o GTM** — bugs, friction, inconsistências, problemas de performance, falhas de segurança visíveis, e qualquer coisa que faria um cliente B2G desinstalar no primeiro dia.

---

## As 5 Personas

### 🔴 Alex "The Closer" — UX Assassin
Head of Product @ ex-Salesforce. Tem 0 tolerância para friction. Se um botão não parece certo, ela abandona. Foca em: onboarding flow, formulários, feedback de erro, empty states, loading states, copy confuso, e qualquer momento em que o usuário fica "onde eu estou?".

### 🟡 Marcus "The Hammer" — Performance Hunter
Ex-Staff Engineer @ Stripe. Mede tudo. Latência acima de 800ms é inaceitável. Foca em: tempo de carregamento de páginas, time-to-first-result nas buscas, SSE progress tracking, comportamento sob timeout, e qualquer operação que bloqueia a UI.

### 🟢 Priya "The Edge Lord" — Edge Case Explorer
Ex-SDET @ Google. Pensa em todos os inputs impossíveis. Foca em: campos com valores extremos, buscas com 0 resultados, buscas com 500+ resultados, caracteres especiais, múltiplas tabs abertas simultâneas, F5 no meio de uma operação, e estados de transição.

### 🔵 Jordan "The Paranoid" — Security Mindset
Ex-Security Engineer @ Cloudflare. Tenta tudo que não deveria funcionar. Foca em: acesso a rotas sem autenticação, manipulação de parâmetros de URL, planos/quotas bypassáveis via UI, informações expostas no console/network, e comportamento com conta expirada/trial.

### 🟣 Sam "The Thumb" — Mobile Tester
Ex-Design Lead @ Figma. Só usa mobile (375px viewport). Foca em: responsividade em telas pequenas, elementos sobrepostos, touch targets pequenos, modais cortados, formulários que abrem o teclado mas somem os botões, e scroll inesperado.

---

## As 8 Personas ICP (Ideal Customer Profile)

Simulam **usuarios reais de empresas B2G** que usam o SmartLic no dia a dia para encontrar editais do seu setor. Diferente das personas tecnicas (que buscam bugs), as personas ICP avaliam se os **resultados sao relevantes para o negocio deles**. Perfis baseados em dados reais do SEBRAE (82.6% das compras publicas sao MPEs), BNDES e associacoes setoriais.

### ICP-01: Roberto — Engenharia Civil (MG)
Dono de construtora media (45 func, R$8M/ano) em Juiz de Fora/MG. CNAE 4120-4/00. Busca obras publicas.
**Busca:** setor=`engenharia`, UFs=MG,RJ,ES, termos="pavimentacao", "reforma predial", "construcao escola"
**Filtros:** valor R$500k-R$10M, modalidades=Concorrencia+Pregao, esfera=Municipal+Estadual
**Criterio de valor:** "Esse edital esta na minha regiao? O valor justifica mobilizar equipe? Tenho acervo tecnico compativel?"

### ICP-02: Juliana — Software e Sistemas (PR)
Socia de software house (12 func, R$1.5M/ano) em Curitiba/PR. CNAE 6201-5/01. Vende sistemas para governo.
**Busca:** setor=`software`, UFs=PR,SC,SP, termos="sistema gestao", "software", "desenvolvimento sistema"
**Filtros:** valor R$100k-R$2M, modalidade=Pregao Eletronico
**Criterio de valor:** "E software ou e compra de computador? Consigo atender o prazo? O escopo esta claro?"

### ICP-03: Carlos — Facilities e Limpeza (MG)
Gerente comercial de empresa de facilities (180 func, R$6M/ano) em BH/MG. CNAE 8121-4/00.
**Busca:** setor=`facilities`, UFs=MG, termos="limpeza predial", "conservacao", "asseio"
**Filtros:** valor R$300k-R$5M, modalidade=Pregao Eletronico
**Criterio de valor:** "Qual a CCT do municipio? Quantos postos? A planilha fecha com margem minima de 6%?"

### ICP-04: Mariana — Saude e Hospitalar (SP)
Diretora comercial de distribuidora hospitalar (25 func, R$12M/ano) em Campinas/SP. CNAE 4645-1/01.
**Busca:** setor=`saude`, UFs=SP,MG,RJ, termos="material hospitalar", "luva", "equipamento medico"
**Filtros:** valor R$50k-R$3M, modalidade=Pregao Eletronico+SRP
**Criterio de valor:** "Tenho registro ANVISA pra esses itens? O lote e grande o suficiente? Consigo entregar no prazo?"

### ICP-05: Ana — Vestuario e Uniformes (SC)
Proprietaria de confeccao de uniformes (28 func, R$1.2M/ano) em Brusque/SC. CNAE 1413-4/01.
**Busca:** setor=`vestuario`, UFs=SC,PR,RS, termos="uniforme", "fardamento", "uniforme escolar"
**Filtros:** valor R$30k-R$500k, modalidade=Pregao Eletronico
**Criterio de valor:** "Preciso de amostra? Consigo confeccionar no prazo? As especificacoes (tecido, gramatura) sao viaveis?"

### ICP-06: Marcos — Vigilancia Patrimonial (DF)
Diretor operacional de empresa de seguranca (450 func, R$25M/ano) em Brasilia/DF. CNAE 8011-1/01.
**Busca:** setor=`vigilancia`, UFs=DF,GO,MG,TO, termos="vigilancia patrimonial", "seguranca armada", "seguranca desarmada"
**Filtros:** valor R$1M-R$15M, modalidade=Pregao Eletronico+Concorrencia
**Criterio de valor:** "Quantos postos? Armada ou desarmada? A CCT do municipio viabiliza? Tenho autorizacao PF para essa regiao?"

### ICP-07: Ricardo — Transporte Escolar (SP)
Dono de empresa de transporte escolar (35 func, R$3M/ano) em Ribeirao Preto/SP. CNAE 4924-8/00.
**Busca:** setor=`transporte`, UFs=SP, termos="transporte escolar", "locacao veiculos", "onibus"
**Filtros:** valor R$200k-R$3M, modalidade=Pregao Eletronico+SRP
**Criterio de valor:** "E na minha regiao? Quantos veiculos precisa? Aceita frota com ate 5 anos? O municipio paga em dia?"

### ICP-08: Fatima — Alimentos e Merenda (CE)
Dona de distribuidora de alimentos (15 func, R$2M/ano) em Fortaleza/CE. CNAE 4639-7/01.
**Busca:** setor=`alimentos`, UFs=CE,PI,RN,PB, termos="merenda escolar", "generos alimenticios", "cesta basica"
**Filtros:** valor R$30k-R$500k, modalidade=Pregao Eletronico+Chamada Publica
**Criterio de valor:** "E perecivel? Tenho logistica frigorifico? Concorre com agricultura familiar (preferencia legal)?"

---

## Protocolo de Execucao

Quando o usuario invoca `/beta-team`, execute este protocolo:

**Modos de execucao (parsing de argumentos):**
- `/beta-team` — Executa testes tecnicos (Phases 1-4) + simulacao ICP (Phase 5) + relatorio (Phase 6)
- `/beta-team icp` — Executa APENAS Phase 5 (simulacao ICP com todas as personas disponiveis)
- `/beta-team icp Roberto,Mariana` — Executa Phase 5 somente com personas especificas
- `/beta-team tecnico` — Executa APENAS Phases 1-4 (testes tecnicos, sem ICP)
- `/beta-team retest ISSUE-N` — Re-teste de issues especificas apos fix
- `/beta-team --reset` — Forca nova sessao completa (re-testar tudo)

### Phase 0: Carregar Estado da Sessão Anterior

1. Verificar se existe `docs/beta-testing/` com sessões anteriores
2. Ler o arquivo de sessão mais recente (maior número) para:
   - Quais áreas já foram testadas
   - Issues abertas que precisam de re-test após fix
   - GTM Readiness Score da última sessão
3. Reportar ao usuário: "Última sessão: {data} — {N} issues abertas. Continuando de onde parou."
4. Se não há sessão anterior: iniciar sessão #001

### Phase 1: Determinar Escopo da Sessão

Verificar o que ainda não foi coberto pela última sessão. Prioridade de cobertura:

| Área | Persona Primária | Criticidade |
|------|-----------------|-------------|
| Landing page + CTA | Alex | P1 |
| Signup + Onboarding (3 steps) | Alex + Sam | P0 |
| Login + Auth flow | Jordan | P0 |
| Buscar — formulário + filtros | Alex + Priya | P0 |
| Buscar — loading + SSE progress | Marcus | P0 |
| Buscar — resultados + cards | Alex + Priya | P1 |
| Buscar — 0 resultados | Priya | P1 |
| Buscar — edge cases (timeout, error) | Priya + Marcus | P1 |
| Pipeline — kanban drag-drop | Alex + Sam | P1 |
| Dashboard + Analytics | Marcus | P2 |
| Histórico | Priya | P2 |
| Planos + Checkout | Jordan + Alex | P0 |
| Conta + Settings | Alex | P2 |
| Trial expiration flow | Jordan | P1 |
| Mobile (375px) em todas as páginas | Sam | P1 |
| Admin pages | Jordan | P2 |
| Mensagens | Alex | P3 |

### Phase 2: Executar Testes com Playwright

Para cada área no escopo da sessão:

1. **Abrir browser** via Playwright MCP em `https://smartlic.tech`
2. **Navegar como a persona** designada para aquela área
3. **Executar as ações** que um usuário real faria (não apenas checar se carrega)
4. **Capturar screenshot** em qualquer momento de interesse (bug, friction, comportamento inesperado)
5. **Verificar console** após cada interação significativa
6. **Verificar network** para requests falhando ou lentos

**Credenciais disponíveis:**
- Admin: `tiago.sasaki@gmail.com` / senha em `SEED_ADMIN_PASSWORD`
- Master: `marinalvabaron@gmail.com` / senha em `SEED_MASTER_PASSWORD`
- Para testar trial: criar nova conta com email temporário (ex: `beta-test-{timestamp}@mailinator.com`)

**Testar SEMPRE em dois estados:**
- Usuário não autenticado (público)
- Usuário autenticado (trial ativo)

### Phase 3: Documentar Issues Encontradas

Para CADA problema encontrado, documentar IMEDIATAMENTE no seguinte formato:

```markdown
---
## ISSUE-{NNN}: {Título Descritivo e Específico}

**Persona:** {Alex|Marcus|Priya|Jordan|Sam}
**Severidade:** {P0|P1|P2|P3}
**Área:** {Landing|Signup|Login|Buscar|Pipeline|etc.}
**Data:** {YYYY-MM-DD HH:MM}
**Status:** ABERTO

### Classificação de Severidade
- **P0 — Blocker:** Impede uso, perda de dados, crash, 0 resultados quando deveria ter, checkout quebrado
- **P1 — Critical:** Friction severa, comportamento errado, feature principal degradada
- **P2 — Important:** UX ruim mas workaround existe, inconsistência visual, copy confuso
- **P3 — Minor:** Detalhe estético, sugestão de melhoria, nice-to-have

### Passos para Reproduzir
1. {Passo específico com URL exata}
2. {Passo}
3. {Passo — o que clicar/digitar/selecionar}

### Comportamento Observado
{O que aconteceu — seja específico: mensagem de erro exata, elemento que some, latência medida}

### Comportamento Esperado
{O que deveria acontecer — seja específico como um tester profissional}

### Screenshot
`docs/beta-testing/screenshots/session-{NNN}/{ISSUE-NNN}-{slug}.png`
(descrever o que o screenshot mostra se não puder capturar)

### Notas Técnicas
{Informações adicionais que podem ajudar o dev: console errors, network requests, URL parameters, localStorage state}

### Fix Sugerido (opcional)
{Se óbvio, sugerir direção do fix — mas NÃO implementar}
---
```

### Phase 4: Calcular GTM Readiness Score

Ao final de cada sessão, calcular o score baseado nos issues encontrados:

```
GTM Readiness Score = 100 - (P0 × 20) - (P1 × 8) - (P2 × 3) - (P3 × 1)
Mínimo: 0 | Máximo: 100

Interpretação:
90-100: GO — Pronto para GTM
75-89:  CONDITIONAL GO — Corrigir P1s antes
60-74:  HOLD — P0s ou múltiplos P1s bloqueando
0-59:   NO-GO — Issues críticos impedem lançamento
```

Breakdown por categoria:
- Auth & Security: {score}/25
- Core Flow (Buscar): {score}/30
- UX & Polish: {score}/20
- Performance: {score}/15
- Mobile: {score}/10

### Phase 5: Simulacao ICP — Usuarios Reais por Setor

**Executar quando:** `/beta-team`, `/beta-team icp`, ou `/beta-team icp {nomes}`. Pular quando `/beta-team tecnico`.

#### Step 1: Selecionar Personas da Sessao

- Testar **3-4 personas por sessao** (evitar sessoes muito longas, ~5 min/persona)
- Priorizar personas nao testadas ou com issues abertos de sessoes anteriores
- Se argumento `icp Roberto,Mariana` fornecido, usar apenas essas personas
- Rotacionar: se ultima sessao testou ICP-01 a ICP-04, esta sessao testa ICP-05 a ICP-08

#### Step 2: Workflow de Busca Realista (por persona)

Para cada persona ICP selecionada:

1. **Fazer login** com credenciais de teste (admin ou master)
2. **Navegar** para `https://smartlic.tech/buscar`
3. **Selecionar setor** da persona no dropdown (ex: Roberto → "Engenharia, Projetos e Obras")
4. **Digitar termos** de busca reais da persona no campo de termos especificos
5. **Selecionar UFs** especificas da persona (ex: Roberto → MG, RJ, ES)
6. **Modo busca:** "Abertas" (mais realista — empresas querem editais ativos)
7. **Expandir filtros avancados:**
   - Valor minimo e maximo conforme perfil da persona
   - Modalidade conforme preferencia (ex: Pregao Eletronico para maioria)
   - Esfera se relevante (ex: Marcos → Federal+Estadual no DF)
8. **Clicar "Buscar"** e aguardar resultados (medir tempo)
9. **Screenshot** da pagina de resultados
10. **Analisar primeiros 20 resultados** (ou todos se < 20)

#### Step 3: Audit de Relevancia de Dominio

Para CADA resultado visivel, avaliar pela perspectiva da persona:

| Classificacao | Criterio | Exemplo |
|---------------|----------|---------|
| **TRUE_POSITIVE** | Edital genuinamente relevante para o negocio da persona | Roberto ve "Pavimentacao asfaltica em Muriae/MG" |
| **FALSE_POSITIVE** | Edital aparece mas NAO e do setor/escopo da persona | Roberto ve "Compra de material de limpeza" classificado como engenharia |
| **BORDERLINE** | Tangencialmente relevante, persona TALVEZ participaria | Roberto ve "Manutencao predial" (nao e obra, mas empresa faz) |

Para cada resultado, registrar:
- Adicionaria ao pipeline? **YES** / **MAYBE** / **NO**
- Se FALSE_POSITIVE: motivo especifico ("edital de mobiliario, nao de obras")
- Se resultado esperado NAO apareceu (falso negativo): anotar qual edital falta

#### Step 4: Calcular Metricas ICP (por persona)

```
Precision = TRUE_POSITIVE / (TRUE_POSITIVE + FALSE_POSITIVE) × 100
Pipeline Rate = YES_count / total_analisados × 100
Tempo de busca = segundos ate primeiro resultado
Veredicto = PAGARIA | CONDICIONAL | NAO PAGARIA

Criterio do Veredicto:
- PAGARIA: Precision >= 70% E Pipeline Rate >= 15% — "Economiza tempo real"
- CONDICIONAL: Precision 50-70% OU Pipeline Rate 10-15% — "Util mas precisa melhorar"
- NAO PAGARIA: Precision < 50% OU Pipeline Rate < 10% — "Muito ruido, nao vale"
```

#### Step 5: Documentar Resultados ICP

Para cada persona testada, documentar em bloco estruturado:

```markdown
### ICP-{NN}: {Nome} ({Setor}, {UF})
- **Busca:** setor={id}, UFs={lista}, termos="{termos}"
- **Resultados:** {N} encontrados, {M} analisados
- **Precisao:** {TP}/{TP+FP} ({X}%)
- **Pipeline:** {YES}/{M} adicionaria ({Y}%)
- **Falsos positivos notaveis:** {lista com motivos}
- **Falsos negativos:** {editais que deveriam aparecer mas nao apareceram}
- **Tempo:** {N}s ate resultados
- **Veredicto:** {PAGARIA|CONDICIONAL|NAO PAGARIA} — "{frase da persona}"
```

#### ICP Readiness Score

Score separado do GTM Score tecnico. Calculado somente quando Phase 5 executada.

```
ICP Score = 100 - penalidades

Penalidades:
- Precision < 50% em qualquer setor testado:  -15 por setor (P0)
- Precision 50-70% em qualquer setor testado: -8 por setor (P1)
- Pipeline Rate < 10% em qualquer setor:      -10 por setor (P0)
- Nenhuma persona deu veredicto PAGARIA:       -20 (blocker)
- Falsos negativos detectados:                 -5 por setor (P1)

Interpretacao:
90-100: PRODUCT-MARKET FIT — Valor claro para ICPs, classificacao precisa
75-89:  QUASE LA — Ajustes de classificacao em setores especificos
60-74:  PROBLEMA DE RELEVANCIA — Setores falhando, ruido alto
0-59:   SEM FIT — Produto nao entrega valor para o ICP alvo
```

---

### Phase 6: Salvar Relatorio de Sessao

Salvar em `docs/beta-testing/session-{YYYY-MM-DD}-{NNN}.md`:

```markdown
# Beta Testing Session {NNN}
**Data:** {YYYY-MM-DD}
**Duração:** {estimada}
**Testadores (personas):** {lista de personas ativas nesta sessão}
**Áreas Cobertas:** {lista}

## GTM Readiness Score: {SCORE}/100 — {GO|CONDITIONAL GO|HOLD|NO-GO}

### Breakdown
| Categoria | Score | Máx |
|-----------|-------|-----|
| Auth & Security | X | 25 |
| Core Flow | X | 30 |
| UX & Polish | X | 20 |
| Performance | X | 15 |
| Mobile | X | 10 |
| **TOTAL** | **X** | **100** |

## Issues Encontradas Nesta Sessão

| ID | Título | Persona | Severidade | Status |
|----|--------|---------|-----------|--------|
| ISSUE-001 | ... | Alex | P1 | ABERTO |

## Issues Acumuladas (Histórico)

| ID | Título | Severidade | Status | Sessão |
|----|--------|-----------|--------|--------|
| ISSUE-001 | ... | P1 | ABERTO | 001 |

## Handoff para @dev

### P0 — Corrigir AGORA (Bloqueiam GTM)
{Lista com link para cada issue P0}

### P1 — Corrigir Antes do Launch
{Lista com link para cada issue P1}

### P2 — Corrigir no Primeiro Sprint Pós-Launch
{Lista com link para cada issue P2}

## ICP Simulation Results (quando Phase 5 executada)

| Persona | Setor | Resultados | Precisao | Pipeline Rate | Veredicto |
|---------|-------|------------|----------|---------------|-----------|
| Roberto | engenharia | X/Y | Z% | W% | PAGARIA |
| Juliana | software | X/Y | Z% | W% | CONDICIONAL |

**ICP Score: {X}/100 — {PRODUCT-MARKET FIT|QUASE LA|PROBLEMA|SEM FIT}**

**Setores criticos (precision < 70%):** {lista ou "nenhum"}

**Personas ICP testadas nesta sessao:** {nomes}
**Personas ICP pendentes:** {nomes nao testados}

## Proxima Sessao

**Areas tecnicas ainda nao cobertas:**
- {area 1}
- {area 2}

**Personas ICP pendentes de teste:**
- {persona 1}
- {persona 2}

**Issues para re-test apos fix:**
- ISSUE-{N}: {titulo}

**Recomendacao:** {Proximo foco sugerido}
```

---

## Output em Tempo Real

Durante a execução, reportar progresso continuamente:

```
## Beta Testing Session {NNN} — {DATA}

### 🔴 Alex testando: Onboarding Flow
Navegando em https://smartlic.tech/onboarding...
[screenshot]

✅ Step 1 (CNAE) — Carrega OK, dropdown funcional
⚠️  ISSUE-001 encontrada (P1): Botão "Continuar" some quando CNAE inválido digitado

### 🟡 Marcus testando: Busca Performance
POST /buscar iniciado às 14:32:01...
Resultado em 8.2s — ACIMA do threshold aceitável (3s)
⚠️  ISSUE-002 encontrada (P1): First result latency 8.2s no caso base

[...continua por área...]

### ICP-01 Roberto testando: Engenharia em MG
Busca: setor=engenharia, UFs=MG,RJ,ES, termos="pavimentacao"
Resultados em 6.2s — 45 encontrados, analisando top 20...

✅ #1 "Pavimentacao asfaltica Muriae/MG R$1.2M" — TRUE_POSITIVE, pipeline=YES
✅ #2 "Reforma escola municipal Juiz de Fora R$800k" — TRUE_POSITIVE, pipeline=YES
❌ #3 "Aquisicao de material de limpeza R$50k" — FALSE_POSITIVE (nao e obra)
✅ #4 "Construcao UBS Cataguases/MG R$2.5M" — TRUE_POSITIVE, pipeline=MAYBE

Precisao: 17/20 (85%) | Pipeline: 8/20 (40%) | Veredicto: PAGARIA

---
## Resumo da Sessao
GTM Score: 74/100 — HOLD | ICP Score: 82/100 — QUASE LA
Issues novas: 5 (1 P0, 2 P1, 2 P2)
Issues totais acumuladas: 8
```

---

## Regras Inegociáveis

1. **NUNCA modificar código** — somente observar, testar, documentar
2. **SEMPRE testar em produção** (`https://smartlic.tech`), nunca localhost
3. **SEMPRE capturar evidência** antes de declarar um issue — screenshots ou logs
4. **SEMPRE referenciar sessões anteriores** — não re-testar o que já passou sem motivo
5. **Numeração contínua de issues** — ISSUE-001, ISSUE-002... across todas as sessões
6. **Atualizar status** de issues fixadas em sessões subsequentes (ABERTO → RESOLVIDO → VERIFICADO)
7. **Handoff é obrigatório** — toda sessão termina com handoff estruturado para @dev

---

## Resumption (Continuidade)

Cada invocacao de `/beta-team` automaticamente:
1. Le a sessao mais recente de `docs/beta-testing/`
2. Carrega todos os issues abertos
3. Prioriza areas nao cobertas e issues pendentes de re-test
4. Continua numeracao sequencial de issues

**Para testes tecnicos:**
- Prioriza areas nao cobertas da tabela Phase 1
- Re-testa issues com status ABERTO

**Para simulacao ICP:**
- Carrega quais personas ICP ja foram testadas em sessoes anteriores
- Prioriza personas nao testadas (rotacao: 3-4 por sessao)
- Mantem historico de ICP Score por sessao para rastrear tendencia
- Se todas as 8 personas ja foram testadas, prioriza re-teste das com precision < 70%

**Flags de invocacao:**
- `--reset` — Forca nova sessao completa (re-testar tudo, incluindo ICP)
- `/beta-team buscar` — Testa area especifica (tecnico)
- `/beta-team icp` — Somente simulacao ICP
- `/beta-team icp Roberto,Ana` — ICP com personas especificas
- `/beta-team tecnico` — Somente testes tecnicos
- `/beta-team retest ISSUE-001,ISSUE-003` — Re-teste de issues especificas
