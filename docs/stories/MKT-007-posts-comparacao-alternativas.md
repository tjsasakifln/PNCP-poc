# MKT-007 — Posts de Comparação e Alternativas (4 posts)

**Status:** pending
**Priority:** P1 — Maior intenção comercial (captura decisão de compra)
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/ (conteúdo editorial)
**Esforço:** 3-4 dias
**Timeline:** Mês 1-2

---

## Contexto

Posts de comparação e "alternativas a" capturam tráfego de alta intenção — pessoas que já estão avaliando soluções. Estes posts preenchem uma lacuna total no conteúdo existente (nenhum dos 30 posts aborda comparações). São os posts com maior taxa de conversão direta para trial.

### Evidências

- Product comparison posts têm a maior intenção comercial entre todos os tipos de conteúdo (Grow and Convert)
- G2: 6.6M visitas/mês vindas de páginas de comparação programáticas
- Posts "alternativa a [X]" capturam switching intent — usuários insatisfeitos com soluções existentes

## Posts a Criar

### Mês 1

- [ ] **Post 9:** "SmartLic vs. Busca Manual no PNCP: Quanto Tempo (e Dinheiro) Você Perde por Semana?" — 2.500 palavras
  - Keywords: "buscar licitações PNCP", "alternativa PNCP"
  - Schema: FAQPage + Article
  - Comparação honesta: tempo gasto, cobertura, filtros, alertas
  - Tabela comparativa lado-a-lado
  - Dados reais: "buscamos 1000 licitações em X min vs Y min manual"
  - **Não depreciar o PNCP** — posicionar como complemento inteligente

- [ ] **Post 10:** "5 Ferramentas de Monitoramento de Licitações no Brasil (Comparativo Honesto 2026)" — 3.000 palavras
  - Keywords: "melhor site para buscar licitações", "plataforma de licitações", "monitoramento de licitações"
  - Schema: FAQPage + Article + ItemList
  - Comparar: SmartLic, Portal de Compras Públicas, LiciteGov, Licitar Digital, busca manual
  - Critérios: fontes de dados, filtros, IA, preço, cobertura, UX
  - **Tom neutro** — apontar prós e contras de cada, SmartLic se destaca em IA + multi-fonte
  - Tabela comparativa com ✅/❌/parcial

### Mês 2

- [ ] **Post 11:** "Planilha de Licitações vs. Software de Pipeline: Quando Migrar?" — 2.200 palavras
  - Keywords: "planilha de licitações", "controle de licitações"
  - Schema: FAQPage + Article
  - Mostra limitações da planilha (manual, sem alertas, sem IA, dados desatualizados)
  - Framework de decisão: "Se você tem X, planilha basta. Se Y, precisa de pipeline."
  - Mostra o Kanban do SmartLic como evolução natural

- [ ] **Post 12:** "Buscar Licitação no Google vs. Plataforma Especializada: O Que os Dados Mostram" — 2.500 palavras
  - Keywords: "buscar licitação", "como achar licitações"
  - Schema: FAQPage + Article + Dataset
  - Teste real: mesma busca no Google vs. SmartLic — comparar resultados
  - Dados: cobertura (% de editais encontrados), falsos positivos, tempo gasto

## Acceptance Criteria

### AC1 — Tom e posicionamento

- [ ] Tom neutro e honesto — não ser panfletário
- [ ] Reconhecer pontos fortes de concorrentes/alternativas
- [ ] SmartLic se destaca por dados, não por marketing
- [ ] Nunca depreciar o PNCP ou portais governamentais — são fonte de dados do SmartLic

### AC2 — Estrutura de cada post

- [ ] Tabela comparativa visual (feature matrix)
- [ ] Front-loaded: conclusão nos primeiros 200 palavras
- [ ] FAQ: 5 perguntas de comparação (40-60 palavras cada)
- [ ] CTA: "Teste grátis 30 dias e compare você mesmo"
- [ ] Screenshots quando possível (SmartLic vs. alternativa)

### AC3 — SEO e schema

- [ ] Schema JSON-LD: `FAQPage` + `Article` + `ItemList` (quando aplicável)
- [ ] Meta title focado em keyword de comparação
- [ ] Internal links para posts "como fazer" (MKT-006) e páginas programáticas

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Parecer panfletário / perder credibilidade | Tom honesto, reconhecer limitações do SmartLic, dados reais |
| Concorrentes reclamarem de comparação | Focar em categorias (manual vs. automatizado) mais que em marcas específicas |
| Dados de concorrentes desatualizados | Indicar data da análise, oferecer atualização se informado |
| PNCP mudar sua UI/funcionalidades | Post baseado em princípios (manual vs. inteligente), não em detalhes de UI |

## Definição de Pronto

- [ ] 4 posts publicados
- [ ] Tabelas comparativas visuais em todos
- [ ] Tom validado como neutro/honesto
- [ ] Schema validado
- [ ] Commit com tag `MKT-007`
