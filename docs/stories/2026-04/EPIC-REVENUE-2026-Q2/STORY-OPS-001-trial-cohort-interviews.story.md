# STORY-OPS-001: Trial Cohort Interviews — 5 Conversas 1:1 (30 min cada)

**Priority:** P1 — Descoberta qualitativa insubstituível quando métricas quantitativas não explicam
**Effort:** S (5 horas founder + 2h síntese)
**Squad:** Founder (execução) + @analyst (síntese opcional)
**Status:** Ready (condicional: ativar no gate D+30 se MRR = R$ 0)
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Sprint:** Disparar W4-W5 dependendo do gate D+30

---

## Contexto

EPIC-CONVERSION-2026-04 (10 stories) está Done. Score viabilidade visível, CTA contextual, tour guiado, nurturing emails, upgrade gates — tudo implementado.

Se após D+30 com **TIER 1** também em execução (cartão, outreach, founding) o MRR continuar R$ 0, há **hipótese desconhecida**. Métricas de funnel Mixpanel mostrarão onde usuários caem mas não **por que**. A única forma de descobrir é conversar.

5 entrevistas × 30 min + 2h síntese é **baratíssimo** para o valor de insights que entrega. Evita pivotar na direção errada.

**Quando disparar:**
- Gate D+30 PASS: adiar para gate D+45 (se ainda sem pagante)
- Gate D+30 FAIL (trials ≤2 OU CI verde 0 runs): disparar imediatamente — produto pode ter problema de fundo
- Default: disparar W5 (D+30 a D+35)

**Impacto esperado:** Top-3 insights viram backlog de stories na semana seguinte. Risco mitigado de investir em hipóteses erradas.

---

## Acceptance Criteria

### AC1: Seleção de 5 trials para entrevista
- [ ] Query Supabase identifica 5 trials encerrados nos últimos 30 dias com perfis diversos:
  - 2× "churn rápido" (dropout <3 dias pós-signup)
  - 2× "churn tardio" (usaram ativamente mas não converteram)
  - 1× "ainda ativo" (trial ativo, ≥3 buscas)
- [ ] Priorizar diversidade de CNAE/UF/porte
- [ ] Script `scripts/ops_interview_candidates.py` gera CSV com contatos

### AC2: Convite e agendamento
- [ ] Email template `docs/sales/templates/interview-invite.md`:
  - Assunto: "5 minutos para uma pergunta sobre SmartLic?"
  - Corpo: reconhecimento de usar/testar + pergunta franca sobre feedback + incentivo simbólico (R$ 50 Uber Eats credit ou equivalente)
  - Link Calendly/Cal.com para agendar 30 min
- [ ] Meta: ≥5 confirmados. Se taxa de aceite baixa (<40%), expandir base de 5 para 15 convites

### AC3: Guia de entrevista estruturado
- [ ] `docs/research/trial-interview-script-v1.md` com 12 perguntas-chave em 4 blocos:

  **Bloco 1 — Contexto (5 min)**
  - O que te levou a procurar uma ferramenta como SmartLic?
  - Qual era a alternativa que você já usava (se alguma)?
  - Quem da sua empresa toma a decisão de comprar esse tipo de ferramenta?

  **Bloco 2 — Experiência SmartLic (10 min)**
  - Descreva a primeira vez que abriu o SmartLic. O que você esperava?
  - Qual foi o momento que mais te impressionou? O que te frustrou?
  - Conseguiu completar uma busca que seria útil no dia a dia?

  **Bloco 3 — Decisão não-conversão (10 min)** (pular se ainda ativo)
  - O que faltou para você pagar os R$ 397?
  - Qual funcionalidade, se existisse, te faria decidir sim na hora?
  - Quanto você consideraria justo pagar se o produto fosse perfeito para você?

  **Bloco 4 — Futuro (5 min)**
  - Você recomendaria o SmartLic mesmo não pagando? Por quê?
  - Se eu te ligasse em 3 meses com uma melhoria específica, você testaria de novo?

- [ ] Cada pergunta tem 1-2 perguntas de follow-up documentadas para aprofundar

### AC4: Execução e gravação
- [ ] Consentimento explícito antes de gravar (LGPD)
- [ ] Gravação Zoom/Meet + transcrição automática (Otter.ai ou equivalente)
- [ ] Transcrições salvas em `docs/research/interviews/{YYYY-MM-DD}-{anon-id}.md` (anonimizadas — sem nome/empresa no arquivo)
- [ ] Tabela master `docs/research/interviews/index.md` mapeia anon-id → metadata (CNAE, data, duração, churn_type)

### AC5: Síntese estruturada
- [ ] Após todas entrevistas, escrever `docs/research/trial-interviews-synthesis-2026-W{XX}.md`
- [ ] Estrutura:
  1. **Pain points recorrentes** (≥3 mencionados por ≥2 entrevistados)
  2. **Objeções de preço** (quantificar quantos mencionaram, com citações)
  3. **Feature gaps** (funcionalidades mencionadas como "teria pagado se tivesse")
  4. **Concorrentes nomeados** (quem usa o quê?)
  5. **Insights surpresa** (o que você não esperava)
  6. **Top 3 decisões recomendadas** (stories de backlog: criar/matar/priorizar)

### AC6: Top-3 vira stories de backlog
- [ ] 3 stories novas criadas baseadas nos insights (podem ser no EPIC-REVENUE-Q2 ou novo epic)
- [ ] Cada story refere a entrevista específica que originou (evidência > opinião)
- [ ] Review com founder antes de marcar Ready

---

## Arquivos

**Scripts:**
- `scripts/ops_interview_candidates.py` (novo)

**Documentação (nova):**
- `docs/sales/templates/interview-invite.md`
- `docs/research/trial-interview-script-v1.md`
- `docs/research/interviews/index.md`
- `docs/research/interviews/.gitkeep`
- `docs/research/trial-interviews-synthesis-2026-W{XX}.md` (gerado ao fim)

---

## Riscos e Mitigações

**Risco 1:** Taxa de aceite baixa (<40%)
- **Mitigação:** Aumentar incentivo (R$ 100 em vez de R$ 50), expandir base 3x, oferecer horários flexíveis

**Risco 2:** Sample viesado (só ouvimos quem está disposto)
- **Mitigação:** Reconhecer na síntese, não generalizar 5 entrevistas como "a verdade"

**Risco 3:** Insights contradizem hipóteses do plano (cartão obrigatório vai fricção demais)
- **Mitigação:** Documentar e enfrentar — se dados dizem A e plano diz B, dados vencem. Revisar plano.

---

## Definition of Done

- [ ] AC1-AC6 todos marcados `[x]`
- [ ] 5 entrevistas realizadas + transcritas
- [ ] Síntese publicada em `docs/research/`
- [ ] 3 stories novas de backlog criadas com evidência
- [ ] Apresentação oral (ou escrita) de 1 página dos insights — pode ser slack post ou commit

---

## Dev Notes

**Por que 5 é o número mágico:** Nielsen Norman Group research — 5 entrevistas capturam ~85% dos problemas qualitativos. Mais que isso tem diminishing returns na fase de discovery.

**Ferramenta de síntese sugerida:** Dovetail ou Miro board. Custo irrelevante comparado ao tempo de founder. Alternativa zero-cost: Notion database com tags.

**Anonimização:** Usar `interview-001-cnae70`, `interview-002-cnae62` etc. Consentimento gravação permite internal review mas não publicação.

---

## File List

_(populado pelo founder durante execução)_

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Condicional ao gate D+30. |
