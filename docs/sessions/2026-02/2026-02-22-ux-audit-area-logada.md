# Auditoria UX — Área Logada SmartLic (2026-02-22)

**Agente:** @ux-design-expert (Uma)
**Método:** Navegação real em produção via Playwright MCP
**Horário:** ~20:30-21:00 UTC
**Usuário teste:** Admin (tiago.sasaki@gmail.com)

---

## Veredicto Executivo

A área logada do SmartLic tem um **gap brutal entre a promessa da landing page e a experiência real de uso**. A landing page vende análise de viabilidade, justificativas objetivas, descarte inteligente. A área logada entrega uma busca que trava por 2+ minutos mostrando mensagens contraditórias, um dashboard vazio, e texto sem acentuação.

**Severidade: Churn imediato no primeiro uso.** O usuário que converteu do trial não vai encontrar NADA do que viu na landing page.

---

## Achados por Severidade

### BLOCKER — Impede uso do produto

#### B01. Busca travada com estado contraditório
- **O que acontece:** Ao buscar, aparece instantaneamente "Nenhuma Oportunidade Relevante Encontrada" + "302 resultados eliminados" ENQUANTO a barra inferior mostra "Atualizando dados em tempo real..."
- **Impacto:** Usuário acredita que não há resultados e sai. O grid de UFs aparece por 1-2s e some.
- **Evidência:** Screenshots audit-02, audit-03, audit-04 (mesma tela após 0s, 60s, 150s)
- **Causa provável:** O empty state é renderizado antes dos resultados do SSE chegarem. Resultados stale da busca anterior "vazam" para nova busca.

#### B02. Resultados de busca anterior contaminam nova busca
- **O que acontece:** Busquei Vestuário (0 relevantes, 302 eliminados). Troquei para Engenharia. A tela mostrou "302 resultados eliminados para engenharia" — número idêntico da busca anterior.
- **Impacto:** Dados incorretos, quebra de confiança.
- **Evidência:** Screenshot audit-08 (2 min após buscar Engenharia, ainda mostra 302)

#### B03. Dashboard completamente vazio
- **O que acontece:** Página /dashboard mostra apenas skeletons de loading que NUNCA resolvem.
- **Impacto:** Funcionalidade core inacessível. Console mostra "Error fetching plan info" (5x).
- **Evidência:** Screenshot audit-05

#### B04. "Atualizando dados em tempo real..." infinito
- **O que acontece:** Banner amarelo com spinner permanece indefinidamente (2+ minutos testados). Nunca desaparece. Nunca resolve.
- **Impacto:** Usuário não sabe se busca terminou ou não. Estado de limbo permanente.

### CRITICAL — Gap promessa vs. entrega (causa direta de churn)

#### C01. Landing page vende produto que não existe na área logada
| Landing page promete | Área logada entrega |
|---|---|
| "Recomendada" / "Descartada" por edital | Nenhum badge de recomendação visível |
| Score de compatibilidade (8.5/10) | Nenhum score visível |
| "Por que foi recomendada" (4 critérios) | Nenhuma justificativa por edital |
| Viabilidade Alta/Média/Baixa | Badge existe no código mas NUNCA aparece (feature flag OFF) |
| Cards elegantes com metadados | Resultados nunca carregaram no teste |
| "87% dos editais descartados" | "302 resultados eliminados" (número cru, sem contexto positivo) |

#### C02. Nenhum botão de download Excel visível
- **O que acontece:** Mesmo quando resultados existem (histórico mostra 153 para engenharia anterior), não há botão de Excel visível.
- **Status no código:** Existe componente condicional (excel_status === 'ready') mas depende de ARQ job que pode não completar.

#### C03. Google Sheets → HTTP 404
- **O que acontece:** Endpoint retorna 404.
- **Impacto:** Feature anunciada que não funciona.

#### C04. "Resumo por IA sendo preparado..." eterno
- **O que acontece:** Mensagem persiste indefinidamente. Usuário espera algo que nunca chega.
- **Causa:** ARQ job de LLM summary não completa ou SSE event `llm_ready` nunca chega.

#### C05. Busca não salva no histórico corretamente
- **O que acontece:** Ao entrar em Histórico pela primeira vez, mostrou "0 buscas". Após buscas, apareceram com status "Processando..." que nunca atualiza.
- **Evidência:** Duas entradas "vestuario Processando..." duplicadas no histórico.

### HIGH — Problemas de UX que causam frustração

#### H01. Grid de UFs aparece e some instantaneamente
- **O que acontece:** O grid com 27 estados e status "Aguardando.../Consultando..." aparece por ~1s e desaparece, substituído pelo empty state.
- **Impacto:** O feedback de progresso (que é bem desenhado!) é invisível na prática.
- **Sugestão:** Grid deve persistir durante toda a busca. Empty state só após conclusão TOTAL.

#### H02. Badges poluem sem agregar valor
- **"Palavra-chave"** — Jargão interno. Usuário não sabe o que significa.
- **"Alta-confianca"** — Sem cedilha (deveria ser "confiança"). E o que é "confiança" de uma licitação?
- **"FONTE OFICIAL"** — Todas são de fontes oficiais. É como restaurante dizer "comida de verdade".
- **Sugestão:** Remover "Palavra-chave" e "FONTE OFICIAL". Renomear "confiança" para "Relevância".

#### H03. "Recomendações do Consultor" sem contexto
- Não deixa claro que é inferência por IA baseada em perfil INCOMPLETO.
- Sem CTA para preencher perfil (que melhoraria as recomendações).
- Sem link para ver oportunidade na fonte oficial (PNCP/ComprasGov).
- Sem acentuação: "Recomendacoes" em vez de "Recomendações".

#### H04. Dobra inicial de resultados = enxurrada cognitiva
- Quando resultados chegam, tudo aparece de uma vez: summary card + badges + alertas + metadata + fonte + timestamp.
- Sem agrupamento, sem legendas, sem hierarquia visual clara.
- **Sugestão:** Progressive disclosure — summary hero primeiro, depois lista com cards colapsáveis.

#### H05. "Período de busca de 10 dias" / "dados de cache" expostos
- "Últimos 10 dias" visível na interface (é detalhe técnico).
- "Dados de cache" em banners é jargão de desenvolvedor.
- **Sugestão:** Substituir por "Oportunidades publicadas recentemente" ou convite "Volte diariamente para novas oportunidades".

### MEDIUM — Polish necessário para GTM (6 itens)

#### M01. Acentuação quebrada em toda a área logada
| Local | Texto atual | Correto |
|---|---|---|
| Sidebar | "Historico" | "Histórico" |
| Sidebar nav aria | "Navegacao principal" | "Navegação principal" |
| Histórico badges | "Concluida" | "Concluída" |
| Histórico badges | "vestuario" | "vestuário" |
| Pipeline vazio | "voce", "licitacoes", "inicio", "avanca" | "você", "licitações", "início", "avança" |
| Badges de resultado | "confianca" | "confiança" |
| Badges de resultado | "Recomendacoes" | "Recomendações" |
| Error detail | "tecnicos" | "técnicos" |
| Feedback | "Ja encerrada" | "Já encerrada" |

#### M02. Mensagens de erro em inglês
- Histórico mostra: "Server restart — retry recommended"
- Deveria: "O servidor reiniciou. Recomendamos repetir a busca."

#### M03. Histórico mostra todos 27 códigos de UF em linha
- "AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PR, PE, PI, RJ, RN, RO, RR, RS, SC, SP, SE, TO"
- Ruído visual. Quando é "Todo o Brasil", mostrar apenas "Todo o Brasil".

#### M04. Footer: "Sistema desenvolvido por servidores públicos"
- Texto incorreto/misleading. SmartLic é produto da CONFENGE (empresa privada).
- Footer da landing page está correto. Footer da área logada está errado.

#### M05. Sidebar: "Mensagens" deveria ser "Suporte"
- O link da sidebar diz "Mensagens" e leva para /mensagens.
- Para o usuário, isso é canal de suporte — o label deveria ser "Suporte" para alinhar com a linguagem da landing page e do footer.
- Landing page usa "Suporte" no header e no footer. Área logada usa "Mensagens". Inconsistência.

#### M06. 5 erros de console em todas as páginas
- "Error fetching plan info: TypeError: Failed..." em loop.
- Indica problema no fetch de informações de plano do usuário.

---

## Stories de Correção Propostas

### Prioridade 1 — Blockers (Sprint atual)

**UX-CRIT-020: Corrigir estado da busca — eliminar empty state prematuro**
- AC1: Empty state NUNCA aparece enquanto busca está em andamento
- AC2: Grid de UFs persiste durante toda a busca com progresso real
- AC3: Resultados de busca anterior são limpos ao iniciar nova busca
- AC4: "Atualizando dados em tempo real" desaparece quando busca conclui
- AC5: Se busca falha/timeout, mostrar mensagem clara com retry

**UX-CRIT-021: Corrigir Dashboard vazio**
- AC1: Dashboard carrega dados ou mostra empty state adequado (não skeleton eterno)
- AC2: Corrigir "Error fetching plan info" que causa 5 erros de console
- AC3: Empty state do dashboard tem CTA claro ("Faça sua primeira busca")

**UX-CRIT-022: Alinhar promessa da landing com entrega da área logada**
- AC1: Resultados mostram badge de viabilidade (Alta/Média/Baixa) — ligar feature flag
- AC2: Cada resultado tem link para fonte oficial (PNCP/ComprasGov)
- AC3: Summary mostra "X oportunidades selecionadas de Y analisadas" (framing positivo)
- AC4: Score de compatibilidade visível por resultado (como landing page mostra)

### Prioridade 2 — Critical (Próximo sprint)

**UX-FIX-040: Botão de download Excel visível e funcional**
- AC1: Botão "Baixar Excel" aparece assim que resultados estão disponíveis
- AC2: Se Excel ainda processando, mostrar estado de loading no botão
- AC3: Remover/esconder opção Google Sheets até funcionar (404 atual)

**UX-FIX-041: "Resumo por IA" com timeout e fallback**
- AC1: "Resumo por IA sendo preparado..." tem timeout de 30s
- AC2: Após timeout, mostrar resumo fallback (já existe `gerar_resumo_fallback`)
- AC3: Se IA completar depois, atualizar silenciosamente (sem "sendo preparado" eterno)

**UX-FIX-042: Recomendações do Consultor com contexto e CTA**
- AC1: Se perfil incompleto, banner: "Complete seu perfil para recomendações mais precisas" + link /conta
- AC2: Cada oportunidade recomendada tem link "Ver edital na fonte oficial"
- AC3: Acentuação corrigida: "Recomendações"

**UX-FIX-043: Histórico funcional**
- AC1: Toda busca é salva no histórico imediatamente ao iniciar
- AC2: Status atualiza de "Processando" para "Concluída"/"Falhou" quando busca termina
- AC3: "Todo o Brasil" em vez de listar 27 UFs quando todas selecionadas
- AC4: Mensagens de erro em português (não "Server restart — retry recommended")

### Prioridade 3 — Polish (Pré-GTM)

**UX-FIX-044: Acentuação, labels e i18n da área logada**
- AC1: Corrigir todos os textos sem acento listados na tabela M01
- AC2: Footer área logada = footer landing page (remover "servidores públicos")
- AC3: Aria labels com acentuação correta
- AC4: Sidebar "Mensagens" → "Suporte" (alinhar com landing page e footer)

**UX-FIX-045: Reduzir carga cognitiva dos resultados**
- AC1: Remover badges "FONTE OFICIAL" e "Palavra-chave"
- AC2: "Alta-confianca" → "Alta relevância" (com cedilha)
- AC3: "Últimos 10 dias" → "Oportunidades recentes" ou remover
- AC4: "Dados de cache" → "Atualizadas em [hora]" ou remover
- AC5: Convite "Volte diariamente para novas oportunidades" em vez de detalhes técnicos

**UX-FIX-046: Dobra de resultados — hierarquia visual**
- AC1: Summary hero card primeiro (resumo + valor total + contagem)
- AC2: Lista de oportunidades com cards colapsáveis
- AC3: Alertas agrupados e contextualizados (não enxurrada)
- AC4: Aderir ao design system (cores, tipografia, spacing consistentes)

---

## Screenshots Capturados

| # | Arquivo | Descrição |
|---|---|---|
| 1 | audit-01-search-page-initial.png | Página de busca antes de buscar |
| 2 | audit-02-search-in-progress.png | Estado contraditório: "Nenhuma" + "Atualizando" |
| 3 | audit-03-after-60s.png | 60s depois — mesma tela, zero progresso |
| 4 | audit-04-after-150s.png | 150s depois — ainda travado |
| 5 | audit-05-dashboard.png | Dashboard = skeletons vazios |
| 6 | audit-06-historico.png | Histórico com problemas de acento e status |
| 7 | audit-07-pipeline.png | Pipeline vazio com texto sem acentos |
| 8 | audit-08-engenharia-2min.png | Engenharia 2min — mostra 302 de vestuário (stale) |

---

## Nota sobre a mensagem do usuário

> "o que temos na pagina inicial na copy não é o que temos na área logada.. isso é churn"

**Confirmado com evidência.** A landing page é nota 8-9/10. A área logada é nota 2/10. Esse gap é a definição de churn — o usuário converte pela promessa e cancela pela entrega. Prioridade absoluta é UX-CRIT-022 (alinhar promessa com entrega).

> "deve ser pq o cache está vazio nesse setor e está buscando de ultima hora..mas usuario fica no escuro"

**Confirmado.** Quando não há cache, o usuário vê 2+ minutos de tela contraditória sem nenhum feedback real de progresso. O grid de UFs (que seria esse feedback) aparece por 1 segundo e some.
