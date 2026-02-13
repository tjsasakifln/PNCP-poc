# STORY-213: LGPD Compliance Sprint — Cookie Consent, Data Deletion, Privacy Policy

**Status:** Pending
**Priority:** P0 — Blocks GTM Launch (Legal)
**Sprint:** Sprint 2 (Weeks 2-3)
**Estimated Effort:** 5-7 days
**Source:** AUDIT-FRENTE-6-BUSINESS (GAP-01, GAP-05, GAP-09, GAP-14), AUDIT-FRENTE-2-SECURITY (SEC-08), AUDIT-CONSOLIDATED (LGPD)
**Squad:** team-bidiq-feature (dev, qa, po, architect)

---

## Context

LGPD (Lei Geral de Proteção de Dados) compliance is **legally required** for a product targeting Brazilian businesses. The audits identified 8 of 13 compliance items as FAIL. Fines can reach 2% of revenue (capped at R$50M per infraction).

**Critical violations:**
1. Mixpanel initializes on every page load **before any consent** (LGPD Art. 7 violation)
2. No self-service account deletion mechanism (LGPD Art. 18 VI)
3. Privacy policy mentions "Google Analytics" but system uses Mixpanel
4. No data portability feature (LGPD Art. 18 V)
5. No DPO contact email published

## Acceptance Criteria

### Track 1: Cookie Consent Banner (3 days)

- [ ] AC1: Create `CookieConsentBanner` component that appears on first visit
- [ ] AC2: Banner explains: essential cookies (always), analytics cookies (opt-in)
- [ ] AC3: User can "Accept All" or "Reject Non-Essential"
- [ ] AC4: **Mixpanel ONLY initializes after analytics consent** — modify `AnalyticsProvider.tsx` to check consent before `mixpanel.init()`
- [ ] AC5: Consent preference persisted in `localStorage` key `bidiq_cookie_consent`
- [ ] AC6: Consent can be changed later via link in footer ("Gerenciar Cookies")
- [ ] AC7: Banner links to `/privacidade` for full details
- [ ] AC8: `identifyUser()` only called after consent is granted (respects opt-out)

### Track 2: Account Deletion (2 days)

- [ ] AC9: "Excluir Minha Conta" button in account settings page (`/conta`)
- [ ] AC10: Confirmation dialog with clear explanation: "Todos os seus dados serão excluídos permanentemente: perfil, histórico de buscas, assinaturas, mensagens."
- [ ] AC11: Backend endpoint `DELETE /api/me` that:
  - Deletes from `search_sessions` where `user_id`
  - Deletes from `monthly_quota` where `user_id`
  - Deletes from `user_subscriptions` where `user_id`
  - Deletes from `user_oauth_tokens` where `user_id`
  - Deletes from `messages` where `user_id`
  - Deletes from `profiles` where `id`
  - Calls Supabase `auth.admin.deleteUser(user_id)` to remove auth record
- [ ] AC12: Cancels active Stripe subscription before deletion (if any)
- [ ] AC13: Audit log entry (anonymized): `"account_deleted", timestamp, hashed_user_id`
- [ ] AC14: Shows confirmation page after deletion with logout redirect

### Track 3: Privacy Policy Fixes (0.5 day)

- [ ] AC15: Section 7: Replace "Google Analytics (anonimizado)" with "Mixpanel"
- [ ] AC16: Section 4: Add Mixpanel as data processor with description
- [ ] AC17: Section 2.2: Update "Dados de Uso" to accurately describe Mixpanel collection
- [ ] AC18: Add specific DPO contact email (e.g., `dpo@smartlic.tech` or `privacidade@smartlic.tech`)
- [ ] AC19: Remove mention of email notifications if not yet implemented (or add "em breve")
- [ ] AC20: Update timestamp at bottom of privacy policy page

### Track 4: Data Portability (1 day)

- [ ] AC21: Backend endpoint `GET /api/me/export` returns JSON file with all user data:
  - Profile information
  - Search history (sessions)
  - Subscription history
  - Messages
- [ ] AC22: "Exportar Meus Dados" button in account settings page
- [ ] AC23: Download as JSON file with filename `smartlic_dados_{user_id_prefix}_{date}.json`

### Testing

- [ ] AC24: Test cookie consent banner appears on fresh visit (no localStorage)
- [ ] AC25: Test Mixpanel does NOT fire before consent
- [ ] AC26: Test account deletion cascades correctly (all tables cleaned)
- [ ] AC27: Test data export includes all expected tables
- [ ] AC28: Test deletion of user with active Stripe subscription cancels it first

## Validation Metric

- 100% of analytics events fire only after consent
- User can delete account in < 3 clicks
- Privacy policy matches actual data processing tools
- Data export returns complete user data as JSON

## Risk Mitigated

- P0: LGPD violation (fines up to R$50M)
- P0: No right to deletion
- P1: Privacy policy inaccuracy undermines legal defense

## File References

| File | Change |
|------|--------|
| `frontend/app/components/CookieConsentBanner.tsx` | NEW |
| `frontend/app/components/AnalyticsProvider.tsx` | Conditional Mixpanel init |
| `frontend/app/layout.tsx` | Add CookieConsentBanner |
| `frontend/app/conta/page.tsx` | Add delete account + export buttons |
| `backend/routes/user.py` | Add DELETE /api/me + GET /api/me/export |
| `frontend/app/privacidade/page.tsx` | Fix inaccuracies |
| `frontend/app/components/Footer.tsx` | Add "Gerenciar Cookies" link |
