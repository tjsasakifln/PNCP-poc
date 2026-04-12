"""
STORY-321 AC7-AC9: Trial email templates — 6 emails over 14-day trial.

Compressed sequence (replaces STORY-310 8-email sequence):
- Day 0:  Welcome — onboarding CTA ("Fazer primeira busca")
- Day 3:  Engagement — stats de uso, destaques ("Explorar mais setores")
- Day 7:  Paywall alert — paywall ativa amanhã ("Assine antes do limite")
- Day 10: Valor acumulado — social proof R$X ("Não perca esse progresso")
- Day 13: Último dia — escassez ("Assinar agora")
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
        Análises realizadas
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
        Não desejo receber emails sobre o trial
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
    {_preheader("Seu trial de 14 dias começou. Faça sua primeira análise agora.")}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Bem-vindo ao SmartLic, {user_name}!
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Seu trial de 14 dias começou. Agora você tem acesso completo à
      plataforma de inteligência em licitações mais avançada do Brasil.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0 0 12px; font-weight: 600;">
            3 passos para começar:
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
                Faça sua primeira análise com IA
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
        Fazer primeira análise
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Seu trial gratuito de 14 dias começou hoje.
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
        preheader_text = f"Você já analisou {_format_brl(value)} em oportunidades"
        headline = f"Você já analisou {_format_brl(value)} em oportunidades"
        intro = (
            f"Olá, {user_name}! Em apenas 3 dias no SmartLic, você já está "
            f"descobrindo oportunidades reais de licitação."
        )
    elif has_usage and opps > 0:
        preheader_text = f"{opps} oportunidades encontradas em 3 dias"
        headline = f"{opps} oportunidades encontradas em 3 dias"
        intro = (
            f"Olá, {user_name}! Você já encontrou {opps} oportunidades. "
            f"Explore mais setores para ampliar seus resultados."
        )
    else:
        preheader_text = "Você ainda tem 11 dias para descobrir oportunidades"
        headline = "Você ainda tem 11 dias para descobrir oportunidades"
        intro = (
            f"Olá, {user_name}! Seu trial do SmartLic está apenas começando e "
            f"há oportunidades esperando por você. Faça sua primeira análise agora!"
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
        value_line = f"Você já descobriu <strong>{_format_brl(value)}</strong> em oportunidades. "
    else:
        value_line = ""

    body = f"""
    {_preheader("A partir de hoje, resultados ficam limitados. Assine para acesso completo.")}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Metade do trial — preview limitado a partir de hoje
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Você está na metade do seu trial de 14 dias.
      {value_line}A partir de hoje, os resultados de busca serão
      exibidos em modo preview (limitado a 10 resultados).
    </p>
    {_stats_block(stats, show_pipeline=True) if has_usage else ''}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #fff3e0; border-radius: 8px; padding: 16px; border-left: 4px solid #ff9800;">
          <p style="color: #e65100; font-size: 14px; margin: 0; font-weight: 600;">
            O que muda a partir de hoje:
          </p>
          <ul style="color: #555; font-size: 14px; margin: 8px 0 0; padding-left: 20px;">
            <li>Resultados limitados a 10 por busca (preview)</li>
            <li>Pipeline limitado a 5 itens</li>
            <li>Análises e IA continuam funcionando normalmente</li>
          </ul>
        </td>
      </tr>
    </table>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Assine o SmartLic Pro <strong>agora</strong> e recupere acesso
      completo a todos os resultados, pipeline ilimitado e relatórios Excel.
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
        title="Metade do trial — preview limitado a partir de hoje",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #4 — Day 10: Valor Acumulado (AC7 — NEW)
# ============================================================================

def _top_opportunity_block(stats: dict) -> str:
    """STORY-371 AC2: Render personalized top opportunity block for day 10 email."""
    top_opp = stats.get("top_opportunity")
    if not top_opp or not top_opp.get("objeto"):
        return ""
    objeto = top_opp.get("objeto", "")
    orgao = top_opp.get("orgao_nome", "")
    valor = top_opp.get("valor_formatado", "")
    dias = top_opp.get("dias_ate_encerramento")
    numero = top_opp.get("numero_controle", "")

    prazo_text = ""
    if dias is not None:
        if dias == 0:
            prazo_text = " · vence hoje"
        elif dias == 1:
            prazo_text = " · vence amanhã"
        else:
            prazo_text = f" · vence em {dias} dias"

    cta_url = f"{FRONTEND_URL}/buscar?highlight={numero}" if numero else f"{FRONTEND_URL}/buscar"

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="margin: 16px 0 24px;">
      <tr>
        <td style="border: 2px solid #1a6cf6; border-radius: 8px; padding: 16px;">
          <p style="color: #888; font-size: 12px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 1px;">
            📋 Sua maior oportunidade identificada
          </p>
          <p style="color: #1a1a2e; font-size: 16px; font-weight: 600; margin: 0 0 6px; line-height: 1.4;">
            {objeto}
          </p>
          {"<p style='color: #555; font-size: 14px; margin: 0 0 6px;'>" + orgao + "</p>" if orgao else ""}
          <p style="color: #1a6cf6; font-size: 15px; font-weight: 700; margin: 0 0 12px;">
            {valor}{prazo_text}
          </p>
          <a href="{cta_url}"
             style="display: inline-block; padding: 10px 20px; background-color: #1a6cf6; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">
            Ver este edital agora →
          </a>
        </td>
      </tr>
    </table>"""


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
        preheader_text = f"Você já analisou {big_value} em oportunidades. Não perca."
        headline = f"Você já analisou {big_value}"
    elif opps > 0:
        preheader_text = f"{opps} oportunidades encontradas. Não perca esse progresso."
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
      Olá, {user_name}! Seu trial termina em 4 dias. Veja o progresso que você
      construiu até agora:
    </p>
    {value_highlight}
    {_top_opportunity_block(stats)}
    {_stats_block(stats, show_pipeline=True) if value == 0 and opps > 0 else ''}
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
      Não perca esse progresso. Com o SmartLic Pro, você mantém acesso a tudo:
      análises ilimitadas, IA de classificação, pipeline e relatórios Excel.
    </p>
    <tr><td style="padding: 20px 30px;">
      <p style="font-size: 15px; color: #1a1a2e; margin: 0 0 12px;">
        <strong>Sabia que voce pode ganhar ate 7 dias extras?</strong>
      </p>
      <p style="font-size: 14px; color: #4a4a6a; margin: 0 0 16px;">
        Complete seu perfil (+3 dias), de feedback sobre uma busca (+2 dias)
        ou convide um colega (+7 dias).
      </p>
      <a href="{FRONTEND_URL}/dashboard" style="display:inline-block;background:#2563eb;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;">
        Ver minhas opcoes
      </a>
    </td></tr>
    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Não perca esse progresso
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Economize 20% com o plano anual.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Você já analisou oportunidades — SmartLic",
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
    opps = stats.get("opportunities_found", 0)  # noqa: F841

    if value > 0:
        preheader_text = f"Amanhã você perde acesso a {_format_brl(value)} em oportunidades."
    else:
        preheader_text = "Amanhã seu acesso expira. Assine agora."

    body = f"""
    {_preheader(preheader_text)}
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
            Economia de 20% no plano anual
          </p>
        </td>
      </tr>
    </table>

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/planos" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: #d32f2f; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Assinar agora — R$ 397/mês
      </a>
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Último dia de trial — SmartLic",
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
            headline = f"Suas {pipeline} oportunidades estão esperando por você"
        else:
            headline = f"Suas {opps} oportunidades estão esperando por você"
        preheader_text = "Sentimos sua falta. Volte com 20% off."
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
      Olá, {user_name}! Seu trial expirou, mas seus dados ficam salvos por 30 dias.
      Reative o acesso para continuar de onde parou.
    </p>
    {_stats_block(stats, show_pipeline=True) if (opps > 0 or pipeline > 0) else ''}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0;">
            Seus dados ficam salvos por 30 dias — análises, pipeline e histórico.
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
            no primeiro mês do SmartLic Pro
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


# ============================================================================
# Email #10 — Day 2: Feature Discovery — Pipeline (Zero-Churn P1 Frente 2B)
# ============================================================================

def render_trial_feature_pipeline_email(user_name: str, stats: dict, unsubscribe_url: str = "") -> str:
    """Day 2 — Feature discovery: Pipeline kanban for tracking opportunities.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    body = f"""
    {_preheader("Organize suas oportunidades com o Pipeline drag-and-drop do SmartLic.")}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Organize suas oportunidades no Pipeline
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Você sabia que o SmartLic tem um pipeline visual
      estilo kanban para acompanhar suas oportunidades de ponta a ponta?
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0 0 12px; font-weight: 600;">
            O que você pode fazer no Pipeline:
          </p>
          <ul style="color: #555; font-size: 14px; margin: 0; padding-left: 20px;">
            <li style="padding: 4px 0;">Arraste oportunidades entre colunas (Lead → Análise → Proposta → Ganho)</li>
            <li style="padding: 4px 0;">Acompanhe prazos e valores de cada edital</li>
            <li style="padding: 4px 0;">Tenha uma visão consolidada de todo o seu funil B2G</li>
          </ul>
        </td>
      </tr>
    </table>

    {_stats_block(stats) if stats.get("searches_count", 0) > 0 else ''}

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/pipeline" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Abrir meu Pipeline
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Dica: após uma busca, clique em "Adicionar ao Pipeline" em qualquer oportunidade.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Organize suas oportunidades no Pipeline — SmartLic",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #11 — Day 5: Feature Discovery — Excel Export (Zero-Churn P1 Frente 2B)
# ============================================================================

def render_trial_feature_excel_email(user_name: str, stats: dict, unsubscribe_url: str = "") -> str:
    """Day 5 — Feature discovery: Excel export for sharing with team.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    body = f"""
    {_preheader("Exporte suas análises para Excel estilizado e compartilhe com a equipe.")}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      Exporte análises para Excel com 1 clique
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Precisa compartilhar oportunidades com sua equipe ou
      diretoria? O SmartLic gera relatórios Excel estilizados prontos para apresentação.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0 0 12px; font-weight: 600;">
            O relatório Excel inclui:
          </p>
          <ul style="color: #555; font-size: 14px; margin: 0; padding-left: 20px;">
            <li style="padding: 4px 0;">Lista completa de oportunidades com classificação IA</li>
            <li style="padding: 4px 0;">Score de viabilidade e análise por fator</li>
            <li style="padding: 4px 0;">Formatação profissional pronta para decisão</li>
          </ul>
        </td>
      </tr>
    </table>

    {_stats_block(stats) if stats.get("searches_count", 0) > 0 else ''}

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/buscar" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Exportar meu primeiro relatório
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Dica: após uma busca, clique em "Exportar Excel" no topo dos resultados.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="Exporte análises para Excel — SmartLic",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


# ============================================================================
# Email #12 — Day 8: Feature Discovery — AI Classification (Zero-Churn P1 Frente 2B)
# ============================================================================

def render_trial_feature_ai_email(user_name: str, stats: dict, unsubscribe_url: str = "") -> str:
    """Day 8 — Feature discovery: AI classification across 15 sectors.

    Args:
        user_name: User's display name.
        stats: Dict with keys from TrialUsageStats.
        unsubscribe_url: URL for one-click unsubscribe.
    """
    body = f"""
    {_preheader("A IA do SmartLic classifica oportunidades em 15 setores e calcula viabilidade.")}
    <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
      IA classifica oportunidades para você
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Olá, {user_name}! Você está usando todo o poder da IA do SmartLic?
      Nossa inteligência artificial analisa cada edital e entrega apenas
      o que importa para o seu negócio.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px;">
      <tr>
        <td style="background-color: #e8f5e9; border-radius: 8px; padding: 16px; border-left: 4px solid {SMARTLIC_GREEN};">
          <p style="color: #1b5e20; font-size: 14px; margin: 0 0 12px; font-weight: 600;">
            Como a IA trabalha para você:
          </p>
          <ul style="color: #555; font-size: 14px; margin: 0; padding-left: 20px;">
            <li style="padding: 4px 0;">Classificação automática em 15 setores especializados</li>
            <li style="padding: 4px 0;">Score de viabilidade com 4 fatores (modalidade, prazo, valor, geografia)</li>
            <li style="padding: 4px 0;">Economia de horas filtrando editais irrelevantes automaticamente</li>
          </ul>
        </td>
      </tr>
    </table>

    {_stats_block(stats) if stats.get("searches_count", 0) > 0 else ''}

    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/buscar" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        Ver classificação IA
      </a>
    </p>
    <p style="color: #888; font-size: 13px; text-align: center; margin: 16px 0 0;">
      Dica: na página de resultados, veja o badge de relevância e o score de viabilidade de cada edital.
    </p>
    {_unsubscribe_block(unsubscribe_url)}
    """

    return email_base(
        title="IA classifica oportunidades para você — SmartLic",
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )
