"""
Quota notification email templates — STORY-225 Track 3 (AC10-AC11)

AC10: Quota warning at 80% usage.
AC11: Quota exhaustion at 100%.
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def render_quota_warning_email(
    user_name: str,
    plan_name: str,
    quota_used: int,
    quota_limit: int,
    reset_date: str,
) -> str:
    """
    Render quota warning email (80% threshold).

    AC10: "Você usou 8 de 10 buscas este mês"

    Args:
        user_name: User's display name.
        plan_name: Current plan name.
        quota_used: Searches used this month.
        quota_limit: Max searches allowed.
        reset_date: Date when quota resets (DD/MM/YYYY).
    """
    quota_remaining = max(0, quota_limit - quota_used)
    pct = int((quota_used / quota_limit) * 100) if quota_limit > 0 else 100

    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Aviso de cota de buscas
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Você utilizou <strong>{pct}%</strong> da sua cota mensal de buscas.
    </p>

    <!-- Progress bar -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 16px 0;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 0;">
          <table role="presentation" width="{pct}%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="background-color: #ff9800; border-radius: 8px; height: 12px; min-width: 12px;">&nbsp;</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 8px;">
      <strong>{quota_used}</strong> de <strong>{quota_limit}</strong> buscas utilizadas
      &mdash; restam <strong>{quota_remaining}</strong> buscas.
    </p>
    <p style="color: #888; font-size: 14px; margin: 0 0 24px;">
      Plano atual: <strong>{plan_name}</strong> &middot; Renovação em {reset_date}
    </p>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/precos"
         class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Fazer upgrade
      </a>
    </p>
    """

    return email_base(
        title="Aviso de cota — SmartLic",
        body_html=body,
        is_transactional=True,
    )


def render_quota_exhausted_email(
    user_name: str,
    plan_name: str,
    quota_limit: int,
    reset_date: str,
) -> str:
    """
    Render quota exhausted email (100% threshold).

    AC11: "Limite atingido. Renova em DD/MM ou faça upgrade."

    Args:
        user_name: User's display name.
        plan_name: Current plan name.
        quota_limit: Max searches allowed.
        reset_date: Date when quota resets (DD/MM/YYYY).
    """
    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Limite de buscas atingido
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Você atingiu o limite de <strong>{quota_limit} buscas</strong>
      mensais do plano <strong>{plan_name}</strong>.
    </p>

    <!-- Progress bar (full) -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 16px 0;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 0;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="background-color: #d32f2f; border-radius: 8px; height: 12px;">&nbsp;</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Sua cota será renovada em <strong>{reset_date}</strong>, ou você pode
      fazer upgrade para um plano com mais buscas.
    </p>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/precos"
         class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Fazer upgrade agora
      </a>
    </p>
    """

    return email_base(
        title="Limite de buscas atingido — SmartLic",
        body_html=body,
        is_transactional=True,
    )
