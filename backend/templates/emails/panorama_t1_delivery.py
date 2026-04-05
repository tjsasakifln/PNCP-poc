"""Panorama 2026 T1 delivery email — sent after a lead requests the PDF.

Delivers the download link plus 3 teaser insights and a soft CTA to start
a trial. Transactional (no unsubscribe link required).
"""

from templates.emails.base import email_base, SMARTLIC_GREEN, FRONTEND_URL


def render_panorama_t1_delivery(empresa: str, download_url: str) -> str:
    """Render the Panorama 2026 T1 delivery HTML email.

    Args:
        empresa: Company name (used in greeting).
        download_url: Public URL to the PDF on Supabase Storage.
    """
    trial_url = f"{FRONTEND_URL}/signup?utm_source=panorama_t1&utm_medium=email"

    body = f"""
    <h1 style="color: #333; font-size: 24px; margin: 0 0 16px;">
      Olá, time da {empresa}
    </h1>
    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
      Obrigado por baixar o <strong>Panorama Licitações Brasil 2026 T1</strong>.
      O PDF está disponível no link abaixo — 8 a 10 páginas de análise
      data-driven sobre o primeiro trimestre do ano no PNCP.
    </p>

    <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 24px auto;">
      <tr>
        <td align="center" style="background: {SMARTLIC_GREEN}; border-radius: 8px;">
          <a href="{download_url}"
             style="display: inline-block; padding: 14px 32px; color: #ffffff;
                    text-decoration: none; font-weight: 600; font-size: 16px;">
            Baixar PDF (8-10 páginas)
          </a>
        </td>
      </tr>
    </table>

    <h2 style="color: #333; font-size: 18px; margin: 32px 0 12px;">
      3 insights exclusivos que você vai encontrar
    </h2>
    <ul style="color: #555; font-size: 15px; line-height: 1.7; padding-left: 20px; margin: 0 0 24px;">
      <li>
        <strong>R$ 14,2 bi em editais publicados no PNCP entre jan-mar/26</strong>
        — +12% vs 2025 T1.
      </li>
      <li>
        <strong>84% dos processos foram via pregão eletrônico</strong>,
        consolidando a migração pós-Lei 14.133.
      </li>
      <li>
        <strong>Top 3 setores (engenharia, saúde, TI) concentram 58% do valor total</strong>
        — com Sul e Sudeste respondendo por 67% dos grandes contratos.
      </li>
    </ul>

    <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 24px 0 16px;">
      Se quiser monitorar esses dados ao vivo, com alertas diários de editais
      compatíveis com seu setor e UF, teste o SmartLic gratuitamente por 14 dias.
    </p>

    <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 16px auto 8px;">
      <tr>
        <td align="center" style="border: 2px solid {SMARTLIC_GREEN}; border-radius: 8px;">
          <a href="{trial_url}"
             style="display: inline-block; padding: 12px 28px; color: {SMARTLIC_GREEN};
                    text-decoration: none; font-weight: 600; font-size: 15px;">
            Testar SmartLic grátis
          </a>
        </td>
      </tr>
    </table>

    <p style="color: #888; font-size: 13px; text-align: center; margin: 24px 0 0;">
      Dúvidas ou quer um recorte customizado? Responda este email.<br>
      CONFENGE Avaliações e Inteligência Artificial LTDA
    </p>
    """
    return email_base(
        title="Panorama Licitações Brasil 2026 T1 — seu download",
        body_html=body,
        is_transactional=True,
    )
