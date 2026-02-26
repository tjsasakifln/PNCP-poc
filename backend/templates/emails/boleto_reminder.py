"""
Boleto reminder and expiration email templates — STORY-280 AC5

AC5: Boleto reminder (day 2 after generation).
AC2: Boleto expired notification (async_payment_failed).
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def render_boleto_reminder_email(
    user_name: str,
    plan_name: str,
    boleto_due_date: str,
) -> str:
    """
    Render boleto payment reminder email.

    STORY-280 AC5: Sent day 2 after boleto generation (vence amanha).

    Args:
        user_name: User's display name.
        plan_name: Plan name (e.g. "SmartLic Pro").
        boleto_due_date: Boleto due date (DD/MM/YYYY).
    """
    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Seu boleto vence amanha
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Ola, {user_name}! Seu boleto para ativacao do plano <strong>{plan_name}</strong>
      vence em <strong style="color: #ff9800;">{boleto_due_date}</strong>.
    </p>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Efetue o pagamento para garantir a ativacao do seu plano sem interrupcoes.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background-color: #fff8e1; border-radius: 8px; border: 1px solid #ffe082; margin: 0 0 24px;">
      <tr>
        <td style="padding: 20px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="color: #888; font-size: 13px; padding: 6px 0;">Plano</td>
              <td align="right" style="color: #333; font-size: 15px; font-weight: 600; padding: 6px 0;">{plan_name}</td>
            </tr>
            <tr>
              <td style="color: #888; font-size: 13px; padding: 6px 0;">Vencimento</td>
              <td align="right" style="color: #ff9800; font-size: 15px; font-weight: 600; padding: 6px 0;">{boleto_due_date}</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <p style="color: #555; font-size: 14px; line-height: 1.6; margin: 0 0 24px;">
      Se voce ja efetuou o pagamento, por favor desconsidere este lembrete.
      O processamento do boleto pode levar ate 1 dia util.
    </p>

    <p style="text-align: center; margin: 16px 0;">
      <a href="{FRONTEND_URL}/planos"
         class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Ver meu plano
      </a>
    </p>
    """

    return email_base(
        title="Lembrete: Boleto vence amanha — SmartLic",
        body_html=body,
        is_transactional=True,
    )


def render_boleto_expired_email(
    user_name: str,
    plan_name: str,
) -> str:
    """
    Render boleto expired notification email.

    STORY-280 AC2: Sent when async_payment_failed webhook fires.

    Args:
        user_name: User's display name.
        plan_name: Plan name (e.g. "SmartLic Pro").
    """
    body = f"""
    <h1 style="color: #d32f2f; font-size: 22px; margin: 0 0 16px;">
      Seu boleto expirou
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Ola, {user_name}! O boleto para ativacao do plano <strong>{plan_name}</strong>
      expirou sem pagamento.
    </p>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Nao se preocupe — voce pode gerar um novo boleto a qualquer momento
      na pagina de planos.
    </p>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos"
         class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Gerar novo boleto
      </a>
    </p>

    <p style="color: #888; font-size: 14px; line-height: 1.6; margin: 24px 0 0;">
      Se preferir, voce tambem pode pagar com cartao de credito para ativacao imediata.
    </p>
    """

    return email_base(
        title="Boleto expirado — SmartLic",
        body_html=body,
        is_transactional=True,
    )
