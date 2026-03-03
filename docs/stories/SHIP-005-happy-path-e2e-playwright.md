# SHIP-005: Happy Path End-to-End Validation (Playwright)

**Status:** 🔴 Pendente
**Prioridade:** P0
**Sprint:** SHIP (Go-to-Market)
**Criado:** 2026-03-03
**Depende de:** SHIP-001

## Contexto

Validar manualmente via Playwright (browser MCP) o fluxo completo de um usuário real
em produção (https://smartlic.tech). Não é teste automatizado — é smoke test com evidências
visuais (screenshots) de cada etapa.

Objetivo: confirmar que um usuário que entra pela primeira vez consegue completar
o fluxo inteiro sem encontrar erros.

## Acceptance Criteria

### Landing & Auth

- [ ] AC1: Landing page (`/`) carrega sem erros de console, hero visível, CTAs funcionam
- [ ] AC2: Link "Cadastrar" leva para `/signup`
- [ ] AC3: Signup com email real → conta criada → email de confirmação recebido
- [ ] AC4: Login com credenciais → redirect para `/buscar` ou `/onboarding`

### Onboarding

- [ ] AC5: Onboarding step 1 — selecionar CNAE funciona
- [ ] AC6: Onboarding step 2 — selecionar UFs funciona
- [ ] AC7: Onboarding step 3 — confirmação + auto-search dispara

### Busca (Core Value)

- [ ] AC8: Busca manual — selecionar setor "Engenharia e Construção", UFs "SP,RJ", 10 dias
- [ ] AC9: Progress bar (SSE) mostra progresso real, não estático, não retrocede
- [ ] AC10: Resultados aparecem com: nome do edital, órgão, UF, valor estimado
- [ ] AC11: Badges de relevância (keyword/LLM) visíveis nos resultados
- [ ] AC12: Badge de viabilidade visível (score + cor)
- [ ] AC13: Tempo total de busca < 60 segundos

### Exportação

- [ ] AC14: Botão "Exportar Excel" gera download
- [ ] AC15: Arquivo .xlsx abre no Excel com formatação e dados corretos

### Pipeline

- [ ] AC16: Arrastar licitação para coluna "Em Análise" persiste (reload confirma)

### Dashboard

- [ ] AC17: Gráficos carregam, números fazem sentido (> 0 se há buscas)

### Planos

- [ ] AC18: `/planos` mostra pricing correto com toggle de billing period
- [ ] AC19: Botão "Assinar" redireciona para Stripe Checkout

### Conta

- [ ] AC20: Alterar senha funciona
- [ ] AC21: Trial badge mostra dias restantes corretamente

### Estabilidade

- [ ] AC22: Nenhum erro 500 durante todo o fluxo
- [ ] AC23: Nenhum console.error crítico no browser
- [ ] AC24: Nenhum novo issue no Sentry durante o teste

## Evidências

Cada AC deve ter um screenshot salvo em `docs/sessions/2026-03/ship-005-screenshots/`.
