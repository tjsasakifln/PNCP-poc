# GTM Production Test Checklist — SmartLic

**Squad:** @qa (Quinn) + @dev (Dex) + @ux-design-expert (Uma)
**Ambiente:** Producao (`https://smartlic.tech`)
**Contas de teste:**
- Admin: `tiago.sasaki@gmail.com` (env `SEED_ADMIN_PASSWORD`)
- Master: `marinalvabaron@gmail.com` (env `SEED_MASTER_PASSWORD`)
- Trial: Criar conta nova para cada rodada de testes

**Criterio de aprovacao:** 100% P0, 95% P1, 80% P2

---

## Legenda

| Prioridade | Significado | Bloqueante? |
|------------|-------------|-------------|
| **P0** | Bloqueante para GTM — sistema inutilizavel se falhar | SIM |
| **P1** | Critico — experiencia severamente degradada | SIM (>2 falhas) |
| **P2** | Importante — impacto moderado, workaround existe | NAO |
| **P3** | Desejavel — polimento, edge cases | NAO |

---

## FASE 1 — FLUXOS CRITICOS (P0)

### 1.1 Cadastro e Primeiro Acesso

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 1.1.1 | Signup com email novo | 1. Acessar `/signup` 2. Preencher email+senha validos 3. Submeter | Tela de confirmacao aparece, email recebido em <60s | P0 | [ ] |
| 1.1.2 | Confirmacao de email | 1. Clicar link no email 2. Aguardar redirect | Redirect para `/onboarding`, usuario logado | P0 | [ ] |
| 1.1.3 | Reenviar confirmacao | 1. Na tela de confirmacao, clicar "Reenviar" 2. Aguardar | Novo email em <60s, botao desabilitado por 60s | P1 | [ ] |
| 1.1.4 | Signup com email duplicado | 1. Tentar cadastrar email ja existente | Mensagem de erro clara, sem expor se email existe | P1 | [ ] |
| 1.1.5 | Signup com email descartavel | 1. Tentar cadastrar com email `@guerrillamail.com` | Bloqueado com mensagem amigavel | P2 | [ ] |
| 1.1.6 | Validacao de senha | 1. Tentar senha <8 chars 2. Sem maiuscula 3. Sem digito | Cada regra mostrada em tempo real, botao desabilitado | P1 | [ ] |

### 1.2 Login

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 1.2.1 | Login email+senha | 1. `/login` 2. Credenciais validas 3. Submit | Redirect para `/buscar` (ou `/onboarding` se primeiro acesso) | P0 | [ ] |
| 1.2.2 | Login Google OAuth | 1. Clicar "Entrar com Google" 2. Autorizar | Redirect para app, sessao criada | P0 | [ ] |
| 1.2.3 | Login senha incorreta | 1. Email valido + senha errada | Mensagem "Email ou senha incorretos" (generica) | P1 | [ ] |
| 1.2.4 | Sessao persistente | 1. Login 2. Fechar aba 3. Reabrir `smartlic.tech` | Sessao mantida, sem re-login | P0 | [ ] |
| 1.2.5 | Logout | 1. Menu usuario > Sair | Redirect para `/login`, sessao destruida | P1 | [ ] |
| 1.2.6 | Redirect pos-login | 1. Acessar `/buscar` sem login 2. Fazer login | Redirect de volta para `/buscar` apos login | P1 | [ ] |
| 1.2.7 | Sessao expirada | 1. Esperar token expirar (ou invalidar manualmente) | Banner "Sessao expirada" com botao de re-login | P1 | [ ] |

### 1.3 Onboarding (Primeiro Acesso)

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 1.3.1 | Step 1 — CNAE e Objetivo | 1. Selecionar CNAE 2. Escolher objetivo | Validacao funciona, pode avancar | P0 | [ ] |
| 1.3.2 | Step 2 — UFs e Valor | 1. Selecionar UFs (min 1) 2. Definir faixa de valor | Validacao funciona, pode avancar | P0 | [ ] |
| 1.3.3 | Step 3 — Confirmacao | 1. Revisar dados 2. Confirmar | Auto-search dispara, redirect para `/buscar?auto=true` | P0 | [ ] |
| 1.3.4 | Navegacao entre steps | 1. Avancar 2. Voltar 3. Verificar dados mantidos | Dados preservados ao navegar entre steps | P1 | [ ] |
| 1.3.5 | Auto-search pos-onboarding | 1. Completar onboarding 2. Observar busca automatica | Busca inicia com parametros do onboarding, progress SSE funciona | P0 | [ ] |

### 1.4 Busca Principal (Core Business)

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 1.4.1 | Busca basica | 1. `/buscar` 2. Selecionar setor 3. Selecionar UFs 4. Clicar "Buscar" | 202 em <2s, SSE progress inicia, resultados aparecem | P0 | [ ] |
| 1.4.2 | SSE progress tracking | 1. Iniciar busca 2. Observar barra de progresso | Updates por UF aparecem, percentual avanca, heartbeat a cada 15s | P0 | [ ] |
| 1.4.3 | Resultados com cards | 1. Aguardar busca completar 2. Ver lista de resultados | Cards com: titulo, orgao, UF, valor, modalidade, data, badges de relevancia | P0 | [ ] |
| 1.4.4 | Filtros de resultados | 1. Apos resultados, aplicar filtros (UF, valor, modalidade) | Resultados filtrados em tempo real, contadores atualizados | P0 | [ ] |
| 1.4.5 | Busca sem resultados | 1. Buscar com filtros muito restritivos (UF=AC, setor raro) | Tela vazia amigavel com sugestoes de relaxar filtros | P1 | [ ] |
| 1.4.6 | Busca multi-UF | 1. Selecionar 5+ UFs 2. Buscar | Todas UFs processadas, progress mostra cada UF, dedup funciona | P0 | [ ] |
| 1.4.7 | Busca com todas fontes | 1. Buscar setor popular (Construcao) em SP | Resultados de PNCP + PCP v2, badges de fonte visiveis | P0 | [ ] |
| 1.4.8 | Classificacao IA | 1. Buscar setor com resultados mistos | Badges de classificacao (keyword/llm_standard/llm_zero_match) visiveis | P1 | [ ] |
| 1.4.9 | Viabilidade 4-fatores | 1. Buscar e ver resultados 2. Verificar badge de viabilidade | Score de viabilidade (Alta/Media/Baixa) em cada card | P1 | [ ] |
| 1.4.10 | Cancelar busca | 1. Iniciar busca 2. Clicar "Cancelar" | Busca para, resultados parciais exibidos (se houver) | P1 | [ ] |
| 1.4.11 | Busca com faixa de valor | 1. Definir min R$100.000 e max R$1.000.000 2. Buscar | Apenas resultados dentro da faixa | P1 | [ ] |
| 1.4.12 | Paginacao de resultados | 1. Busca com muitos resultados 2. Navegar paginas | Paginacao funciona, scroll to top | P1 | [ ] |

### 1.5 Download e Exportacao

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 1.5.1 | Download Excel | 1. Buscar 2. Clicar "Baixar Excel" | Arquivo .xlsx baixado com dados formatados, colunas corretas | P0 | [ ] |
| 1.5.2 | Excel conteudo | 1. Abrir Excel baixado | Dados batem com resultados da tela, formatacao profissional | P0 | [ ] |
| 1.5.3 | Excel com muitos itens | 1. Busca com 50+ resultados 2. Baixar | Excel gerado sem timeout, todos itens presentes | P1 | [ ] |
| 1.5.4 | Relatorio PDF | 1. Clicar "Gerar Relatorio" (se disponivel) | PDF gerado com scoring de viabilidade | P1 | [ ] |

---

## FASE 2 — FLUXOS COMERCIAIS (P0-P1)

### 2.1 Trial de 14 Dias

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 2.1.1 | Trial ativo — acesso total | 1. Login com conta trial (dia 1-5) | Acesso total: busca, pipeline, dashboard, export | P0 | [ ] |
| 2.1.2 | Trial expirando — banner | 1. Login com conta trial (dia 6+) | Banner amarelo "Seu trial expira em X dias" visivel | P1 | [ ] |
| 2.1.3 | Trial expirado — paywall | 1. Login com conta trial expirada | Tela de conversao fullscreen com valor analisado | P0 | [ ] |
| 2.1.4 | Trial expirado — pipeline readonly | 1. Trial expirado 2. Acessar `/pipeline` | Pipeline visivel mas drag-and-drop bloqueado, CTA de upgrade | P1 | [ ] |
| 2.1.5 | Contador de buscas trial | 1. Verificar `/trial-status` | Buscas usadas/limite corretos, dias restantes corretos | P1 | [ ] |
| 2.1.6 | Quota trial excedida | 1. Esgotar quota de buscas do trial | Mensagem amigavel com CTA de upgrade | P0 | [ ] |

### 2.2 Checkout e Pagamento

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 2.2.1 | Pagina de planos | 1. Acessar `/planos` | SmartLic Pro com 3 periodos (mensal/semestral/anual), precos corretos | P0 | [ ] |
| 2.2.2 | Toggle de periodo | 1. Clicar entre mensal/semestral/anual | Precos atualizados: R$397, R$357 (-10%), R$297 (-25%) | P0 | [ ] |
| 2.2.3 | Iniciar checkout | 1. Clicar "Assinar" 2. Redirect para Stripe | Checkout Stripe abre com plano/periodo corretos | P0 | [ ] |
| 2.2.4 | Checkout com cartao teste | 1. Usar cartao `4242 4242 4242 4242` no Stripe | Pagamento processado, redirect para `/planos/obrigado` | P0 | [ ] |
| 2.2.5 | Pos-checkout — plano ativo | 1. Apos checkout 2. Verificar `/conta/plano` | Plano SmartLic Pro ativo, data de renovacao correta | P0 | [ ] |
| 2.2.6 | Checkout cancelado | 1. Iniciar checkout 2. Fechar janela Stripe | Retorno para `/planos`, sem cobranca | P1 | [ ] |
| 2.2.7 | Pagamento falhou | 1. Usar cartao de teste que falha | Banner de falha de pagamento, opcao de tentar novamente | P1 | [ ] |

### 2.3 Gestao de Assinatura

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 2.3.1 | Status da assinatura | 1. `/conta/plano` com plano ativo | Plano atual, proxima renovacao, buscas restantes | P0 | [ ] |
| 2.3.2 | Portal Stripe | 1. Clicar "Gerenciar assinatura" | Redirect para Stripe Customer Portal | P1 | [ ] |
| 2.3.3 | Cancelar assinatura | 1. `/conta/plano` > "Cancelar" 2. Confirmar 3. Feedback | Assinatura cancelada ao fim do periodo, feedback salvo | P1 | [ ] |
| 2.3.4 | Mudar periodo de cobranca | 1. Assinante mensal > mudar para anual | Preco atualizado, proration automatica pelo Stripe | P2 | [ ] |

---

## FASE 3 — FEATURES SECUNDARIAS (P1-P2)

### 3.1 Pipeline (Kanban)

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 3.1.1 | Visualizar pipeline | 1. `/pipeline` | 5 colunas: Descoberta, Analise, Preparando, Enviada, Resultado | P1 | [ ] |
| 3.1.2 | Adicionar item ao pipeline | 1. Buscar 2. No resultado, clicar "Adicionar ao pipeline" | Card aparece na coluna "Descoberta" | P1 | [ ] |
| 3.1.3 | Drag-and-drop | 1. Arrastar card entre colunas | Card movido, status persistido no backend | P1 | [ ] |
| 3.1.4 | Editar notas do card | 1. Clicar card 2. Editar notas 3. Salvar | Notas persistidas, modal fecha | P2 | [ ] |
| 3.1.5 | Excluir card | 1. Clicar card 2. Excluir | Card removido, confirmacao previa | P2 | [ ] |
| 3.1.6 | Alertas de deadline | 1. Card com prazo proximo | Borda vermelha, alerta visivel | P2 | [ ] |

### 3.2 Dashboard

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 3.2.1 | Metricas resumo | 1. `/dashboard` | Cards: total buscas, downloads, oportunidades, valor descoberto | P1 | [ ] |
| 3.2.2 | Grafico temporal | 1. Ver grafico de buscas no tempo | Dados por semana/mes/ano, interativo | P1 | [ ] |
| 3.2.3 | Top UFs e Setores | 1. Ver ranking de UFs e setores | Top 5 UFs e setores mais buscados | P2 | [ ] |
| 3.2.4 | Dashboard vazio | 1. Login com conta sem historico | Estado vazio amigavel com CTA para buscar | P2 | [ ] |

### 3.3 Historico

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 3.3.1 | Listar historico | 1. `/historico` | Lista de buscas anteriores com data, setor, UFs, qtd resultados | P1 | [ ] |
| 3.3.2 | Carregar busca salva | 1. Clicar em busca do historico | Formulario preenchido com parametros da busca anterior | P1 | [ ] |
| 3.3.3 | Historico vazio | 1. Conta nova sem buscas | Estado vazio com CTA | P2 | [ ] |

### 3.4 Conta e Perfil

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 3.4.1 | Ver perfil | 1. `/conta/perfil` | Nome, email, empresa exibidos | P1 | [ ] |
| 3.4.2 | Editar perfil | 1. Alterar nome/empresa 2. Salvar | Dados atualizados, toast de sucesso | P2 | [ ] |
| 3.4.3 | Alterar senha | 1. `/conta/seguranca` 2. Senha atual + nova 3. Salvar | Senha alterada, toast de sucesso | P1 | [ ] |
| 3.4.4 | Senha errada na troca | 1. Informar senha atual incorreta | Erro claro sem revelar detalhes | P2 | [ ] |
| 3.4.5 | Recuperar senha | 1. `/recuperar-senha` 2. Informar email 3. Verificar inbox | Email com link de reset recebido em <60s | P1 | [ ] |
| 3.4.6 | Reset de senha via link | 1. Clicar link do email 2. Definir nova senha | Senha atualizada, redirect para login | P1 | [ ] |

### 3.5 Mensagens (se ativo)

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 3.5.1 | Criar conversa | 1. `/mensagens` 2. Nova conversa 3. Enviar mensagem | Conversa criada, mensagem salva | P2 | [ ] |
| 3.5.2 | Listar conversas | 1. Ver lista de conversas | Ordenadas por data, unread badge | P2 | [ ] |
| 3.5.3 | Responder conversa | 1. Abrir conversa 2. Enviar resposta | Resposta adicionada ao thread | P2 | [ ] |

---

## FASE 4 — RESILIENCIA E DEGRADACAO (P0-P1)

### 4.1 Fontes de Dados

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 4.1.1 | PNCP funcionando | 1. Buscar e verificar resultados PNCP | Resultados com badge "PNCP", dados completos | P0 | [ ] |
| 4.1.2 | PCP v2 funcionando | 1. Buscar e verificar resultados PCP | Resultados com badge "PCP", valor_estimado=0 (esperado) | P1 | [ ] |
| 4.1.3 | Fonte indisponivel | 1. Se uma fonte estiver fora, verificar comportamento | Resultados parciais exibidos, banner de degradacao | P0 | [ ] |
| 4.1.4 | Todas fontes fora | 1. Se todas fontes falharem | Cache servido (se disponivel) OU mensagem amigavel | P0 | [ ] |
| 4.1.5 | Cache stale servido | 1. Busca com dados em cache | Banner "Dados em cache de X horas atras" visivel | P1 | [ ] |

### 4.2 Timeouts e Circuit Breakers

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 4.2.1 | Busca lenta (>30s) | 1. Buscar muitas UFs + setor amplo | Progress SSE continua, heartbeat a cada 15s, sem timeout | P0 | [ ] |
| 4.2.2 | Timeout parcial | 1. Busca que timeout em algumas UFs | Resultados parciais + banner indicando UFs que falharam | P1 | [ ] |
| 4.2.3 | SSE desconexao | 1. Iniciar busca 2. Simular perda de rede (DevTools offline) 3. Reconectar | Fallback para simulacao por timer OU reconexao automatica | P1 | [ ] |
| 4.2.4 | Backend reiniciando | 1. Observar comportamento se backend reiniciar | Indicador de status (verde/vermelho), fila de busca se offline | P1 | [ ] |

### 4.3 LLM e IA

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 4.3.1 | Resumo com IA | 1. Buscar 2. Verificar resumo executivo | Resumo gerado ou fallback deterministico | P1 | [ ] |
| 4.3.2 | LLM indisponivel | 1. Se OpenAI estiver lento/fora | Fallback para classificacao keyword-only, sem LLM badge | P1 | [ ] |
| 4.3.3 | Zero-match classification | 1. Buscar com resultados de 0% keyword density | Itens classificados via LLM com badge "llm_zero_match" | P2 | [ ] |

---

## FASE 5 — SEGURANCA E PROTECAO (P0-P1)

### 5.1 Autenticacao e Autorizacao

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 5.1.1 | Acesso sem login | 1. Acessar `/buscar` direto (sem cookie) | Redirect para `/login?reason=login_required` | P0 | [ ] |
| 5.1.2 | Token invalido | 1. Manipular cookie de sessao | Redirect para `/login?reason=session_expired` | P0 | [ ] |
| 5.1.3 | Admin sem permissao | 1. Conta normal acessa `/admin` | Bloqueado, redirect ou 403 | P0 | [ ] |
| 5.1.4 | Rate limiting | 1. Fazer 100+ requests em 1 minuto | 429 Too Many Requests apos limite | P1 | [ ] |
| 5.1.5 | CORS | 1. Request de dominio nao autorizado | Bloqueado pelo CORS | P1 | [ ] |
| 5.1.6 | RLS — dados de outro usuario | 1. Tentar acessar pipeline/historico de outro user via API | Nenhum dado retornado (RLS bloqueia) | P0 | [ ] |

### 5.2 Inputs e Validacao

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 5.2.1 | XSS no formulario | 1. Inserir `<script>alert(1)</script>` em campo de busca | HTML escapado, sem execucao | P0 | [ ] |
| 5.2.2 | SQL injection | 1. Inserir `'; DROP TABLE --` em campo | Pydantic valida, sem execucao SQL raw | P0 | [ ] |
| 5.2.3 | Campos obrigatorios | 1. Submeter formularios vazios | Validacao client-side + server-side, mensagens claras | P1 | [ ] |
| 5.2.4 | Valores extremos | 1. Valor max = R$999.999.999.999 | Validacao server-side, sem crash | P2 | [ ] |

### 5.3 HTTPS e Headers

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 5.3.1 | HTTPS enforced | 1. Acessar via HTTP | Redirect 301 para HTTPS | P0 | [ ] |
| 5.3.2 | Security headers | 1. Inspecionar response headers | HSTS, X-Frame-Options: DENY, CSP, nosniff | P1 | [ ] |
| 5.3.3 | Cookie flags | 1. Inspecionar cookies de sessao | HttpOnly, Secure, SameSite=Lax | P1 | [ ] |

---

## FASE 6 — MOBILE E RESPONSIVIDADE (P1-P2)

### 6.1 Mobile (375px)

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 6.1.1 | Landing mobile | 1. Acessar `/` em 375px | Layout correto, sem overflow horizontal, CTAs visiveis | P1 | [ ] |
| 6.1.2 | Login mobile | 1. `/login` em 375px | Formulario usavel, botoes touch-friendly (44px+) | P1 | [ ] |
| 6.1.3 | Busca mobile | 1. `/buscar` em 375px | Filtros em accordion, resultados empilhados, scroll OK | P1 | [ ] |
| 6.1.4 | Resultados mobile | 1. Ver resultados em 375px | Cards legiveis, botoes acessiveis | P1 | [ ] |
| 6.1.5 | Pipeline mobile | 1. `/pipeline` em 375px | View em tabs (nao kanban), navegacao entre colunas | P2 | [ ] |
| 6.1.6 | Navegacao mobile | 1. Verificar BottomNav e MobileDrawer | Menu inferior visivel, drawer funcional | P1 | [ ] |
| 6.1.7 | Onboarding mobile | 1. Completar onboarding em 375px | Steps navegaveis, sem overflow | P1 | [ ] |

### 6.2 Tablet (768px)

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 6.2.1 | Busca tablet | 1. `/buscar` em 768px | Layout intermediario funcional | P2 | [ ] |
| 6.2.2 | Dashboard tablet | 1. `/dashboard` em 768px | Graficos redimensionados, legiveis | P2 | [ ] |

---

## FASE 7 — ADMIN E MONITORAMENTO (P1-P2)

### 7.1 Admin Dashboard

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 7.1.1 | Acesso admin | 1. Login admin 2. `/admin` | Dashboard com metricas, lista de usuarios | P1 | [ ] |
| 7.1.2 | Health das fontes | 1. Verificar status de PNCP, PCP, ComprasGov | Status (verde/vermelho), latencia, ultima verificacao | P1 | [ ] |
| 7.1.3 | Cache health | 1. `/admin/cache` | Hit/miss rates, TTL, tamanho do cache | P2 | [ ] |
| 7.1.4 | Search trace | 1. Buscar trace de uma search_id especifica | Timeline completa: fontes consultadas, tempos, erros | P2 | [ ] |

### 7.2 Monitoramento

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 7.2.1 | Health endpoint | 1. `GET /health` | 200 com status de DB, Redis, dependencias | P0 | [ ] |
| 7.2.2 | Metricas Prometheus | 1. `GET /metrics` | Metricas expostas: latency, error rate, cache hits | P1 | [ ] |
| 7.2.3 | Sentry errors | 1. Verificar Sentry dashboard | Sem erros P0 nao tratados nas ultimas 24h | P1 | [ ] |

---

## FASE 8 — PAGINAS PUBLICAS E SEO (P2)

### 8.1 Landing e Marketing

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 8.1.1 | Landing page | 1. Acessar `/` (deslogado) | Hero, problema, solucao, como funciona, stats, CTA | P1 | [ ] |
| 8.1.2 | Pricing page | 1. Acessar `/planos` (deslogado) | Planos com precos, toggle de periodo, FAQ | P1 | [ ] |
| 8.1.3 | Termos e Privacidade | 1. Acessar `/termos` e `/privacidade` | Conteudo legal completo e atualizado | P2 | [ ] |
| 8.1.4 | Ajuda | 1. Acessar `/ajuda` | Centro de ajuda com artigos/FAQ | P2 | [ ] |
| 8.1.5 | Meta tags SEO | 1. Inspecionar `<head>` das paginas publicas | Title, description, og:image, canonical URL | P2 | [ ] |
| 8.1.6 | Redirect railway → smartlic.tech | 1. Acessar URL do Railway diretamente | 301 redirect para `smartlic.tech` | P1 | [ ] |

---

## FASE 9 — PERFORMANCE (P1-P2)

### 9.1 Tempos de Resposta

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 9.1.1 | TTFB landing | 1. Medir TTFB de `/` | <1.5s (target Lighthouse) | P2 | [ ] |
| 9.1.2 | TTFB buscar (logado) | 1. Medir TTFB de `/buscar` | <2s | P1 | [ ] |
| 9.1.3 | Resposta POST /buscar | 1. Medir tempo do 202 Accepted | <2s | P0 | [ ] |
| 9.1.4 | Busca completa (1 UF) | 1. Buscar 1 UF, medir ate resultados | <15s | P1 | [ ] |
| 9.1.5 | Busca completa (5 UFs) | 1. Buscar 5 UFs, medir ate resultados | <45s | P1 | [ ] |
| 9.1.6 | Excel download | 1. Medir tempo de geracao do Excel | <10s para 50 itens | P2 | [ ] |

### 9.2 Lighthouse Scores

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 9.2.1 | Performance landing | 1. Lighthouse em `/` | Score >= 70 | P2 | [ ] |
| 9.2.2 | Performance buscar | 1. Lighthouse em `/buscar` | Score >= 60 | P2 | [ ] |
| 9.2.3 | Accessibility | 1. Lighthouse a11y em paginas principais | Score >= 80 | P2 | [ ] |

---

## FASE 10 — EDGE CASES E REGRESSAO (P2-P3)

### 10.1 Edge Cases

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 10.1.1 | Busca simultanea | 1. Iniciar 2 buscas ao mesmo tempo (2 abas) | Ambas funcionam independentemente | P2 | [ ] |
| 10.1.2 | Duplo-click no botao | 1. Duplo-click em "Buscar" | Apenas 1 busca disparada | P2 | [ ] |
| 10.1.3 | Refresh durante busca | 1. F5 durante busca em andamento | Busca continua ou mensagem de busca em andamento | P2 | [ ] |
| 10.1.4 | Back button | 1. Ir para resultados 2. Clicar "Voltar" | Volta para busca com filtros preservados | P2 | [ ] |
| 10.1.5 | Caracteres especiais | 1. Buscar com acentos: "Construcao", "Saude" | Funciona normalmente | P2 | [ ] |
| 10.1.6 | Navegador sem JS | 1. Verificar meta tags e noscript | Mensagem de fallback | P3 | [ ] |

### 10.2 Regressoes Conhecidas

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 10.2.1 | PNCP page size | 1. Verificar que backend usa tamanhoPagina<=50 | Sem HTTP 400 silencioso | P0 | [ ] |
| 10.2.2 | PCP UF filtering | 1. Buscar UF especifica via PCP | Apenas resultados da UF selecionada (client-side filter) | P1 | [ ] |
| 10.2.3 | SSE heartbeat | 1. Busca longa (>30s) 2. Verificar Network tab | Heartbeat comments a cada 15s, sem BodyTimeoutError | P1 | [ ] |
| 10.2.4 | Sync fallback eliminado | 1. Busca longa 2. Verificar que nao ha fallback sincrono | Sem HTTP 524, apenas async | P0 | [ ] |

---

## FASE 11 — INTEGRACAO E WEBHOOKS (P1)

### 11.1 Stripe Webhooks

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 11.1.1 | Webhook checkout.session.completed | 1. Completar checkout 2. Verificar DB | plan_type atualizado, profiles.plan_type sincronizado | P0 | [ ] |
| 11.1.2 | Webhook invoice.payment_failed | 1. Simular falha de pagamento | Banner de falha no frontend, email enviado | P1 | [ ] |
| 11.1.3 | Webhook customer.subscription.deleted | 1. Cancelar via Stripe | Plano revertido, acesso limitado | P1 | [ ] |
| 11.1.4 | Webhook signature verification | 1. Enviar webhook sem assinatura valida | 400 Bad Request, webhook rejeitado | P1 | [ ] |

### 11.2 Emails Transacionais

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 11.2.1 | Email de boas-vindas | 1. Criar conta nova | Email recebido com branding correto | P1 | [ ] |
| 11.2.2 | Email de confirmacao | 1. Signup 2. Verificar inbox | Link funcional, expira em 1h | P0 | [ ] |
| 11.2.3 | Email de reset de senha | 1. Solicitar reset | Link funcional, expira em 1h | P1 | [ ] |
| 11.2.4 | Email de trial expirando | 1. Verificar se email automatico e enviado | Email com CTA de upgrade, metricas de valor | P2 | [ ] |

---

## FASE 12 — CROSS-BROWSER (P2)

### 12.1 Compatibilidade

| # | Teste | Passos | Resultado Esperado | P | Status |
|---|-------|--------|-------------------|---|--------|
| 12.1.1 | Chrome (desktop) | 1. Fluxo completo de busca | Funcional, sem erros de console | P1 | [ ] |
| 12.1.2 | Firefox (desktop) | 1. Login + Busca + Download | Funcional | P2 | [ ] |
| 12.1.3 | Safari (desktop) | 1. Login + Busca + Download | Funcional, SSE compativel | P2 | [ ] |
| 12.1.4 | Chrome mobile (Android) | 1. Fluxo mobile completo | Touch OK, layout responsivo | P2 | [ ] |
| 12.1.5 | Safari mobile (iOS) | 1. Fluxo mobile completo | Touch OK, layout responsivo, SSE funcional | P2 | [ ] |
| 12.1.6 | Edge (desktop) | 1. Login + Busca basica | Funcional | P3 | [ ] |

---

## RESUMO EXECUTIVO

### Totais por Prioridade

| Prioridade | Quantidade | Bloqueante |
|------------|-----------|------------|
| P0 | 35 testes | SIM — todos devem passar |
| P1 | 58 testes | SIM se >2 falhas |
| P2 | 38 testes | NAO |
| P3 | 2 testes | NAO |
| **TOTAL** | **133 testes** | |

### Estimativa de Execucao

| Fase | Testes | Tempo Estimado |
|------|--------|----------------|
| Fase 1 — Fluxos Criticos | 30 | 3-4h |
| Fase 2 — Fluxos Comerciais | 17 | 2h |
| Fase 3 — Features Secundarias | 22 | 2-3h |
| Fase 4 — Resiliencia | 11 | 1-2h |
| Fase 5 — Seguranca | 11 | 1-2h |
| Fase 6 — Mobile | 9 | 1h |
| Fase 7 — Admin | 7 | 1h |
| Fase 8 — Paginas Publicas | 6 | 30min |
| Fase 9 — Performance | 8 | 1h |
| Fase 10 — Edge Cases | 10 | 1h |
| Fase 11 — Integracoes | 8 | 1-2h |
| Fase 12 — Cross-Browser | 6 | 1h |
| **TOTAL** | **133** | **~16-20h** |

### Criterio GO/NO-GO

| Decisao | Condicao |
|---------|----------|
| **GO** | 100% P0 pass + <=2 P1 fail + sem regressao critica |
| **GO com ressalvas** | 100% P0 pass + 3-5 P1 fail com workaround documentado |
| **NO-GO** | Qualquer P0 fail OU >5 P1 fail |

### Pre-requisitos

1. Conta trial nova criada para testes (nao usar contas existentes)
2. Stripe em modo de teste (test keys) ou producao com cartao teste
3. Acesso admin para verificar health e metricas
4. DevTools aberto para monitorar Network/Console
5. Dispositivo mobile real OU emulador Chrome DevTools (375px)
6. Acesso ao Sentry para verificar erros
7. Acesso ao Railway logs para verificar backend

---

*Gerado por Squad @qa + @dev + @ux-design-expert*
*Data: 2026-03-25*
*Versao: 1.0*
