# MKT-011 — Radar Semanal de Licitações (PDF Automático)

**Status:** pending
**Priority:** P1 — Quick Win (viralidade dark social, custo zero)
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** backend/ (geração PDF), distribuição manual/automatizada
**Esforço:** 3-4 dias
**Timeline:** Mês 1

---

## Contexto

PDF de 1 página com as top licitações da semana, gerado automaticamente pelo SmartLic e distribuído em grupos de WhatsApp/Telegram de licitações. É o growth loop mais direto: cada PDF tem branding SmartLic + CTA para trial, e é compartilhado organicamente em dezenas de grupos B2G.

### Evidências

- Dark social: 80%+ do compartilhamento B2B real (WhatsApp, Telegram, DMs)
- PDFs são o formato mais compartilhado em grupos de WhatsApp B2B no Brasil
- Custo de produção: zero (dados já existem no SmartLic, geração automatizada)
- Cada compartilhamento é um endosso implícito (peer recommendation)

## Acceptance Criteria

### AC1 — Geração automática do PDF

- [ ] Script/endpoint que gera PDF de 1 página com:
  - **Header:** "Radar SmartLic — Semana {DD/MM} a {DD/MM/AAAA}"
  - **Logo SmartLic** no topo
  - **Top 10 licitações da semana** (selecionadas por viabilidade score):
    - Objeto (resumido em 1 linha)
    - Valor estimado
    - Órgão
    - UF
    - Modalidade
    - Data limite
  - **Dado destaque:** "Esta semana: {X} novas licitações em {Y} setores"
  - **CTA rodapé:** "Gerado pelo SmartLic — Inteligência em Licitações | Teste grátis: smartlic.tech"
  - **QR code:** link para `/signup?utm_source=radar&utm_medium=whatsapp`
- [ ] Opção de gerar por setor (radar setorial): top 10 do setor específico
- [ ] Agendamento: geração automática toda segunda-feira às 6h
- [ ] Formato: A4, orientação retrato, design limpo/profissional

### AC2 — Variantes setoriais

- [ ] Gerar variantes para os 5 setores maiores: informática, saúde, engenharia, facilities, software
- [ ] **Header variante:** "Radar SmartLic — {Setor} — Semana {DD/MM}"
- [ ] Cada variante filtra licitações do setor específico
- [ ] Permite distribuição segmentada por grupo de WhatsApp setorial

### AC3 — Design e branding

- [ ] Cores SmartLic (gradiente do header)
- [ ] Fonte legível em tela de celular (tamanho mínimo 10pt)
- [ ] Tabela com zebra-striping para legibilidade
- [ ] **Sem clutter** — informação densa mas limpa
- [ ] Otimizado para visualização em tela de celular (a maioria abre direto no WhatsApp)

### AC4 — Distribuição

- [ ] **Fase 1 (manual):** Fundador distribui em 10 grupos de WhatsApp/Telegram identificados
  - Grupos de licitação (existem dezenas no Brasil)
  - Grupos de associações empresariais
  - Grupos de consultores de licitação
- [ ] **Fase 2 (semi-automática):** Lista de email opt-in no site ("Receba o Radar Semanal grátis")
  - Formulário de captura em `/blog` e landing page
  - Envio via Resend (email service já configurado)
- [ ] **Fase 3 (viral):** Cada PDF incentiva reenvio ("Compartilhe com seu grupo de licitações")

### AC5 — Tracking

- [ ] QR code com UTM único por edição: `utm_source=radar&utm_medium=whatsapp&utm_campaign=semana-{N}`
- [ ] Short link rastreável (smartlic.tech/radar → redirect com UTM)
- [ ] Métricas: downloads, cliques no QR, signups via UTM

### AC6 — Página de arquivo

- [ ] `/blog/radar/` — arquivo com todos os Radares publicados (download PDF)
- [ ] "Receba toda semana no seu email" → formulário de captura
- [ ] SEO: "Radar de Licitações — Oportunidades Semanais | SmartLic"

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Spam em grupos de WhatsApp | Valor real (top licitações reais, não propaganda); 1 envio/semana (não intrusivo) |
| Admin de grupo remover posts | Entrar em grupos de forma orgânica; se removido, focar em distribuição via email |
| PDF não gerar cliques | QR code grande e visível; CTA direto para trial; short link fácil de digitar |
| Dados do radar incorretos | Mesma pipeline de dados do SmartLic (já validada em produção) |
| Scaling manual insustentável | Fase 2 (email) automatiza; Fase 3 (viral) depende dos leitores |

## Definição de Pronto

- [ ] Geração automática de PDF funcionando
- [ ] 5 variantes setoriais disponíveis
- [ ] Design aprovado (legível em celular)
- [ ] Primeira edição distribuída em 10 grupos
- [ ] QR code e tracking funcionando
- [ ] Página `/blog/radar/` publicada
- [ ] Commit com tag `MKT-011`

## KPIs

| Métrica | 30 dias | 90 dias | 180 dias |
|---------|---------|---------|----------|
| Downloads/semana | 50 | 200 | 500 |
| Grupos de distribuição | 10 | 30 | 50 |
| Signups via Radar UTM/mês | 5 | 20 | 50 |
| Assinantes email (opt-in) | 50 | 200 | 500 |
