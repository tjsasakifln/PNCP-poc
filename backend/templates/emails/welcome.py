"""
Welcome email template — STORY-225 Track 2 (AC6-AC9)

Sent after successful signup (both email and Google OAuth).
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def render_welcome_email(
    user_name: str,
    plan_name: str = "FREE Trial",
    login_url: str = "",
) -> str:
    """
    Render welcome email HTML.

    AC6: Value proposition recap, link to first search, support link.
    AC8: Includes user name, plan type, link to /buscar.
    AC9: Responsive HTML design (via base template).

    Args:
        user_name: User's display name.
        plan_name: Current plan name (e.g. "FREE Trial").
        login_url: URL to login/search page.
    """
    if not login_url:
        login_url = f"{FRONTEND_URL}/buscar"

    body = f"""
    <h1 style="color: #333; font-size: 24px; margin: 0 0 16px;">
      Bem-vindo ao SmartLic, {user_name}! 🎉
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Sua conta foi criada com sucesso no plano <strong>{plan_name}</strong>.
    </p>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      O SmartLic monitora dezenas de fontes oficiais automaticamente
      para identificar oportunidades de licitação relevantes ao seu setor.
      Avaliação objetiva por IA indica onde focar para ganhar mais.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding: 8px 0;">
          <table role="presentation" cellpadding="0" cellspacing="0" style="width: 100%;">
            <tr>
              <td style="width: 32px; vertical-align: top; padding-top: 2px;">
                <span style="color: {SMARTLIC_GREEN}; font-size: 18px;">&#10003;</span>
              </td>
              <td style="color: #555; font-size: 15px; line-height: 1.5;">
                <strong>Busca inteligente</strong> — Encontre licitações por estado, valor e palavras-chave
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding: 8px 0;">
          <table role="presentation" cellpadding="0" cellspacing="0" style="width: 100%;">
            <tr>
              <td style="width: 32px; vertical-align: top; padding-top: 2px;">
                <span style="color: {SMARTLIC_GREEN}; font-size: 18px;">&#10003;</span>
              </td>
              <td style="color: #555; font-size: 15px; line-height: 1.5;">
                <strong>Avaliação estratégica por IA</strong> — Cada oportunidade avaliada com critérios objetivos
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding: 8px 0;">
          <table role="presentation" cellpadding="0" cellspacing="0" style="width: 100%;">
            <tr>
              <td style="width: 32px; vertical-align: top; padding-top: 2px;">
                <span style="color: {SMARTLIC_GREEN}; font-size: 18px;">&#10003;</span>
              </td>
              <td style="color: #555; font-size: 15px; line-height: 1.5;">
                <strong>Relatórios em Excel</strong> — Exporte dados estruturados para análise
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 32px 0 16px;">
      <a href="{login_url}" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Fazer minha primeira busca
      </a>
    </p>

    <p style="color: #888; font-size: 13px; text-align: center; margin: 24px 0 0;">
      Dúvidas? Responda este email ou acesse
      <a href="{FRONTEND_URL}" style="color: {SMARTLIC_GREEN};">smartlic.tech</a>
    </p>
    """

    return email_base(
        title="Bem-vindo ao SmartLic!",
        body_html=body,
        is_transactional=True,
    )
