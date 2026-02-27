"""
STORY-301 AC15-AC18: Alert digest email template.

Renders a mobile-responsive email showing top 10 opportunities matching
a user-defined alert, with viability badges, value formatting, and
direct PNCP links per item.

Design:
- Header: "N novas oportunidades em {setor}" (AC15 subject line)
- Table: top 10 items with objeto, UF, valor, modalidade, link PNCP (AC16)
- CTA: "Ver todas as {total} oportunidades no SmartLic" -> /buscar (AC17)
- Footer: unsubscribe + preferences link (AC18)
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


# Viability badge colors and labels (same as digest.py)
_VIABILITY_COLORS = {
    "alta": {"bg": "#e8f5e9", "text": "#2e7d32", "label": "Alta viabilidade"},
    "media": {"bg": "#fff8e1", "text": "#f57f17", "label": "Viabilidade media"},
    "baixa": {"bg": "#ffebee", "text": "#c62828", "label": "Baixa viabilidade"},
}


def _format_brl(value: float) -> str:
    """Format a float as Brazilian Real currency string."""
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"R$ {value / 1_000:.0f}k"
    return f"R$ {value:,.0f}".replace(",", ".")


def _viability_badge(score: float | None) -> str:
    """Render an inline viability badge based on score.

    Args:
        score: Viability score 0.0-1.0, or None if not assessed.

    Returns:
        HTML string for the badge.
    """
    if score is None:
        return ""

    if score >= 0.7:
        style = _VIABILITY_COLORS["alta"]
    elif score >= 0.4:
        style = _VIABILITY_COLORS["media"]
    else:
        style = _VIABILITY_COLORS["baixa"]

    return (
        f'<span style="display: inline-block; padding: 2px 8px; '
        f'background-color: {style["bg"]}; color: {style["text"]}; '
        f'border-radius: 4px; font-size: 11px; font-weight: 600; '
        f'line-height: 1.4;">{style["label"]}</span>'
    )


def _render_opportunity_row(opp: dict, index: int) -> str:
    """Render a single opportunity row in the alert digest table.

    AC16: Each row shows objeto, UF, valor, modalidade, and link PNCP.

    Args:
        opp: Dict with keys: titulo, orgao, valor_estimado, uf, modalidade,
             link_pncp, viability_score.
        index: Row number (1-based).

    Returns:
        HTML table row string.
    """
    titulo = opp.get("titulo", "Sem titulo")
    if len(titulo) > 120:
        titulo = titulo[:117] + "..."

    orgao = opp.get("orgao", "Orgao nao informado")
    if len(orgao) > 60:
        orgao = orgao[:57] + "..."

    valor = opp.get("valor_estimado", 0.0) or 0.0
    uf = opp.get("uf", "\u2014")
    modalidade = opp.get("modalidade", "")
    link_pncp = opp.get("link_pncp", "")
    viability_score = opp.get("viability_score")

    badge = _viability_badge(viability_score)
    valor_display = _format_brl(valor) if valor > 0 else "Valor nao informado"
    modalidade_display = f" &middot; {modalidade}" if modalidade else ""

    bg_color = "#ffffff" if index % 2 == 1 else "#f9f9f9"

    # Title as link to PNCP if link available
    if link_pncp:
        titulo_html = (
            f'<a href="{link_pncp}" style="color: #333; text-decoration: none; '
            f'font-weight: 600;">{titulo}</a>'
        )
    else:
        titulo_html = f'<span style="font-weight: 600;">{titulo}</span>'

    return f"""
    <tr style="background-color: {bg_color};">
      <td style="padding: 12px 16px; border-bottom: 1px solid #eee; vertical-align: top;">
        <p style="margin: 0 0 4px; font-size: 14px; color: #333; line-height: 1.4;">
          {titulo_html}
        </p>
        <p style="margin: 0 0 4px; font-size: 13px; color: #666; line-height: 1.3;">
          {orgao} &mdash; {uf}{modalidade_display}
        </p>
        <p style="margin: 0; font-size: 13px;">
          <span style="color: {SMARTLIC_GREEN}; font-weight: 600;">{valor_display}</span>
          &nbsp;&nbsp;{badge}
        </p>
        {_render_pncp_link(link_pncp)}
      </td>
    </tr>"""


def _render_pncp_link(link_pncp: str) -> str:
    """Render a small 'Ver no PNCP' link below the opportunity details.

    Args:
        link_pncp: Full URL to the PNCP edital page.

    Returns:
        HTML string with the link, or empty string if no link.
    """
    if not link_pncp:
        return ""

    return (
        f'<p style="margin: 4px 0 0; font-size: 12px;">'
        f'<a href="{link_pncp}" style="color: #1976d2; text-decoration: underline;">'
        f'Ver no PNCP &rarr;</a></p>'
    )


def render_alert_digest_email(
    user_name: str,
    alert_name: str,
    opportunities: list[dict],
    total_count: int,
    unsubscribe_url: str,
) -> str:
    """Render the alert digest email.

    STORY-301 AC15-AC18: Alert digest with top 10 opportunities table,
    CTA to SmartLic, and unsubscribe/preferences footer.

    Args:
        user_name: User's display name.
        alert_name: Name of the alert (e.g., sector name or custom label).
        opportunities: List of dicts (max 10) with keys:
            titulo, orgao, valor_estimado, uf, modalidade, link_pncp, viability_score.
        total_count: Total number of new opportunities found (may be > len(opportunities)).
        unsubscribe_url: URL to unsubscribe from this alert.

    Returns:
        Complete HTML email string.
    """
    # AC15: Subject line uses alert_name (passed separately for email sending)
    # The title here is for the <title> tag in the HTML wrapper
    email_title = f"{total_count} novas oportunidades em {alert_name} \u2014 SmartLic"

    # Empty state: no new opportunities
    if not opportunities:
        body = f"""
        <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
          Ola, {user_name}!
        </h1>
        <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 8px;">
          Seu alerta <strong>{alert_name}</strong> nao encontrou novas oportunidades hoje.
        </p>
        <p style="color: #555; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
          Continuaremos monitorando e avisaremos assim que houver novidades.
        </p>
        <p style="text-align: center; margin: 24px 0 16px;">
          <a href="{FRONTEND_URL}/buscar" class="btn"
             style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
            Fazer busca manual
          </a>
        </p>
        <p style="color: #888; font-size: 12px; text-align: center; margin: 16px 0 0;">
          Para ajustar ou desativar este alerta,
          <a href="{FRONTEND_URL}/conta" style="color: #888; text-decoration: underline;">acesse suas preferencias</a>.
        </p>
        """
        return email_base(
            title=f"Alerta {alert_name} \u2014 SmartLic",
            body_html=body,
            is_transactional=False,
            unsubscribe_url=unsubscribe_url,
        )

    # Build opportunity rows (AC16: top 10)
    opp_rows = ""
    display_opps = opportunities[:10]
    for i, opp in enumerate(display_opps):
        opp_rows += _render_opportunity_row(opp, i + 1)

    # CTA text (AC17)
    if total_count > len(display_opps):
        cta_text = f"Ver todas as {total_count} oportunidades no SmartLic"
    else:
        cta_text = "Ver oportunidades no SmartLic"

    body = f"""
    <h1 style="color: #333; font-size: 22px; margin: 0 0 8px;">
      Ola, {user_name}!
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Seu alerta <strong>{alert_name}</strong> encontrou
      <strong>{total_count}</strong> nova{"s" if total_count != 1 else ""} oportunidade{"s" if total_count != 1 else ""}.
    </p>

    <!-- Stats highlight bar -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background-color: #e8f5e9; border-radius: 8px; margin: 0 0 24px;">
      <tr>
        <td style="padding: 12px 16px; text-align: center;">
          <span style="color: {SMARTLIC_GREEN}; font-size: 24px; font-weight: 700;">
            {total_count}
          </span>
          <span style="color: #555; font-size: 14px; margin-left: 8px;">
            {"oportunidade encontrada" if total_count == 1 else "oportunidades encontradas"}
          </span>
        </td>
      </tr>
    </table>

    <!-- Opportunities table (AC16) -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="border: 1px solid #eee; border-radius: 8px; overflow: hidden; margin: 0 0 24px;">
      <tr>
        <td style="padding: 10px 16px; background-color: #f5f5f5; border-bottom: 2px solid #eee;">
          <span style="font-size: 13px; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: 0.5px;">
            Top oportunidades &mdash; {alert_name}
          </span>
        </td>
      </tr>
      {opp_rows}
    </table>

    <!-- CTA (AC17) -->
    <p style="text-align: center; margin: 24px 0 16px;">
      <a href="{FRONTEND_URL}/buscar" class="btn"
         style="display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
        {cta_text}
      </a>
    </p>

    <!-- Footer preferences (AC18) -->
    <p style="color: #888; font-size: 12px; text-align: center; margin: 16px 0 0;">
      Viability badges indicam a relevancia da oportunidade para seu perfil.
      <br>
      Para ajustar ou desativar este alerta,
      <a href="{FRONTEND_URL}/conta" style="color: #888; text-decoration: underline;">acesse suas preferencias</a>.
    </p>
    """

    return email_base(
        title=email_title,
        body_html=body,
        is_transactional=False,
        unsubscribe_url=unsubscribe_url,
    )


def get_alert_digest_subject(total_count: int, alert_name: str) -> str:
    """Generate the email subject line for an alert digest.

    AC15: Subject format: "SmartLic -- {N} novas oportunidades em {setor}"

    Args:
        total_count: Number of new opportunities.
        alert_name: Alert name (typically the sector name).

    Returns:
        Email subject string.
    """
    if total_count == 0:
        return f"SmartLic \u2014 Nenhuma novidade em {alert_name}"
    if total_count == 1:
        return f"SmartLic \u2014 1 nova oportunidade em {alert_name}"
    return f"SmartLic \u2014 {total_count} novas oportunidades em {alert_name}"
