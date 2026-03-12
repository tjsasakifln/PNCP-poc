#!/usr/bin/env python3
"""
Coleta semi-automática de dados SICAF via Playwright.

Abre o navegador, preenche o CNPJ, aguarda o usuário resolver
o hCaptcha (~5 segundos), e extrai os dados automaticamente.

Persiste cookies da sessão para que consultas subsequentes
(modo batch) não exijam captcha novamente.

Usage:
    python scripts/collect-sicaf.py --cnpj 01721078000168
    python scripts/collect-sicaf.py --cnpj 01.721.078/0001-68 --output sicaf.json
    python scripts/collect-sicaf.py --cnpj 01721078000168,09225035000101  # batch

Requires:
    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext
except ImportError:
    print("ERROR: playwright não instalado. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


# ============================================================
# CONSTANTS
# ============================================================

SICAF_BASE = "https://www3.comprasnet.gov.br/sicaf-web"
CRC_URL = f"{SICAF_BASE}/public/pages/consultas/consultarCRC.jsf"
RESTRICAO_URL = f"{SICAF_BASE}/public/pages/consultas/consultarRestricaoContratarAdministracaoPublica.jsf"
LINHAS_URL = f"{SICAF_BASE}/public/pages/consultas/consultarLinhaFornecimento.jsf"

COOKIES_PATH = Path(__file__).parent.parent / ".sicaf-cookies.json"
CAPTCHA_TIMEOUT = 120  # seconds to wait for user to solve captcha
NAVIGATION_TIMEOUT = 15000  # ms


# ============================================================
# HELPERS
# ============================================================

def _clean_cnpj(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", cnpj).zfill(14)


def _format_cnpj(cnpj14: str) -> str:
    c = cnpj14
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _source_tag(status: str, detail: str = "") -> dict:
    tag = {"status": status, "timestamp": _now_iso()}
    if detail:
        tag["detail"] = detail
    return tag


# ============================================================
# CAPTCHA HANDLING
# ============================================================

def _wait_for_captcha(page: Page, quiet: bool = False) -> bool:
    """Wait for user to solve hCaptcha. Returns True if solved."""
    if not quiet:
        print("\n  ⏳ Resolva o hCaptcha no navegador que abriu...")
        print("     (clique no checkbox 'Sou humano' e complete o desafio)")

    start = time.time()
    while time.time() - start < CAPTCHA_TIMEOUT:
        try:
            # Check if captcha iframe has the response token set
            # hCaptcha sets a textarea[name="h-captcha-response"] with the token
            token = page.evaluate("""
                () => {
                    const ta = document.querySelector('textarea[name="h-captcha-response"]');
                    return ta ? ta.value : '';
                }
            """)
            if token:
                if not quiet:
                    print("  ✓ Captcha resolvido!")
                return True
        except Exception:
            pass
        time.sleep(0.5)

    if not quiet:
        print("  ✗ Timeout aguardando captcha")
    return False


def _is_captcha_present(page: Page) -> bool:
    """Check if hCaptcha is present on the page."""
    try:
        iframe = page.query_selector("iframe[src*='hcaptcha']")
        return iframe is not None
    except Exception:
        return False


# ============================================================
# COOKIE PERSISTENCE
# ============================================================

def _save_cookies(context: BrowserContext) -> None:
    """Save browser cookies for session reuse."""
    cookies = context.cookies()
    COOKIES_PATH.write_text(json.dumps(cookies, indent=2), encoding="utf-8")


def _load_cookies(context: BrowserContext) -> bool:
    """Load saved cookies. Returns True if cookies were loaded."""
    if not COOKIES_PATH.exists():
        return False
    try:
        cookies = json.loads(COOKIES_PATH.read_text(encoding="utf-8"))
        if cookies:
            context.add_cookies(cookies)
            return True
    except (json.JSONDecodeError, Exception):
        pass
    return False


# ============================================================
# CRC EXTRACTION
# ============================================================

def _fill_cnpj(page: Page, cnpj14: str) -> None:
    """Fill CNPJ field using multiple selector strategies."""
    cnpj_fmt = _format_cnpj(cnpj14)
    # Strategy 1: aria label
    cnpj_input = page.get_by_label("CNPJ").first
    if cnpj_input.is_visible(timeout=2000):
        cnpj_input.fill(cnpj_fmt)
        return
    # Strategy 2: input with id containing cnpj
    cnpj_input = page.locator("input[id*='cnpj'], input[id*='Cnpj']").first
    if cnpj_input.is_visible(timeout=2000):
        cnpj_input.fill(cnpj_fmt)
        return
    # Strategy 3: first text input inside the search fieldset
    cnpj_input = page.locator("fieldset input[type='text'], .ui-inputtext").first
    cnpj_input.fill(cnpj_fmt)


def _collect_crc(page: Page, cnpj14: str, quiet: bool = False) -> dict:
    """Collect CRC (Certificado de Registro Cadastral) data.

    The CRC page has a "Relatório" button that triggers a PDF download.
    We intercept the download, save the PDF, and extract text from it.
    If the company is not registered, an error message appears instead.
    """
    result = {
        "tipo": "CRC",
        "cnpj": _format_cnpj(cnpj14),
        "_source": _source_tag("UNAVAILABLE", "Não consultado"),
    }

    try:
        page.goto(CRC_URL, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        _fill_cnpj(page, cnpj14)
        page.wait_for_timeout(500)

        # Handle captcha
        if _is_captcha_present(page):
            if not _wait_for_captcha(page, quiet):
                result["_source"] = _source_tag("API_FAILED", "Captcha não resolvido")
                return result

        # Click "Relatório" — this triggers a PDF download
        # Use expect_download to capture the file
        try:
            with page.expect_download(timeout=15000) as download_info:
                page.get_by_role("button", name="Relatório").click()
            download = download_info.value
            # Save PDF to temp dir
            pdf_path = Path(os.environ.get("TEMP", "/tmp")) / f"sicaf_crc_{cnpj14}.pdf"
            download.save_as(str(pdf_path))
            result["status_cadastral"] = "CADASTRADO"
            result["pdf_path"] = str(pdf_path)
            result["pdf_filename"] = download.suggested_filename or f"CRC_{cnpj14}.pdf"
            result["_source"] = _source_tag("API", f"CRC PDF baixado: {pdf_path.name}")

            # Try to extract text from PDF
            crc_text = _extract_pdf_text(pdf_path)
            if crc_text:
                result["conteudo_extraido"] = crc_text[:3000]
                # Parse structured fields from CRC text
                parsed = _parse_crc_text(crc_text)
                result.update(parsed)

            if not quiet:
                print(f"    PDF CRC salvo: {pdf_path}")

        except Exception as dl_err:
            # Download didn't happen — check for error messages on page
            page.wait_for_timeout(2000)

            # Look for error/warning messages OUTSIDE the search form
            error_el = page.locator(
                ".ui-messages-error-summary, .ui-messages-warn-summary, "
                ".ui-growl-message, [class*='message']"
            ).first
            if error_el.is_visible(timeout=1000):
                error_text = error_el.text_content() or ""
                error_clean = error_text.strip()
                if not quiet:
                    print(f"    SICAF CRC: {error_clean}")

                is_not_registered = (
                    "não possui" in error_clean.lower()
                    or "não encontrad" in error_clean.lower()
                    or "não cadastrad" in error_clean.lower()
                    or "credenciamento não cadastrado" in error_clean.lower()
                )
                if is_not_registered:
                    result["status_cadastral"] = "NÃO CADASTRADO"
                    result["detalhe"] = error_clean
                    result["_source"] = _source_tag("API", f"SICAF CRC: {error_clean[:80]}")
                elif "captcha" in error_clean.lower():
                    result["_source"] = _source_tag("API_FAILED", "Captcha necessário")
                else:
                    result["status_cadastral"] = "VERIFICAR"
                    result["detalhe"] = error_clean
                    result["_source"] = _source_tag("API", f"SICAF CRC: {error_clean[:80]}")
            else:
                result["_source"] = _source_tag("API_FAILED", f"Download não iniciou: {str(dl_err)[:80]}")

    except Exception as e:
        if not quiet:
            print(f"  ✗ Erro CRC: {e}")
        result["_source"] = _source_tag("API_FAILED", str(e)[:100])

    return result


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF file. Tries multiple methods."""
    # Method 1: PyPDF2/pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        text_parts = []
        for pg in reader.pages:
            text_parts.append(pg.extract_text() or "")
        return "\n".join(text_parts)
    except ImportError:
        pass
    except Exception:
        pass

    # Method 2: pdfminer (if available)
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(pdf_path))
    except ImportError:
        pass
    except Exception:
        pass

    # Method 3: reportlab can't read, but note the file exists
    return ""


def _parse_crc_text(text: str) -> dict:
    """Parse structured fields from CRC PDF text.

    The CRC PDF has a specific structure where labels and values
    are on different lines (PDF text extraction puts them sequentially).

    Example CRC text:
        CNPJ:
        Razão Social:

        26.420.889/0001-50
        GAMARRA CONSTRUTORA E LOCADORA LTDA

        Atividade Econômica Principal:

        4120-4/00 - CONSTRUÇÃO DE EDIFÍCIOS

        Endereço:

        RUA ODILON LINHARES, ...
    """
    data = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Strategy 1: Find labels and extract the value from subsequent lines
    label_map = {
        "razao_social": ["Razão Social", "Razao Social"],
        "cnpj_sicaf": ["CNPJ:"],
        "atividade_principal": ["Atividade Econômica Principal", "Atividade Economica"],
        "endereco": ["Endereço", "Endereco"],
        "porte": ["Porte"],
        "natureza_juridica": ["Natureza Jurídica", "Natureza Juridica"],
        "nome_fantasia": ["Nome Fantasia"],
    }

    # The CRC PDF has labels like "CNPJ:\nRazão Social:\n\n26.420.889/0001-50\nGAMARRA..."
    # Labels appear together, then values appear together in same order.
    # Special handling: find the CNPJ value first, then razão social is the next line.
    cnpj_line_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", line):
            cnpj_line_idx = i
            data["cnpj_sicaf"] = line
            break

    if cnpj_line_idx is not None and cnpj_line_idx + 1 < len(lines):
        candidate = lines[cnpj_line_idx + 1]
        if not candidate.endswith(":") and not re.match(r"^\d{2}\.\d{3}", candidate):
            data["razao_social"] = candidate[:200]

    for key, labels in label_map.items():
        if key in ("cnpj_sicaf", "razao_social"):
            continue  # Already handled above
        for i, line in enumerate(lines):
            if any(label.lower() in line.lower() for label in labels):
                # The value is typically 1-3 lines after the label
                for offset in range(1, 4):
                    if i + offset < len(lines):
                        candidate = lines[i + offset]
                        # Skip empty or label-like lines
                        if candidate.endswith(":") or len(candidate) < 2:
                            continue
                        data[key] = candidate[:200]
                        break
                break

    # Strategy 2: Regex patterns for inline format (fallback)
    if "razao_social" not in data:
        m = re.search(r"Raz[ãa]o Social[:\s]+(.+?)(?:\n|$)", text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Filter out CNPJ-like values (the PDF puts them on same line sometimes)
            if not re.match(r"^\d{2}\.\d{3}\.\d{3}", val):
                data["razao_social"] = val[:200]

    # Extract observações
    m = re.search(r"Observa[çc][õo]es[:\s]*\n(.+?)(?:\n\n|Emitido)", text, re.IGNORECASE | re.DOTALL)
    if m:
        data["observacoes"] = m.group(1).strip()[:500]

    # Extract emission date
    m = re.search(r"Emitido em[:\s]*(\d{2}/\d{2}/\d{4})", text)
    if m:
        data["data_emissao"] = m.group(1)

    # Extract habilitação levels (for more complete CRCs)
    hab_patterns = {
        "habilitacao_juridica": r"Habilita[çc][ãa]o Jur[ií]dica[:\s]*(Regular|Irregular|Vencid[ao]|N[ãa]o)",
        "regularidade_fiscal_federal": r"(?:Regularidade )?Fiscal Federal[:\s]*(Regular|Irregular|Vencid[ao]|N[ãa]o)",
        "regularidade_fiscal_estadual": r"(?:Regularidade )?Fiscal Estadual[:\s]*(Regular|Irregular|Vencid[ao]|N[ãa]o)",
        "regularidade_fiscal_municipal": r"(?:Regularidade )?Fiscal Municipal[:\s]*(Regular|Irregular|Vencid[ao]|N[ãa]o)",
        "regularidade_trabalhista": r"(?:Regularidade )?Trabalhista[:\s]*(Regular|Irregular|Vencid[ao]|N[ãa]o)",
        "qualificacao_economica": r"Qualifica[çc][ãa]o Econ[oô]mic[ao][:\s]*(Regular|Irregular|Vencid[ao]|N[ãa]o)",
    }
    habilitacao = {}
    for key, pattern in hab_patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            habilitacao[key] = m.group(1).strip()
    if habilitacao:
        data["habilitacao"] = habilitacao

    return data


# ============================================================
# RESTRIÇÃO EXTRACTION
# ============================================================

def _collect_restricao(page: Page, cnpj14: str, quiet: bool = False) -> dict:
    """Collect restriction data (Restrição Contratar Administração Pública)."""
    result = {
        "tipo": "RESTRICAO",
        "cnpj": _format_cnpj(cnpj14),
        "_source": _source_tag("UNAVAILABLE", "Não consultado"),
    }

    try:
        page.goto(RESTRICAO_URL, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        _fill_cnpj(page, cnpj14)
        page.wait_for_timeout(500)

        # Handle captcha
        if _is_captcha_present(page):
            if not _wait_for_captcha(page, quiet):
                result["_source"] = _source_tag("API_FAILED", "Captcha não resolvido")
                return result

        # Click "Pesquisar"
        page.get_by_role("button", name="Pesquisar").click()
        page.wait_for_timeout(3000)

        # Check for messages (captcha error, not-registered, etc)
        error_el = page.locator(
            ".ui-messages-error-summary, .ui-messages-warn-summary, "
            ".ui-growl-message, .ui-messages-info-summary"
        ).first
        msg_text = ""
        if error_el.is_visible(timeout=2000):
            msg_text = (error_el.text_content() or "").strip()
            if "captcha" in msg_text.lower():
                result["_source"] = _source_tag("API_FAILED", "Captcha necessário")
                return result
            if not quiet:
                print(f"    SICAF Restrição: {msg_text}")

        msg_lower = msg_text.lower()

        # "Fornecedor não credenciado" = not registered, so no restrictions apply
        # "não possui restrição" = registered, no restrictions
        # "nenhum registro" = no restrictions found
        is_clean = (
            "não credenciad" in msg_lower
            or "não possui" in msg_lower
            or "nenhum registro" in msg_lower
            or "não encontrad" in msg_lower
        )

        if is_clean:
            result["possui_restricao"] = False
            result["detalhe"] = msg_text or "Nenhuma restrição encontrada"
            result["_source"] = _source_tag("API", f"Sem restrições: {msg_text[:60]}")
        elif msg_text:
            # Has a message that's not "clean" — might indicate restrictions
            # Check the result section for details
            result_section = page.locator("fieldset").nth(1)
            if result_section.is_visible(timeout=2000):
                restricoes = _extract_restricoes(result_section)
                if restricoes:
                    result["possui_restricao"] = True
                    result["restricoes"] = restricoes
                    result["detalhe"] = f"{len(restricoes)} restrição(ões) encontrada(s)"
                    result["_source"] = _source_tag("API", f"{len(restricoes)} restrições SICAF")
                else:
                    result["possui_restricao"] = False
                    result["detalhe"] = msg_text
                    result["_source"] = _source_tag("API", f"Restrição: {msg_text[:60]}")
            else:
                result["possui_restricao"] = False
                result["detalhe"] = msg_text
                result["_source"] = _source_tag("API", f"Restrição: {msg_text[:60]}")
        else:
            # No message and no clear signal — check result area
            result_section = page.locator("fieldset").nth(1)
            if result_section.is_visible(timeout=2000):
                result_text = (result_section.text_content() or "").strip()
                # Filter out navigation noise
                for noise in ("Realizar nova pesquisa", "Voltar para página inicial"):
                    result_text = result_text.replace(noise, "")
                result_text = result_text.strip()

                if not result_text or len(result_text) < 10:
                    result["possui_restricao"] = False
                    result["detalhe"] = "Nenhuma restrição encontrada"
                    result["_source"] = _source_tag("API", "Sem restrições no SICAF")
                else:
                    restricoes = _extract_restricoes(result_section)
                    result["possui_restricao"] = bool(restricoes)
                    if restricoes:
                        result["restricoes"] = restricoes
                        result["detalhe"] = f"{len(restricoes)} restrição(ões)"
                    else:
                        result["detalhe"] = result_text[:200]
                    result["_source"] = _source_tag("API", "Consulta restrição realizada")
            else:
                result["possui_restricao"] = False
                result["detalhe"] = "Resultado não visível"
                result["_source"] = _source_tag("API_PARTIAL", "Resultado não carregou")

    except Exception as e:
        if not quiet:
            print(f"  ✗ Erro Restrição: {e}")
        result["_source"] = _source_tag("API_FAILED", str(e)[:100])

    return result


def _extract_restricoes(result_section) -> list[dict]:
    """Extract restriction details from the result section (NOT the search form)."""
    restricoes = []
    try:
        # Target data table rows inside the result section only
        rows = result_section.locator(
            ".ui-datatable-data tr, table:not(:first-child) tbody tr"
        ).all()
        for row in rows[:20]:
            cells = row.locator("td").all()
            # Skip rows that look like form elements (radio buttons etc)
            if len(cells) < 2:
                continue
            cell_texts = [(c.text_content() or "").strip() for c in cells]
            # Filter out radio button labels
            if any(t in ("Pessoa Jurídica", "Pessoa Física", "Estrangeiro") for t in cell_texts):
                continue
            restricao = {"tipo": cell_texts[0], "detalhe": cell_texts[1]}
            if len(cell_texts) >= 3:
                restricao["orgao"] = cell_texts[2]
            if len(cell_texts) >= 4:
                restricao["data"] = cell_texts[3]
            restricoes.append(restricao)

        # If no table rows, try extracting from panel text
        if not restricoes:
            text = (result_section.text_content() or "").strip()
            # Remove common noise
            for noise in ("Realizar nova pesquisa", "Voltar para página inicial"):
                text = text.replace(noise, "")
            text = text.strip()
            if text and len(text) > 10:
                restricoes.append({"tipo": "SICAF", "detalhe": text[:500]})

    except Exception:
        pass
    return restricoes


# ============================================================
# LINHAS DE FORNECIMENTO
# ============================================================

def _collect_linhas(page: Page, cnpj14: str, quiet: bool = False) -> dict:
    """Collect supply lines (Linhas de Fornecimento)."""
    result = {
        "tipo": "LINHAS_FORNECIMENTO",
        "cnpj": _format_cnpj(cnpj14),
        "_source": _source_tag("UNAVAILABLE", "Não consultado"),
    }

    try:
        page.goto(LINHAS_URL, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        _fill_cnpj(page, cnpj14)
        page.wait_for_timeout(500)

        # Handle captcha
        if _is_captcha_present(page):
            if not _wait_for_captcha(page, quiet):
                result["_source"] = _source_tag("API_FAILED", "Captcha não resolvido")
                return result

        # Click submit button (may be "Pesquisar" or "Relatório")
        pesquisar_btn = page.get_by_role("button", name="Pesquisar")
        if pesquisar_btn.is_visible(timeout=2000):
            pesquisar_btn.click()
        else:
            page.get_by_role("button", name="Relatório").click()
        page.wait_for_timeout(3000)

        # Extract results
        body_text = page.locator("body").text_content() or ""

        if "nenhum registro" in body_text.lower() or "não encontrad" in body_text.lower():
            result["linhas"] = []
            result["detalhe"] = "Nenhuma linha de fornecimento cadastrada"
            result["_source"] = _source_tag("API", "Sem linhas de fornecimento")
        else:
            linhas = _extract_linhas(page)
            result["linhas"] = linhas
            result["detalhe"] = f"{len(linhas)} linha(s) de fornecimento"
            result["_source"] = _source_tag("API", f"{len(linhas)} linhas de fornecimento")

    except Exception as e:
        if not quiet:
            print(f"  ✗ Erro Linhas: {e}")
        result["_source"] = _source_tag("API_FAILED", str(e)[:100])

    return result


def _extract_linhas(page: Page) -> list[dict]:
    """Extract supply line details, skipping header rows."""
    linhas = []
    header_values = {"material", "serviço", "servico", "código", "codigo", "descrição", "descricao", "linha"}
    try:
        # Target result section (second fieldset)
        result_section = page.locator("fieldset").nth(1)
        if not result_section.is_visible(timeout=2000):
            result_section = page.locator("body")

        rows = result_section.locator(
            ".ui-datatable-data tr, table tbody tr"
        ).all()
        for row in rows[:50]:
            cells = row.locator("td").all()
            if len(cells) >= 2:
                code = (cells[0].text_content() or "").strip()
                desc = (cells[1].text_content() or "").strip()
                # Skip header-like rows
                if code.lower() in header_values and desc.lower() in header_values:
                    continue
                if not code and not desc:
                    continue
                linhas.append({"codigo": code, "descricao": desc})
    except Exception:
        pass
    return linhas


# ============================================================
# MAIN COLLECTION
# ============================================================

def collect_sicaf(
    cnpjs: list[str],
    output: str | None = None,
    quiet: bool = False,
    skip_linhas: bool = False,
) -> list[dict]:
    """
    Collect SICAF data for one or more CNPJs.

    Opens a headed browser, waits for user to solve captcha once,
    then reuses cookies for subsequent queries.
    """
    results = []

    with sync_playwright() as p:
        # Launch headed browser so user can solve captcha
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="pt-BR",
        )

        # Try loading saved cookies
        cookies_loaded = _load_cookies(context)
        if cookies_loaded and not quiet:
            print("  ℹ Cookies de sessão anterior carregados")

        page = context.new_page()
        page.set_default_timeout(NAVIGATION_TIMEOUT)

        captcha_solved_once = False

        for i, cnpj_raw in enumerate(cnpjs):
            cnpj14 = _clean_cnpj(cnpj_raw)
            cnpj_fmt = _format_cnpj(cnpj14)

            if not quiet:
                print(f"\n{'='*60}")
                print(f"📋 SICAF — {cnpj_fmt} ({i+1}/{len(cnpjs)})")
                print(f"{'='*60}")

            sicaf_data = {
                "cnpj": cnpj_fmt,
                "cnpj_limpo": cnpj14,
                "consulta_timestamp": _now_iso(),
            }

            # 1. CRC
            if not quiet:
                print("\n  1/3 Certificado de Registro Cadastral (CRC)...")
            crc = _collect_crc(page, cnpj14, quiet)
            sicaf_data["crc"] = crc

            if crc["_source"]["status"] == "API":
                captcha_solved_once = True
                _save_cookies(context)

            # 2. Restrição
            if not quiet:
                print("  2/3 Restrição Contratar Administração Pública...")
            restricao = _collect_restricao(page, cnpj14, quiet)
            sicaf_data["restricao"] = restricao

            if restricao["_source"]["status"] == "API":
                _save_cookies(context)

            # 3. Linhas de Fornecimento
            if not skip_linhas:
                if not quiet:
                    print("  3/3 Linhas de Fornecimento...")
                linhas = _collect_linhas(page, cnpj14, quiet)
                sicaf_data["linhas_fornecimento"] = linhas
            else:
                sicaf_data["linhas_fornecimento"] = {
                    "tipo": "LINHAS_FORNECIMENTO",
                    "_source": _source_tag("UNAVAILABLE", "Skipped"),
                }

            # Build consolidated status
            all_sources = [
                crc["_source"]["status"],
                restricao["_source"]["status"],
            ]
            if not skip_linhas:
                all_sources.append(sicaf_data["linhas_fornecimento"]["_source"]["status"])

            if all(s == "API" for s in all_sources):
                sicaf_data["_source"] = _source_tag("API", "SICAF completo via Playwright")
                sicaf_data["status"] = _build_status_summary(crc, restricao)
            elif any(s == "API" for s in all_sources):
                sicaf_data["_source"] = _source_tag("API_PARTIAL", "SICAF parcial")
                sicaf_data["status"] = _build_status_summary(crc, restricao)
            else:
                sicaf_data["_source"] = _source_tag("API_FAILED", "SICAF não consultado")
                sicaf_data["status"] = "NÃO CONSULTADO"

            results.append(sicaf_data)

            if not quiet:
                print(f"\n  ✅ SICAF {cnpj_fmt}: {sicaf_data['status']}")

        # Cleanup
        _save_cookies(context)
        browser.close()

    # Save output
    if output:
        out_path = Path(output)
        data_out = results[0] if len(results) == 1 else results
        out_path.write_text(json.dumps(data_out, indent=2, ensure_ascii=False), encoding="utf-8")
        if not quiet:
            print(f"\n📦 Dados SICAF salvos em: {out_path}")

    return results


def _build_status_summary(crc: dict, restricao: dict) -> str:
    """Build a human-readable SICAF status summary."""
    parts = []

    # CRC status
    crc_status = crc.get("status_cadastral", "")
    if crc_status:
        parts.append(f"CRC: {crc_status}")
    else:
        parts.append("CRC: Consultado")

    # Restriction status
    if restricao.get("possui_restricao") is True:
        n = len(restricao.get("restricoes", []))
        parts.append(f"Restrições: {n} encontrada(s) ⚠")
    elif restricao.get("possui_restricao") is False:
        parts.append("Restrições: Nenhuma ✓")

    return " | ".join(parts)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Coleta semi-automática de dados SICAF via Playwright"
    )
    parser.add_argument(
        "--cnpj", required=True,
        help="CNPJ(s) para consultar (separados por vírgula para batch)",
    )
    parser.add_argument("--output", help="Caminho do arquivo JSON de saída")
    parser.add_argument("--quiet", action="store_true", help="Menos output no console")
    parser.add_argument("--skip-linhas", action="store_true", help="Pular Linhas de Fornecimento")
    parser.add_argument(
        "--clear-cookies", action="store_true",
        help="Limpar cookies salvos (força novo captcha)",
    )
    args = parser.parse_args()

    if args.clear_cookies and COOKIES_PATH.exists():
        COOKIES_PATH.unlink()
        print("🗑 Cookies limpos")

    cnpjs = [c.strip() for c in args.cnpj.split(",") if c.strip()]

    if not cnpjs:
        print("ERROR: Nenhum CNPJ fornecido")
        sys.exit(1)

    print(f"🔍 SICAF Collector — {len(cnpjs)} CNPJ(s)")
    print(f"   Navegador vai abrir. Resolva o captcha quando solicitado.")

    results = collect_sicaf(
        cnpjs=cnpjs,
        output=args.output,
        quiet=args.quiet,
        skip_linhas=args.skip_linhas,
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 Resumo SICAF")
    print(f"{'='*60}")
    for r in results:
        src = r["_source"]["status"]
        emoji = "✓" if src == "API" else "~" if src == "API_PARTIAL" else "✗"
        print(f"  {emoji} {r['cnpj']}: {r.get('status', 'N/A')}")


if __name__ == "__main__":
    main()
