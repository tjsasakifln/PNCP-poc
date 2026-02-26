"""
STORY-266 AC1-AC4: Trial reminder email templates.

4 emails in the trial conversion chain:
- Day 3: Midpoint — celebrate usage, show value discovered
- Day 5: Expiring — 2 days remaining, moderate urgency
- Day 6: Last day — maximum urgency, tomorrow access expires
- Day 8: Expired — reengagement, data saved for 30 days
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def _format_brl(value: float) -> str:
    """Format a float as Brazilian Real currency string."""
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"R$ {value / 1_000:.0f}k"
    return f"R$ {value:,.0f}".replace(",", ".")


def _stats_block(stats: dict, show_pipeline: bool = False) -> str:
    """Render a stats summary block for email templates."""
    searches = stats.get("searches_count", 0)
    opps = stats.get("opportunities_found", 0)
    value = stats.get("total_value_estimated", 0.0)
    pipeline = stats.get("pipeline_items_count", 0)

    rows = f"""
    <tr>
      <td style="padding: 8px 16px; color: #555; font-size: 15px; border-bottom: 1px solid #eee;">
        Buscas realizadas
      </td>
      <td style="padding: 8px 16px; color: #333; font-size: 15px; font-weight: 600; text-align: right; border-bottom: 1px solid #eee;">
        {searches}
      </td>
    </tr>
    <tr>
      <td style="padding: 8px 16px; color: #555; font-size: 15px; border-bottom: 1px solid #eee;">
        Oportunidades encontradas
      </td>
      <td style="padding: 8px 16px; color: #333; font-size: 15px; font-weight: 600; text-align: right; border-bottom: 1px solid #eee;">
        {opps}
      </td>
    </tr>
    <tr>
      <td style="padding: 8px 16px; color: #555; font-size: 15px; border-bottom: 1px solid #eee;">
        Valor total estimado
      </td>
      <td style="padding: 8px 16px; color: {SMARTLIC_GREEN}; font-size: 15px; font-weight: 600; text-align: right; border-bottom: 1px solid #eee;">
        {_format_brl(value)}
      </td>
    </tr>"""

    if show_pipeline:
        rows += f"""
    <tr>
      <td style="padding: 8px 16px; color: #555; font-size: 15px;">
        Itens no pipeline
      </td>
      <td style="padding: 8px 16px; color: #333; font-size: 15px; font-weight: 600; text-align: right;">
        {pipeline}
      </td>
    </tr>"""

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background-color: #f8f9fa; border-radius: 8px; margin: 16px 0 24px; overflow: hidden;">
      {rows}
    </table>"""


def render_trial_midpoint_email(user_name: str, stats: dict) -> str:
    """AC1: Day 3 — midpoint email. Celebrate usage, show value.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats (searches_count, opportunities_found, etc.)
    """
    has_usage = stats.get("searches_count", 0) > 0

    if has_usage:
        headline = f"Você já analisou {_format_brl(stats.get('total_value_estimated', 0))} em oportunidades"
        intro = (
            f"Olá, {user_name}! Em apenas 3 dias no SmartLic, você já está "
            f"descobrindo oportunidades reais de licitação."
        )
    else:
        headline = "Você ainda tem 4 dias para descobrir oportunidades"
        intro = (
            f"Olá, {user_name}! Seu trial do SmartLic está na metade e "
            f"há oportunidades esperando por você. Faça sua primeira busca agora!"
        )

    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      {headline}
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      {intro}
    </p>
    {_stats_block(stats) if has_usage else ''}
    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/buscar" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Continuar descobrindo oportunidades
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Seu trial gratuito termina em 4 dias.
    </p>
    """

    return email_base(
        title="Meio do trial — SmartLic",
        body_html=body,
        is_transactional=True,
    )


def render_trial_expiring_email(user_name: str, days_remaining: int, stats: dict) -> str:
    """AC2: Day 5 — 2 days remaining. Informative with moderate urgency.

    Args:
        user_name: User's display name.
        days_remaining: Days left in trial (typically 2).
        stats: Dict with keys from TrialUsageStats.
    """
    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Seu acesso completo ao SmartLic acaba em {days_remaining} dias
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Seu período de trial está chegando ao fim.
      Veja o que você já conquistou:
    </p>
    {_stats_block(stats, show_pipeline=True)}
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Para continuar tendo acesso completo a buscas ilimitadas, análise por IA,
      relatórios Excel e pipeline de oportunidades, ative o SmartLic Pro.
    </p>
    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Garantir acesso contínuo
      </a>
    </p>
    """

    return email_base(
        title="Seu trial expira em breve — SmartLic",
        body_html=body,
        is_transactional=True,
    )


def render_trial_last_day_email(user_name: str, stats: dict) -> str:
    """AC3: Day 6 — last day. Maximum urgency.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
    """
    body = f"""
    <h1 style="color: #d32f2f; font-size: 22px; margin: 0 0 16px;">
      Amanhã seu acesso expira — não perca o que você construiu
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Este é o <strong>último dia</strong> do seu trial no SmartLic.
      Amanhã você perderá acesso às funcionalidades completas.
    </p>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 8px;">
      <strong>Resumo do seu trial:</strong>
    </p>
    {_stats_block(stats, show_pipeline=True)}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #fff3e0; border-radius: 8px; padding: 16px; border-left: 4px solid #ff9800;">
          <p style="color: #e65100; font-size: 14px; margin: 0; font-weight: 600;">
            Ative hoje e não perca nenhuma oportunidade
          </p>
          <p style="color: #555; font-size: 14px; margin: 8px 0 0;">
            SmartLic Pro — R$ 397/mês &nbsp;|&nbsp;
            Economia de 25% no plano anual
          </p>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: #d32f2f; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Ativar SmartLic Pro — R$ 397/mês
      </a>
    </p>
    """

    return email_base(
        title="Último dia de trial — SmartLic",
        body_html=body,
        is_transactional=True,
    )


def render_trial_expired_email(user_name: str, stats: dict) -> str:
    """AC4: Day 8 — 1 day after expiry. Reengagement.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
    """
    opps = stats.get("opportunities_found", 0)
    pipeline = stats.get("pipeline_items_count", 0)

    # Adapt headline based on usage
    if opps > 0 or pipeline > 0:
        if pipeline > 0:
            headline = f"Suas {pipeline} oportunidades estão esperando por você"
        else:
            headline = f"Suas {opps} oportunidades estão esperando por você"
    else:
        headline = "As oportunidades de licitação continuam surgindo"

    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      {headline}
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Seu trial expirou, mas seus dados ficam salvos por 30 dias.
      Reative o acesso para continuar de onde parou.
    </p>
    {_stats_block(stats, show_pipeline=True) if (opps > 0 or pipeline > 0) else ''}
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0;">
            Seus dados ficam salvos por 30 dias — buscas, pipeline e histórico.
          </p>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Reativar acesso
      </a>
    </p>
    """

    return email_base(
        title="Seu trial expirou — SmartLic",
        body_html=body,
        is_transactional=True,
    )
