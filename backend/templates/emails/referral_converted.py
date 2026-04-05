"""Referral converted email — sent to the referrer when a referred user converts.

Celebrates the credit and invites them to share more.
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def render_referral_converted_email(
    user_name: str,
    credits_total: int = 1,
) -> str:
    """Render the referral conversion celebration HTML email.

    Args:
        user_name: Display name for greeting.
        credits_total: How many free months this user has accumulated so far.
    """
    body = f"""
    <h1 style="color: #333; font-size: 24px; margin: 0 0 16px;">
      🎉 Parabéns, {user_name}! Você ganhou 1 mês grátis
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Uma pessoa indicada por você acabou de assinar o SmartLic Pro.
      Como prometido, <strong>1 mês grátis foi creditado</strong> na sua próxima cobrança —
      automaticamente, sem ação sua.
    </p>

    <div style="background-color: #F1F8E9; border-radius: 12px; padding: 24px;
                text-align: center; margin: 24px 0;">
      <p style="color: #555; font-size: 13px; text-transform: uppercase;
                letter-spacing: 1px; margin: 0 0 8px;">Créditos acumulados</p>
      <p style="color: {SMARTLIC_GREEN}; font-size: 36px; font-weight: 700; margin: 0;">
        {credits_total} {'mês' if credits_total == 1 else 'meses'} grátis
      </p>
    </div>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Quer continuar ganhando? Cada nova indicação que converter
      vira outro mês de SmartLic sem custo para você.
    </p>

    <p style="text-align: center; margin: 32px 0 16px;">
      <a href="{FRONTEND_URL}/indicar" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN};
                color: #ffffff; text-decoration: none; border-radius: 8px;
                font-weight: 600; font-size: 16px;">
        Indicar mais pessoas
      </a>
    </p>

    <p style="color: #888; font-size: 13px; text-align: center; margin: 24px 0 0;">
      Obrigado por espalhar a palavra!
    </p>
    """
    return email_base(
        title="Parabéns! Você ganhou 1 mês grátis no SmartLic",
        body_html=body,
        is_transactional=True,
    )
