"""
Base email template — STORY-225

Responsive HTML email wrapper compatible with Gmail, Outlook, Apple Mail.
AC18: Footer includes company info and privacy policy link.
"""

SMARTLIC_GREEN = "#2E7D32"
SMARTLIC_DARK = "#1B5E20"
FRONTEND_URL = "https://smartlic.tech"


def email_base(
    title: str,
    body_html: str,
    unsubscribe_url: str = "",
    is_transactional: bool = True,
) -> str:
    """
    Wrap email body in responsive HTML template.

    AC9: Responsive HTML design.
    AC17: Transactional emails exempt from unsubscribe.
    AC18: Footer includes company info and privacy policy link.

    Args:
        title: Email subject (used in <title> tag).
        body_html: Inner HTML content.
        unsubscribe_url: URL for unsubscribe link (empty = no link shown).
        is_transactional: If True, no unsubscribe link (AC17).
    """
    unsubscribe_section = ""
    if not is_transactional and unsubscribe_url:
        unsubscribe_section = f"""
        <tr>
          <td align="center" style="padding: 12px 0 0;">
            <a href="{unsubscribe_url}"
               style="color: #999; font-size: 12px; text-decoration: underline;">
              Cancelar inscrição de emails promocionais
            </a>
          </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style>
    body {{ margin: 0; padding: 0; background-color: #f4f4f4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
    .container {{ max-width: 600px; margin: 0 auto; }}
    .btn {{ display: inline-block; padding: 14px 32px; background-color: {SMARTLIC_GREEN}; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; }}
    .btn:hover {{ background-color: {SMARTLIC_DARK}; }}
    @media only screen and (max-width: 620px) {{
      .container {{ width: 100% !important; }}
      .content {{ padding: 24px 16px !important; }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td align="center" style="background-color: {SMARTLIC_GREEN}; padding: 24px;">
              <span style="font-size: 28px; font-weight: 700; color: #ffffff; letter-spacing: 1px;">SmartLic</span>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td class="content" style="padding: 32px;">
              {body_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 24px 32px; background-color: #fafafa; border-top: 1px solid #eee;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="color: #888; font-size: 12px; line-height: 1.6;">
                    SmartLic &mdash; Inteligência em Licitações<br>
                    <a href="{FRONTEND_URL}/privacidade" style="color: #888; text-decoration: underline;">Política de Privacidade</a>
                    &nbsp;|&nbsp;
                    <a href="{FRONTEND_URL}/termos" style="color: #888; text-decoration: underline;">Termos de Uso</a>
                  </td>
                </tr>
                {unsubscribe_section}
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
