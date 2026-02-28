# MKT-010 — Sistema de Distribuição LinkedIn + Dark Social

**Status:** pending
**Priority:** P1 — Quick Win (custo zero, alcance imediato)
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** Processos e templates (não código)
**Esforço:** 2-3 dias (setup), ongoing 3h/semana
**Timeline:** Semana 1 (início imediato)

---

## Contexto

LinkedIn gera 277% mais leads B2B que qualquer outra plataforma. Porém, links externos são penalizados em 60% pelo algoritmo. A estratégia é criar conteúdo nativo no LinkedIn (carrosséis, dados, stories) que entrega valor completo sem exigir clique — capturando leads via DM e comentários. Complementada por distribuição em dark social (WhatsApp/Telegram), que representa 80%+ do compartilhamento B2B.

### Evidências

- LinkedIn: 277% mais leads B2B (HubSpot State of Marketing, 2026)
- Links externos: -60% alcance (Richard van der Blom Study, 2025)
- Perfis pessoais: 65% do feed allocation vs 5% para páginas de empresa
- Dark social: 80%+ do compartilhamento B2B real (Altair Media)

## Acceptance Criteria

### AC1 — Série "Dados que Ninguém Mostra" (3x/semana no LinkedIn)

- [ ] Template de post: dado surpreendente extraído dos posts do blog + insight + sem link externo
- [ ] Formatos: carrossel (5-7 slides com dados visuais), document post, texto com tabela
- [ ] CTA: "Comente '[PALAVRA]' que eu mando o relatório completo" → captura via DM → link blog → trial
- [ ] **Nunca link no post principal** — link no primeiro comentário ou via DM
- [ ] Banco de 15 posts prontos antes de iniciar (buffer de 5 semanas)

Exemplos de posts:
1. "O governo brasileiro publicou 4.237 licitações na última semana. 68% foram de apenas 5 setores. Aqui está a distribuição:" → carrossel com gráfico
2. "Analisamos 10.000 licitações com IA. O resultado: 73% dos editais são irrelevantes para o setor que os buscou. Aqui está o porquê:" → carrossel
3. "Ranking: qual estado brasileiro publica mais licitações? A resposta pode te surpreender:" → carrossel com mapa

### AC2 — Série "Erros que Custam Contratos" (2x/semana no LinkedIn)

- [ ] Template: história + erro comum + consequência financeira + solução prática
- [ ] Tom: narrativo, empático, baseado em padrões reais (não invenções)
- [ ] CTA: "Se você quer [resultado], comenta '[PALAVRA]' que eu mando o método"
- [ ] Banco de 10 posts prontos

Exemplos:
1. "Uma empresa de TI de Curitiba perdeu 3 pregões seguidos. O problema não era o preço. Era que ela só descobria os editais faltando 48h para o prazo..."
2. "Uma consultoria me procurou porque seu cliente perdeu R$350k em contratos. O diagnóstico: 40h/mês lendo editais que descartava..."

### AC3 — Série "Bastidores do SmartLic" (1x/semana no LinkedIn)

- [ ] Template: building in public — métricas reais, decisões de produto, dados de uso
- [ ] Tom: transparente, técnico mas acessível
- [ ] Objetivo: credibilidade + curiosidade → visita ao site → trial

Exemplos:
1. "Na última semana, o SmartLic analisou 12.847 licitações com IA. 73% descartadas automaticamente. O que a IA encontrou nos 27% que sobraram:"
2. "Construímos um pipeline que busca em 3 fontes governamentais ao mesmo tempo. Aqui está a arquitetura (e por que foi tão difícil):"

### AC4 — Operação do perfil pessoal do fundador

- [ ] Perfil pessoal do fundador como canal primário (65% do feed)
- [ ] Página da empresa como canal secundário (5% do feed)
- [ ] Repost seletivo de posts pessoais no perfil da empresa (1-2/semana)
- [ ] Hashtags relevantes: #LicitacoesPublicas #B2G #GovTech #Licitacao #ComprasPublicas #PNCP
- [ ] Horários ideais: terça-quinta, 7h-9h ou 17h-19h (horário BR)

### AC5 — WhatsApp/Telegram — "Radar Semanal" (ver MKT-011)

- [ ] Cross-reference com MKT-011 — conteúdo do Radar alimenta posts LinkedIn
- [ ] Dados do Radar geram 2-3 posts de "Dados que Ninguém Mostra" por semana

### AC6 — Métricas e tracking

- [ ] UTM links únicos por canal: `utm_source=linkedin&utm_medium=dm`, `utm_source=whatsapp`
- [ ] Tracking de leads capturados via DM (planilha ou CRM simples)
- [ ] Review semanal: quais posts tiveram mais engajamento → feedback para temas do blog

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Dependência do fundador | Criar sistema de templates + dados → draft automático; expandir para 2-3 perfis |
| Inconsistência na cadência | Buffer de 15 posts prontos; se faltar tempo, manter apenas "Dados" (3x) |
| Engagement farming vs. valor real | Cada post deve entregar insight completo, não isca vazia |
| DM scaling não sustentável | Preparar respostas-template; links diretos para blog com UTM |
| Alcance cair se LinkedIn mudar algoritmo | Diversificar: WhatsApp (MKT-011) como canal paralelo |

## Definição de Pronto

- [ ] 15 posts "Dados que Ninguém Mostra" prontos em banco
- [ ] 10 posts "Erros que Custam Contratos" prontos em banco
- [ ] 5 posts "Bastidores" prontos em banco
- [ ] Templates de resposta para DMs
- [ ] UTM tracking configurado
- [ ] Calendário editorial de 4 semanas montado
- [ ] Commit com tag `MKT-010`
