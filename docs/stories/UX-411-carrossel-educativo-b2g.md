# STORY-411: Substituir progress bar por carrossel educativo B2G

**Prioridade:** P1
**Esforço:** L
**Squad:** team-bidiq-frontend

## Contexto
O componente `EnhancedLoadingProgress` exibe 5 estágios técnicos ("Consultando fontes oficiais", "Buscando dados", "Filtrando resultados", etc.) com countdown ("7s / ~25s", "~18s restantes") que gera ansiedade. O usuário não precisa saber que estamos na etapa 3 de 5 — ele precisa de uma experiência de espera que agregue valor. A proposta é substituir os indicadores de estágio e o countdown por um carrossel de dicas/curiosidades sobre licitações, mantendo apenas um spinner minimalista com "Analisando oportunidades...". Estudos de UX mostram que conteúdo educativo durante loading reduz a percepção de espera (NN/g, Smashing Magazine).

## Problema (Causa Raiz)
- `frontend/components/EnhancedLoadingProgress.tsx:54-85`: `STAGES[]` com 5 estágios técnicos expostos ao usuário.
- Linhas 341-357: Display `{elapsedTime}s / ~{estimatedTime}s` e `~{remaining}s restantes` — cria ansiedade e é impreciso.
- Linhas 375-419: Stage indicators (círculos numerados 1-5) — informação técnica sem valor para usuário.

## Critérios de Aceitação
- [ ] AC1: Remover os 5 stage indicators (círculos numerados) do componente visual.
- [ ] AC2: Remover display de countdown (`{elapsedTime}s / ~{estimatedTime}s` e `~{remaining}s restantes`).
- [ ] AC3: Manter progress bar (barra azul animada) mas sem porcentagem numérica. Barra deve animar suavemente de 0% a 95% usando o cálculo assintótico existente.
- [ ] AC4: Manter spinner SVG com texto "Analisando oportunidades..." (singular, sem detalhes técnicos).
- [ ] AC5: Adicionar carrossel de dicas B2G que troca automaticamente a cada 6 segundos com transição fade. Conteúdo inicial (15 dicas):

  1. "O Brasil homologou mais de R$ 1 trilhão em contratações públicas em 2025. Sua empresa pode capturar parte desse mercado."
  2. "Empate ficto (5%): No pregão eletrônico, se sua proposta estiver até 5% acima e você for ME/EPP, você pode cobrir o lance vencedor."
  3. "Licitações exclusivas até R$ 80 mil podem ser reservadas para micro e pequenas empresas (LC 123/2006)."
  4. "Desde a Lei 14.133/2021, o PNCP é o canal oficial obrigatório para publicação de editais de todos os entes federativos."
  5. "Inversão de fases: Na nova lei, propostas são julgadas ANTES da habilitação — agilizando o processo decisivamente."
  6. "Pregão eletrônico é a modalidade mais usada no Brasil, representando mais de 60% das contratações públicas."
  7. "Você pode participar de licitações em qualquer estado do Brasil, independente de onde sua empresa está sediada."
  8. "Contratos públicos costumam ter pagamento garantido por dotação orçamentária — menor risco de inadimplência que o setor privado."
  9. "A margem de preferência para produtos nacionais pode chegar a 25% em determinados setores estratégicos."
  10. "Consórcio de empresas: Pequenas empresas podem se unir em consórcio para participar de licitações maiores."
  11. "O prazo médio para pagamento em contratos públicos é de 30 dias após a entrega — preveja isso no fluxo de caixa."
  12. "Atestados de capacidade técnica são o documento mais importante na habilitação. Mantenha-os sempre atualizados."
  13. "Inexigibilidade de licitação: Se sua empresa oferece serviço exclusivo, pode contratar diretamente com o órgão público."
  14. "A pesquisa de preços no PNCP permite consultar valores históricos para formar preço competitivo nas suas propostas."
  15. "Certidões negativas (FGTS, INSS, Fazenda) são exigidas em praticamente todas as licitações. Mantenha-as em dia."

- [ ] AC6: Manter display "X de Y estados processados" na parte inferior (útil e não causa ansiedade).
- [ ] AC7: Manter mensagens de overtime (`getOvertimeMessage`) para buscas que excedem o tempo estimado.
- [ ] AC8: Manter funcionalidade de cancel button.
- [ ] AC9: Manter tratamento de estado degradado (amber scheme) e timeout overlay.
- [ ] AC10: Carrossel deve ter indicadores de dots (pontos) na parte inferior para mostrar posição.
- [ ] AC11: Carrossel deve pausar animação quando usuário passa o mouse por cima (hover pause).
- [ ] AC12: Interface interna (props do componente) não deve mudar — manter compatibilidade com `useSearch` e `page.tsx`.

## Arquivos Impactados
- `frontend/components/EnhancedLoadingProgress.tsx` — Rewrite do render: remover stages, countdown; adicionar carrossel.
- `frontend/__tests__/EnhancedLoadingProgress.test.tsx` — Atualizar testes para nova estrutura.

## Testes Necessários
- [ ] Teste que carrossel renderiza pelo menos 1 dica.
- [ ] Teste que carrossel troca dica após 6s (fake timers).
- [ ] Teste que progress bar anima sem mostrar porcentagem.
- [ ] Teste que spinner e texto "Analisando oportunidades..." estão presentes.
- [ ] Teste que stages indicators NÃO estão no DOM.
- [ ] Teste que countdown (`~Xs restantes`) NÃO está no DOM.
- [ ] Teste que overtime message ainda aparece.
- [ ] Teste que cancel button funciona.
- [ ] Teste que estado degraded (amber) funciona.
- [ ] Teste que hover pausa o carrossel.
- [ ] Snapshot visual do novo componente.

## Notas Técnicas
- Carrossel pode usar `setInterval` com `useState` para index rotation. Limpar no cleanup.
- Transição fade: `transition-opacity duration-500` com troca de `opacity-0/opacity-100`.
- NÃO usar biblioteca de carrossel externa — é um carrossel simples de texto.
- O cálculo assintótico existente (linhas 173-178) deve ser preservado para a barra de progresso.
- As props (`sseEvent`, `useRealProgress`, `statesProcessed`, etc.) devem continuar sendo aceitas e usadas internamente para lógica de progresso, mas não expostas visualmente como stages.
- Os testes existentes em `__tests__/EnhancedLoadingProgress.test.tsx` precisarão de refatoração significativa.
- Referências: NN/g Skeleton Screens 101, Smashing Magazine Carousel UX, Clay.global Skeleton Screen design patterns.
