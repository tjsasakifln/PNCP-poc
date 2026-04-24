# GV-005: "Enviar ao Colega" — Contextual Share no Card de Resultado

**Priority:** P0
**Effort:** S (5 SP, 2-3 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 1

---

## Contexto

Hoje user que encontra licitação promissora tem 2 opções para compartilhar:
1. Copy-paste URL (alto atrito)
2. Share system atual `/api/share` (gera `/analise/[hash]` genérico — sem contexto do destinatário)

**Gap:** não há flow contextual "enviar ao colega/sócio/consultor" com mensagem pré-preenchida. Esse é o ponto de maior intenção (user acabou de ver valor + quer validar com terceiro) e maior conversão para viral signup.

ChatGPT cresceu 100M MAU em 2 meses via share + screenshot organic loop. SmartLic precisa do equivalente B2G: "manda pro meu advogado" flow.

---

## Acceptance Criteria

### AC1: Botão no card de resultado

- [ ] `frontend/app/buscar/components/SearchResults.tsx`:
  - Novo botão "Enviar ao colega" ao lado de "Adicionar ao pipeline" / "Exportar"
  - Ícone + label, hover state
  - Visível para todos users (trial + Pro+)
  - Mobile: menu overflow (3-dot)

### AC2: Modal `ShareToColleagueModal`

- [ ] `frontend/app/buscar/components/ShareToColleagueModal.tsx`:
  - Form:
    - Email destinatário (required, validação regex)
    - Relação (optional, radio): "Sócio", "Consultor", "Advogado", "Cliente", "Outro"
    - Mensagem pessoal (optional, textarea pre-populated baseado em relação):
      - Sócio: "Achei essa licitação que combina com nossa empresa — dá uma olhada"
      - Consultor: "Pode avaliar essa licitação para nós?"
      - Advogado: "Precisamos da sua análise jurídica nesta licitação"
      - Cliente: "Encontrei essa oportunidade para você"
    - Toggle "Incluir minha mensagem pessoal na assinatura"
  - Preview do email antes de enviar
  - Botões: Cancelar / Enviar

### AC3: Endpoint backend `/v1/share/to-colleague`

- [ ] `backend/routes/share.py` estende com POST `/v1/share/to-colleague`:
  - Input: `licitacao_id`, `recipient_email`, `relationship`, `message`
  - Valida email + rate limit 10/dia por user
  - Cria registro em tabela `colleague_shares`:
    ```sql
    CREATE TABLE colleague_shares (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      sender_id UUID REFERENCES auth.users(id),
      recipient_email TEXT NOT NULL,
      licitacao_id TEXT NOT NULL,
      share_hash TEXT UNIQUE NOT NULL,  -- reutiliza infra /analise/[hash]
      relationship TEXT,
      opened_at TIMESTAMPTZ,
      signup_user_id UUID REFERENCES auth.users(id),  -- preenchido se destinatário cadastrou
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    ALTER TABLE colleague_shares ENABLE ROW LEVEL SECURITY;
    ```
  - Envia email via Resend com:
    - Subject: "{remetente} pediu sua opinião sobre uma licitação"
    - CTA principal: "Ver análise completa" → `/analise/{hash}?source=colleague_share`
    - CTA secundário: "Analisar minhas licitações grátis" → `/signup?ref={sender_hash}`
    - Mensagem pessoal (se preenchida)

### AC4: Email template

- [ ] `backend/templates/emails/share_colleague.html`:
  - Header branded SmartLic
  - Saudação personalizada
  - Card da licitação: título, valor (pseudonimizado), UF, modalidade, prazo
  - Mensagem pessoal (se houver)
  - 2 CTAs (ver análise + criar conta grátis)
  - Footer "você recebeu este email porque {email_remetente} te convidou"
- [ ] Multi-channel: versão texto puro fallback
- [ ] Preview em `/admin/email-preview/share_colleague` (dev only)

### AC5: Tracking + attribution

- [ ] Eventos Mixpanel:
  - `share_colleague_initiated` (modal opened)
  - `share_colleague_sent` (email sent)
  - `share_colleague_opened` (recipient click — via Resend webhook)
  - `share_colleague_signup` (recipient cadastrou)
- [ ] Signup via `source=colleague_share`:
  - Atribuição automatica `attribution_source = colleague_share`
  - Inviter recebe email "{destinatário} criou conta!" (+ possível reward via GV-018 tiered)
- [ ] Rate limit enforcement: 10 shares/dia por user (reset 24h UTC)

### AC6: Notificação ao remetente

- [ ] Se destinatário opens email → inviter recebe push/email "Seu convite foi lido"
- [ ] Se destinatário cadastra → inviter recebe "Você convidou {nome} com sucesso!" + reward status (se GV-018 live)

### AC7: Testes

- [ ] Unit `backend/tests/test_share_colleague.py`
- [ ] Unit `frontend/__tests__/components/ShareToColleagueModal.test.tsx`
- [ ] E2E Playwright: user A faz busca → abre modal → preenche → envia → user B (email different) abre link → signup → user A vê notificação

---

## Scope

**IN:**
- Botão no card + modal
- Endpoint + tabela + email template
- Tracking + attribution
- Notificação remetente

**OUT:**
- Share múltiplos colegas no mesmo flow (batch) — v2
- Integração WhatsApp/LinkedIn share buttons direto (email-first)
- Contacts sync do Google/Outlook — v2
- Custom email domain (enviar de @empresa.com) — v3

---

## Dependências

- **GV-002** (watermark + pseudonimização) — share email usa mask
- **GV-018** (referral tiered) — se Done, reward fires on signup; se não, só tracking

---

## Riscos

- **Spam via abuse (user envia pra emails aleatórios):** rate limit 10/dia + detection padrões suspeitos (mesmo user envia pra mesmo email 3x = block). Resend spam protection.
- **Email deliverability:** SPF/DKIM já configurado; monitorar bounce rate. Se >5% → pausar e investigar.
- **LGPD — envio email não-consentido:** copy do email deixa claro "{remetente} te convidou"; destinatário tem unsubscribe 1-click; não adicionar a lista marketing sem consent expresso.

---

## Arquivos Impactados

### Novos
- `frontend/app/buscar/components/ShareToColleagueModal.tsx`
- `backend/templates/emails/share_colleague.html`
- `backend/templates/emails/share_colleague.txt`
- `supabase/migrations/YYYYMMDDHHMMSS_colleague_shares.sql` (+ `.down.sql`)
- `backend/tests/test_share_colleague.py`
- `frontend/__tests__/components/ShareToColleagueModal.test.tsx`

### Modificados
- `frontend/app/buscar/components/SearchResults.tsx` (adiciona botão)
- `backend/routes/share.py` (novo endpoint + integração rate limit)
- `backend/webhooks/resend.py` (novo ou extender — captura email_opened)

---

## Testing Strategy

1. **Unit + E2E** AC7
2. **Email deliverability** test com 10 destinatários Gmail/Outlook/proprietário
3. **Spam detection** manual: enviar pra 15 emails diferentes em 1h → 11º deveria bloquear
4. **LGPD compliance audit** copy email + unsubscribe

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — ChatGPT-style contextual share adaptado B2G; flow "envia pro advogado" |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
