"""Referral welcome email — sent when a user generates their referral code.

Shows the user their unique code, a copy-ready share link, and sales copy
explaining the 1-month-free reward.
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def render_referral_welcome_email(
    user_name: str,
    code: str,
    share_url: str,
) -> str:
    """Render the referral program welcome HTML email.

    Args:
        user_name: Display name for greeting.
        code: The user's unique 8-char referral code.
        share_url: Full shareable signup URL containing ?ref=CODE.
    """
    body = f"""
    <h1 style="color: #333; font-size: 24px; margin: 0 0 16px;">
      Indique o SmartLic e ganhe 1 mês grátis, {user_name}
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      A cada amigo que assinar o SmartLic usando seu código,
      <strong>você ganha 1 mês grátis</strong> automaticamente na sua próxima cobrança.
      Sem limite de indicações. Quanto mais amigos, mais meses grátis.
    </p>

    <div style="background-color: #F1F8E9; border: 2px dashed {SMARTLIC_GREEN};
                border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
      <p style="color: #555; font-size: 13px; text-transform: uppercase;
                letter-spacing: 1px; margin: 0 0 8px;">Seu código</p>
      <p style="color: {SMARTLIC_GREEN}; font-size: 36px; font-weight: 700;
                letter-spacing: 4px; margin: 0; font-family: monospace;">{code}</p>
    </div>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 12px;">
      Compartilhe este link direto — o código já vem preenchido:
    </p>
    <p style="background-color: #f5f5f5; border-radius: 8px; padding: 12px;
              font-family: monospace; font-size: 13px; word-break: break-all; margin: 0 0 24px;">
      <a href="{share_url}" style="color: {SMARTLIC_GREEN}; text-decoration: none;">{share_url}</a>
    </p>

    <p style="text-align: center; margin: 32px 0 16px;">
      <a href="{FRONTEND_URL}/indicar" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN};
                color: #ffffff; text-decoration: none; border-radius: 8px;
                font-weight: 600; font-size: 16px;">
        Acompanhar minhas indicações
      </a>
    </p>

    <h2 style="color: #333; font-size: 18px; margin: 32px 0 12px;">Como funciona</h2>
    <ol style="color: #555; font-size: 15px; line-height: 1.7; padding-left: 20px; margin: 0 0 24px;">
      <li>Compartilhe seu código ou link com quem conhece</li>
      <li>Seu amigo assina o SmartLic Pro</li>
      <li>Na sua próxima cobrança, 30 dias a mais de crédito entram automaticamente</li>
    </ol>

    <p style="color: #888; font-size: 13px; text-align: center; margin: 24px 0 0;">
      Dúvidas? Responda este email.
    </p>
    """
    return email_base(
        title="Indique o SmartLic e ganhe 1 mês grátis",
        body_html=body,
        is_transactional=True,
    )
