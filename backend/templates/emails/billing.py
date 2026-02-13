"""
Billing email templates — STORY-225 Track 3 (AC12-AC14)

AC12: Payment confirmation.
AC13: Subscription expiration warning (7 days and 1 day before).
AC14: Cancellation confirmation.
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def render_payment_confirmation_email(
    user_name: str,
    plan_name: str,
    amount: str,
    next_renewal_date: str,
    billing_period: str = "mensal",
) -> str:
    """
    Render payment confirmation email.

    AC12: Plan name, amount, next renewal date.

    Args:
        user_name: User's display name.
        plan_name: Plan name (e.g. "Consultor Ágil").
        amount: Formatted amount (e.g. "R$ 297,00").
        next_renewal_date: Next renewal date (DD/MM/YYYY).
        billing_period: "mensal" or "anual".
    """
    body = f"""
    <h1 style="color: {SMARTLIC_GREEN}; font-size: 22px; margin: 0 0 16px;">
      Pagamento confirmado!
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Olá, {user_name}! Seu pagamento foi processado com sucesso.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background-color: #f8faf8; border-radius: 8px; border: 1px solid #e8f5e9; margin: 0 0 24px;">
      <tr>
        <td style="padding: 20px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="color: #888; font-size: 13px; padding: 6px 0;">Plano</td>
              <td align="right" style="color: #333; font-size: 15px; font-weight: 600; padding: 6px 0;">{plan_name}</td>
            </tr>
            <tr>
              <td style="color: #888; font-size: 13px; padding: 6px 0;">Valor</td>
              <td align="right" style="color: #333; font-size: 15px; font-weight: 600; padding: 6px 0;">{amount}</td>
            </tr>
            <tr>
              <td style="color: #888; font-size: 13px; padding: 6px 0;">Periodicidade</td>
              <td align="right" style="color: #333; font-size: 15px; padding: 6px 0;">{billing_period.capitalize()}</td>
            </tr>
            <tr>
              <td style="color: #888; font-size: 13px; padding: 6px 0;">Próxima renovação</td>
              <td align="right" style="color: #333; font-size: 15px; padding: 6px 0;">{next_renewal_date}</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 16px 0;">
      <a href="{FRONTEND_URL}/buscar"
         class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Começar a buscar
      </a>
    </p>
    """

    return email_base(
        title="Pagamento confirmado — SmartLic",
        body_html=body,
        is_transactional=True,  # AC17: Payment emails exempt from unsubscribe
    )


def render_subscription_expiring_email(
    user_name: str,
    plan_name: str,
    expiry_date: str,
    days_remaining: int,
) -> str:
    """
    Render subscription expiration warning email.

    AC13: Sent 7 days and 1 day before expiration.

    Args:
        user_name: User's display name.
        plan_name: Current plan name.
        expiry_date: Expiration date (DD/MM/YYYY).
        days_remaining: Days until expiration (7 or 1).
    """
    urgency_color = "#d32f2f" if days_remaining <= 1 else "#ff9800"
    days_text = "1 dia" if days_remaining <= 1 else f"{days_remaining} dias"

    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Sua assinatura expira em {days_text}
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Sua assinatura do plano <strong>{plan_name}</strong>
      expira em <strong style="color: {urgency_color};">{expiry_date}</strong>.
    </p>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Renove agora para manter acesso a todas as funcionalidades sem interrupção.
    </p>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/precos"
         class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Renovar assinatura
      </a>
    </p>
    """

    return email_base(
        title=f"Assinatura expira em {days_text} — SmartLic",
        body_html=body,
        is_transactional=True,
    )


def render_cancellation_email(
    user_name: str,
    plan_name: str,
    end_date: str,
) -> str:
    """
    Render cancellation confirmation email.

    AC14: Plan name, end date, reactivation link.

    Args:
        user_name: User's display name.
        plan_name: Cancelled plan name.
        end_date: Date when access ends (DD/MM/YYYY).
    """
    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Cancelamento confirmado
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Confirmamos o cancelamento da sua assinatura
      do plano <strong>{plan_name}</strong>.
    </p>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Você continua com acesso até <strong>{end_date}</strong>.
      Após essa data, sua conta será revertida para o plano gratuito.
    </p>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 8px;">
      Sentiremos sua falta! Se mudar de ideia, pode reativar a qualquer momento:
    </p>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/precos"
         class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Reativar assinatura
      </a>
    </p>
    """

    return email_base(
        title="Cancelamento confirmado — SmartLic",
        body_html=body,
        is_transactional=True,  # AC17: Cancellation emails are transactional
    )
