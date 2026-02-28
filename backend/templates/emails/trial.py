"""
STORY-321 AC7-AC9: Trial email templates — 6 emails over 14-day trial.

Compressed sequence (replaces STORY-310 8-email sequence):
- Day 0:  Welcome — onboarding CTA ("Fazer primeira busca")
- Day 3:  Engagement — stats de uso, destaques ("Explorar mais setores")
- Day 7:  Paywall alert — paywall ativa amanha ("Assine antes do limite")
- Day 10: Valor acumulado — social proof R$X ("Nao perca esse progresso")
- Day 13: Ultimo dia — escassez ("Assinar agora")
- Day 16: Expirado — reengajamento com cupom 20% off ("Voltar com 20% off")
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
    """AC8: Render a stats summary block for email templates."""
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


def _unsubscribe_block(unsubscribe_url: str) -> str:
    """Render unsubscribe link block (AC2: RFC 8058 one-click)."""
    if not unsubscribe_url:
        return ""
    return f"""
    <p style="color: #999; font-size: 12px; text-align: center; margin: 24px 0 0;">
      <a href="{unsubscribe_url}" style="color: #999; text-decoration: underline;">
        Nao desejo receber emails sobre o trial
      </a>
    </p>"""


def _preheader(text: str) -> str:
    """AC2: Hidden preheader text for email clients (Gmail, Apple Mail)."""
    return (
        f'<div style="display:none;font-size:1px;color:#f4f4f4;'
        f'line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">'
        f'{text}</div>'
    )


# ============================================================================
# Email #1 — Day 0: Boas-vindas (AC7)
# ============================================================================

def render_trial_welcome_email(user_name: str, unsubscribe_url: str = "") -> str:
    """STORY-321 AC7: Day 0 — Welcome email with 3 steps.

    Args:
        user_name: User's display name.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    body = f"""
    {_preheader("Seu trial de 14 dias comecou. Faca sua primeira busca agora.")}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Bem-vindo ao SmartLic, {user_name}!
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Seu trial de 14 dias comecou. Agora voce tem acesso completo a
      plataforma de inteligencia em licitacoes mais avancada do Brasil.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0 0 12px; font-weight: 600;">
            3 passos para comecar:
          </p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding: 6px 0; color: #555; font-size: 14px;">
                <strong style="color: {SMARTLIC_GREEN}; font-size: 18px; margin-right: 8px;">1.</strong>
                Escolha seu setor e UFs de interesse
              </td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #555; font-size: 14px;">
                <strong style="color: {SMARTLIC_GREEN}; font-size: 18px; margin-right: 8px;">2.</strong>
                Faca sua primeira busca com IA
              </td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #555; font-size: 14px;">
                <strong style="color: {SMARTLIC_GREEN}; font-size: 18px; margin-right: 8px;">3.</strong>
                Arraste oportunidades para o pipeline
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/buscar" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Fazer primeira busca
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Seu trial gratuito de 14 dias comecou hoje.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Bem-vindo ao SmartLic!",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #2 — Day 3: Engajamento (AC7)
# ============================================================================

def render_trial_engagement_email(user_name: str, stats: dict, unsubscribe_url: str = "") -> str:
    """STORY-321 AC7: Day 3 — Engagement email with real stats.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    has_usage = stats.get("searches_count", 0) > 0
    value = stats.get("total_value_estimated", 0.0)
    opps = stats.get("opportunities_found", 0)

    if has_usage and value > 0:
        preheader_text = f"Voce ja analisou {_format_brl(value)} em oportunidades"
        headline = f"Voce ja analisou {_format_brl(value)} em oportunidades"
        intro = (
            f"Ola, {user_name}! Em apenas 3 dias no SmartLic, voce ja esta "
            f"descobrindo oportunidades reais de licitacao."
        )
    elif has_usage and opps > 0:
        preheader_text = f"{opps} oportunidades encontradas em 3 dias"
        headline = f"{opps} oportunidades encontradas em 3 dias"
        intro = (
            f"Ola, {user_name}! Voce ja encontrou {opps} oportunidades. "
            f"Explore mais setores para ampliar seus resultados."
        )
    else:
        preheader_text = "Voce ainda tem 11 dias para descobrir oportunidades"
        headline = "Voce ainda tem 11 dias para descobrir oportunidades"
        intro = (
            f"Ola, {user_name}! Seu trial do SmartLic esta apenas comecando e "
            f"ha oportunidades esperando por voce. Faca sua primeira busca agora!"
        )

    body = f"""
    {_preheader(preheader_text)}
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
        Explorar mais setores
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Seu trial gratuito termina em 11 dias.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Suas primeiras descobertas — SmartLic",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #3 — Day 7: Paywall Alert (AC7 — NEW)
# ============================================================================

def render_trial_paywall_alert_email(user_name: str, stats: dict, unsubscribe_url: str = "") -> str:
    """STORY-321 AC7: Day 7 — Paywall alert. Preview limited starting tomorrow.

    References STORY-320 soft paywall that activates on day 7.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    has_usage = stats.get("searches_count", 0) > 0
    value = stats.get("total_value_estimated", 0.0)

    if has_usage and value > 0:
        value_line = f"Voce ja descobriu <strong>{_format_brl(value)}</strong> em oportunidades. "
    else:
        value_line = ""

    body = f"""
    {_preheader("A partir de amanha, resultados ficam limitados. Assine antes.")}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Metade do trial — a partir de amanha, preview limitado
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Ola, {user_name}! Voce esta na metade do seu trial de 14 dias.
      {value_line}A partir de amanha, os resultados de busca serao
      exibidos em modo preview (limitado a 10 resultados).
    </p>
    {_stats_block(stats, show_pipeline=True) if has_usage else ''}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #fff3e0; border-radius: 8px; padding: 16px; border-left: 4px solid #ff9800;">
          <p style="color: #e65100; font-size: 14px; margin: 0; font-weight: 600;">
            O que muda a partir de amanha:
          </p>
          <ul style="color: #555; font-size: 14px; margin: 8px 0 0; padding-left: 20px;">
            <li>Resultados limitados a 10 por busca (preview)</li>
            <li>Pipeline limitado a 5 itens</li>
            <li>Buscas e IA continuam funcionando normalmente</li>
          </ul>
        </td>
      </tr>
    </table>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Assine o SmartLic Pro <strong>antes do limite</strong> e mantenha acesso
      completo a todos os resultados, pipeline ilimitado e relatorios Excel.
    </p>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Assine antes do limite
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Seu trial gratuito termina em 7 dias.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Metade do trial — preview limitado amanha",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #4 — Day 10: Valor Acumulado (AC7 — NEW)
# ============================================================================

def render_trial_value_email(user_name: str, stats: dict, unsubscribe_url: str = "") -> str:
    """STORY-321 AC7: Day 10 — Accumulated value. Social proof with big R$ number.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    value = stats.get("total_value_estimated", 0.0)
    opps = stats.get("opportunities_found", 0)
    pipeline = stats.get("pipeline_items_count", 0)

    if value > 0:
        big_value = _format_brl(value)
        preheader_text = f"Voce ja analisou {big_value} em oportunidades. Nao perca."
        headline = f"Voce ja analisou {big_value}"
    elif opps > 0:
        preheader_text = f"{opps} oportunidades encontradas. Nao perca esse progresso."
        headline = f"{opps} oportunidades encontradas"
    else:
        preheader_text = "Restam 4 dias. Descubra oportunidades antes que seu trial expire."
        headline = "Restam 4 dias no seu trial"

    # Big value highlight block
    value_highlight = ""
    if value > 0:
        value_highlight = f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="margin: 16px 0 24px;">
      <tr>
        <td align="center"
            style="background-color: #e8f5e9; border-radius: 12px; padding: 24px;">
          <p style="color: #888; font-size: 13px; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 1px;">
            Valor total analisado
          </p>
          <p style="color: {SMARTLIC_GREEN}; font-size: 36px; font-weight: 700; margin: 0; line-height: 1.2;">
            {_format_brl(value)}
          </p>
          <p style="color: #666; font-size: 14px; margin: 8px 0 0;">
            em {opps} oportunidades{f" | {pipeline} no pipeline" if pipeline > 0 else ""}
          </p>
        </td>
      </tr>
    </table>"""

    body = f"""
    {_preheader(preheader_text)}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      {headline}
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Ola, {user_name}! Seu trial termina em 4 dias. Veja o progresso que voce
      construiu ate agora:
    </p>
    {value_highlight}
    {_stats_block(stats, show_pipeline=True) if value == 0 and opps > 0 else ''}
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Nao perca esse progresso. Com o SmartLic Pro, voce mantem acesso a tudo:
      buscas ilimitadas, IA de classificacao, pipeline e relatorios Excel.
    </p>
    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Nao perca esse progresso
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Economize 20% com o plano anual.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Voce ja analisou oportunidades — SmartLic",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #5 — Day 13: Ultimo Dia (AC7)
# ============================================================================

def render_trial_last_day_email(user_name: str, stats: dict, unsubscribe_url: str = "") -> str:
    """STORY-321 AC7: Day 13 — Last day. Maximum urgency with countdown.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    value = stats.get("total_value_estimated", 0.0)
    opps = stats.get("opportunities_found", 0)

    if value > 0:
        preheader_text = f"Amanha voce perde acesso a {_format_brl(value)} em oportunidades."
    else:
        preheader_text = "Amanha seu acesso expira. Assine agora."

    body = f"""
    {_preheader(preheader_text)}
    <h1 style="color: #d32f2f; font-size: 22px; margin: 0 0 16px;">
      Amanha seu acesso expira — nao perca o que voce construiu
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Ola, {user_name}! Este e o <strong>ultimo dia</strong> do seu trial no SmartLic.
      Amanha voce perdera acesso as funcionalidades completas.
    </p>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 8px;">
      <strong>Resumo do seu trial:</strong>
    </p>
    {_stats_block(stats, show_pipeline=True)}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #fff3e0; border-radius: 8px; padding: 16px; border-left: 4px solid #ff9800;">
          <p style="color: #e65100; font-size: 14px; margin: 0; font-weight: 600;">
            Ative hoje e nao perca nenhuma oportunidade
          </p>
          <p style="color: #555; font-size: 14px; margin: 8px 0 0;">
            SmartLic Pro — R$ 397/mes &nbsp;|&nbsp;
            Economia de 20% no plano anual
          </p>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: #d32f2f; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Assinar agora — R$ 397/mes
      </a>
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Ultimo dia de trial — SmartLic",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #6 — Day 16: Expirado (AC7 + AC14: coupon 20% off)
# ============================================================================

def render_trial_expired_email(
    user_name: str,
    stats: dict,
    unsubscribe_url: str = "",
    coupon_checkout_url: str = "",
) -> str:
    """STORY-321 AC7 + AC14: Day 16 — Expired. Reengagement with 20% off coupon.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
        coupon_checkout_url: Checkout URL with TRIAL_COMEBACK_20 coupon applied.
    """
    opps = stats.get("opportunities_found", 0)
    pipeline = stats.get("pipeline_items_count", 0)

    if opps > 0 or pipeline > 0:
        if pipeline > 0:
            headline = f"Suas {pipeline} oportunidades estao esperando por voce"
        else:
            headline = f"Suas {opps} oportunidades estao esperando por voce"
        preheader_text = f"Sentimos sua falta. Volte com 20% off."
    else:
        headline = "Sentimos sua falta"
        preheader_text = "As oportunidades continuam surgindo. Volte com 20% off."

    # Determine CTA URL — use coupon checkout if available, else /planos
    cta_url = coupon_checkout_url if coupon_checkout_url else f"{FRONTEND_URL}/planos"
    cta_text = "Voltar com 20% off" if coupon_checkout_url else "Reativar acesso"

    body = f"""
    {_preheader(preheader_text)}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      {headline}
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Ola, {user_name}! Seu trial expirou, mas seus dados ficam salvos por 30 dias.
      Reative o acesso para continuar de onde parou.
    </p>
    {_stats_block(stats, show_pipeline=True) if (opps > 0 or pipeline > 0) else ''}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0;">
            Seus dados ficam salvos por 30 dias — buscas, pipeline e historico.
          </p>
        </td>
      </tr>
    </table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td align="center"
            style="background: linear-gradient(135deg, {SMARTLIC_GREEN}, #1B5E20); border-radius: 12px; padding: 20px;">
          <p style="color: #ffffff; font-size: 13px; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 1px;">
            Oferta exclusiva de retorno
          </p>
          <p style="color: #ffffff; font-size: 28px; font-weight: 700; margin: 0;">
            20% OFF
          </p>
          <p style="color: rgba(255,255,255,0.85); font-size: 14px; margin: 4px 0 0;">
            no primeiro mes do SmartLic Pro
          </p>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{cta_url}" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        {cta_text}
      </a>
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Sentimos sua falta — SmartLic",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )
