#!/usr/bin/env python3
"""
Download e extração de texto de documentos de editais do PNCP.

Suporta: PDF (com OCR fallback), ZIP, RAR, XLS, XLSX.

Usage:
    python scripts/intel-extract-docs.py --input docs/intel/intel-XXX.json
    python scripts/intel-extract-docs.py --input data.json --top 10
    python scripts/intel-extract-docs.py --input data.json --top 5 --output enriched.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# ============================================================
# Windows console encoding fix
# ============================================================
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass  # Already wrapped or buffer closed

# ============================================================
# CONSTANTS
# ============================================================

VERSION = "1.0.0"

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024  # 50 MB per file
MAX_TEXT_PER_EDITAL = 60_000           # chars
MAX_DOCS_PER_EDITAL = 3               # top-priority documents
DOWNLOAD_TIMEOUT_S = 60               # seconds
DOWNLOAD_RATE_LIMIT_S = 0.2           # seconds between downloads
OCR_CHARS_PER_PAGE_THRESHOLD = 100    # trigger OCR if avg chars/page below this

# ============================================================
# OPTIONAL DEPENDENCY IMPORTS (soft — warn and skip if missing)
# ============================================================

try:
    import httpx
    _HTTPX_OK = True
except ImportError:
    _HTTPX_OK = False
    print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

try:
    import fitz  # PyMuPDF
    _FITZ_OK = True
except ImportError:
    _FITZ_OK = False
    print("WARN: PyMuPDF (fitz) not installed — PDFs will be skipped. Run: pip install pymupdf")

try:
    import zipfile as _zipfile_mod
    _ZIP_OK = True
except ImportError:
    _ZIP_OK = False  # stdlib — should always be present

try:
    import rarfile as _rarfile_mod
    _RAR_OK = True
except ImportError:
    _RAR_OK = False
    print("WARN: rarfile not installed — RAR archives will be skipped. Run: pip install rarfile")

try:
    from openpyxl import load_workbook as _openpyxl_load
    _OPENPYXL_OK = True
except ImportError:
    _OPENPYXL_OK = False
    print("WARN: openpyxl not installed — XLSX files will be skipped. Run: pip install openpyxl")

try:
    import xlrd as _xlrd_mod
    _XLRD_OK = True
except ImportError:
    _XLRD_OK = False
    print("WARN: xlrd not installed — XLS files will be skipped. Run: pip install xlrd")

# ── Structured extraction templates (optional) ──
try:
    from lib.doc_templates import extract_structured, detect_doc_type, merge_extractions, DocType
    _DOC_TEMPLATES_OK = True
except ImportError:
    _DOC_TEMPLATES_OK = False

# ── Victory profile (optional) ──
try:
    from lib.victory_profile import build_victory_profile, score_edital_fit, format_fit_label
    _VICTORY_PROFILE_OK = True
except ImportError:
    _VICTORY_PROFILE_OK = False


# ============================================================
# TEXT EXTRACTION — PDF
# ============================================================

def extract_pdf(path: str) -> str:
    """Extract text from a PDF.

    Primary: pymupdf4llm.to_markdown() — preserves table structure for better LLM analysis.
    Fallback: PyMuPDF page.get_text() with pytesseract OCR for scanned PDFs.
    """
    # --- Primary: pymupdf4llm (markdown output preserves tables) ---
    try:
        import pymupdf4llm  # type: ignore[import]
        text = pymupdf4llm.to_markdown(path)
        return text[:MAX_TEXT_PER_EDITAL]
    except ImportError:
        pass  # Not installed — fall through to PyMuPDF direct extraction
    except Exception as exc:
        print(f"    ⚠ pymupdf4llm falhou para {Path(path).name}: {exc} — usando fallback")

    # --- Fallback: PyMuPDF direct extraction ---
    if not _FITZ_OK:
        print(f"    ⚠ PyMuPDF not available — skipping {Path(path).name}")
        return ""

    try:
        doc = fitz.open(path)  # type: ignore[name-defined]
    except Exception as exc:
        print(f"    ⚠ Falha ao abrir PDF {Path(path).name}: {exc}")
        return ""

    texts: list[str] = []
    for page in doc:
        try:
            texts.append(page.get_text())
        except Exception:
            texts.append("")

    full_text = "\n".join(texts)
    page_count = max(len(doc), 1)
    avg_chars = len(full_text) / page_count

    if avg_chars < OCR_CHARS_PER_PAGE_THRESHOLD:
        # OCR fallback
        try:
            import pytesseract
            from PIL import Image

            print(f"    → OCR fallback (avg {avg_chars:.0f} chars/pag, PDF: {Path(path).name})")
            ocr_texts: list[str] = []
            for page in doc:
                try:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img, lang="por")
                    ocr_texts.append(ocr_text)
                except Exception as ocr_exc:
                    print(f"    ⚠ OCR falhou na página: {ocr_exc}")
                    ocr_texts.append("")
            ocr_full = "\n".join(ocr_texts)
            if len(ocr_full) > len(full_text):
                full_text = ocr_full
        except ImportError:
            print(f"    ⚠ pytesseract/Pillow não instalado — OCR ignorado para {Path(path).name}")

    doc.close()
    return full_text


# ============================================================
# TEXT EXTRACTION — SPREADSHEETS
# ============================================================

def extract_spreadsheet(path: str) -> str:
    """Extract cell text from XLS or XLSX spreadsheets."""
    ext = Path(path).suffix.lower()
    texts: list[str] = []

    if ext == ".xlsx":
        if not _OPENPYXL_OK:
            print(f"    ⚠ openpyxl não instalado — ignorando {Path(path).name}")
            return ""
        try:
            wb = _openpyxl_load(path, read_only=True, data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    row_text = " | ".join(
                        str(c) for c in row if c is not None and str(c).strip()
                    )
                    if row_text.strip():
                        texts.append(row_text)
            wb.close()
        except Exception as exc:
            print(f"    ⚠ Erro ao ler XLSX {Path(path).name}: {exc}")

    elif ext == ".xls":
        if not _XLRD_OK:
            print(f"    ⚠ xlrd não instalado — ignorando {Path(path).name}")
            return ""
        try:
            wb = _xlrd_mod.open_workbook(path)
            for ws in wb.sheets():
                for row_idx in range(ws.nrows):
                    row_text = " | ".join(
                        str(ws.cell_value(row_idx, col))
                        for col in range(ws.ncols)
                        if ws.cell_value(row_idx, col) not in (None, "")
                    )
                    if row_text.strip():
                        texts.append(row_text)
        except Exception as exc:
            print(f"    ⚠ Erro ao ler XLS {Path(path).name}: {exc}")

    return "\n".join(texts)


# ============================================================
# TEXT EXTRACTION — ARCHIVES (ZIP / RAR)
# ============================================================

def extract_archive(path: str, archive_type: str) -> str:
    """Extract text from all recognisable files inside a ZIP or RAR archive."""
    tmpdir = tempfile.mkdtemp(prefix="intel_arc_")
    try:
        if archive_type == "zip":
            if not _ZIP_OK:
                print(f"    ⚠ zipfile não disponível — ignorando {Path(path).name}")
                return ""
            try:
                with _zipfile_mod.ZipFile(path, "r") as zf:
                    zf.extractall(tmpdir)
            except Exception as exc:
                print(f"    ⚠ Erro ao extrair ZIP {Path(path).name}: {exc}")
                return ""

        elif archive_type == "rar":
            if not _RAR_OK:
                print(f"    ⚠ rarfile não instalado — ignorando {Path(path).name}")
                return ""
            try:
                with _rarfile_mod.RarFile(path, "r") as rf:
                    rf.extractall(tmpdir)
            except Exception as exc:
                print(f"    ⚠ Erro ao extrair RAR {Path(path).name}: {exc}")
                return ""

        else:
            print(f"    ⚠ Tipo de arquivo desconhecido: {archive_type}")
            return ""

        texts: list[str] = []
        for root, _dirs, files in os.walk(tmpdir):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                ext = Path(fname).suffix.lower()
                if ext == ".pdf":
                    sub_text = extract_pdf(fpath)
                    if sub_text.strip():
                        texts.append(sub_text)
                elif ext in (".xlsx", ".xls"):
                    sub_text = extract_spreadsheet(fpath)
                    if sub_text.strip():
                        texts.append(sub_text)
                # Skip other formats silently

        return "\n\n".join(texts)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ============================================================
# DOCUMENT PRIORITIZATION
# ============================================================

def _doc_priority(doc: dict[str, Any]) -> int:
    """
    Lower number = higher priority.
    P1: edital
    P2: termo / referencia / referência
    P3: planilha or .xls/.xlsx suffix
    P4: everything else
    """
    titulo = (doc.get("titulo") or "").lower()
    tipo = (doc.get("tipo") or "").lower()
    combined = titulo + " " + tipo
    url = (doc.get("download_url") or "").lower()

    if "edital" in combined:
        return 1
    if any(w in combined for w in ("termo", "referência", "referencia")):
        return 2
    if "planilha" in combined or url.endswith((".xls", ".xlsx")):
        return 3
    return 4


def prioritize_docs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return docs sorted by priority (P1 first), filtering out inactive ones."""
    active = [d for d in docs if d.get("ativo", True) and d.get("download_url")]
    return sorted(active, key=_doc_priority)


# ============================================================
# DOWNLOAD + DETECT FORMAT
# ============================================================

def _detect_format(content_type: str, url: str, local_path: str) -> str:
    """
    Detect file format from Content-Type header, URL extension, or magic bytes.
    Returns one of: 'pdf', 'zip', 'rar', 'xlsx', 'xls', 'unknown'.
    """
    ct = content_type.lower()
    if "pdf" in ct:
        return "pdf"
    if "zip" in ct or "x-zip" in ct:
        return "zip"
    if "rar" in ct or "x-rar" in ct:
        return "rar"
    if "spreadsheetml" in ct or "vnd.openxmlformats" in ct:
        return "xlsx"
    if "ms-excel" in ct or "vnd.ms-excel" in ct:
        return "xls"

    # Fallback: extension from URL
    ext = Path(url.split("?")[0]).suffix.lower()
    if ext in (".pdf", ".zip", ".rar", ".xlsx", ".xls"):
        return ext.lstrip(".")

    # Magic bytes (sniff first 8 bytes)
    try:
        with open(local_path, "rb") as f:
            header = f.read(8)
        if header[:4] == b"%PDF":
            return "pdf"
        if header[:4] == b"PK\x03\x04":
            return "zip"
        if header[:7] == b"Rar!\x1a\x07\x00" or header[:8] == b"Rar!\x1a\x07\x01\x00":
            return "rar"
        # XLSX is also a ZIP with specific internal structure
        # If PK magic and xlsx suffix → xlsx already handled above
    except Exception:
        pass

    return "unknown"


def download_and_extract(doc: dict[str, Any], tmpdir: str) -> str:
    """
    Download a single document and extract its text.
    Returns extracted text string (may be empty on failure).
    """
    url = doc.get("download_url")
    titulo = doc.get("titulo") or doc.get("tipo") or "sem-titulo"

    if not url:
        return ""

    print(f"    Baixando: {titulo[:60]}")

    # Stream download with size check
    try:
        with httpx.Client(timeout=DOWNLOAD_TIMEOUT_S, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    print(f"    ⚠ HTTP {resp.status_code} para {url[:80]}")
                    return ""

                content_length = resp.headers.get("content-length")
                if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                    print(f"    ⚠ Arquivo muito grande ({int(content_length) // (1024*1024)}MB > 50MB) — ignorado")
                    return ""

                content_type = resp.headers.get("content-type", "")
                chunks: list[bytes] = []
                downloaded = 0
                for chunk in resp.iter_bytes(chunk_size=65536):
                    downloaded += len(chunk)
                    if downloaded > MAX_DOWNLOAD_BYTES:
                        print(f"    ⚠ Arquivo excedeu 50MB durante download — abortado")
                        return ""
                    chunks.append(chunk)

                raw = b"".join(chunks)

    except httpx.TimeoutException:
        print(f"    ⚠ Timeout ao baixar {url[:80]}")
        return ""
    except Exception as exc:
        print(f"    ⚠ Erro ao baixar {url[:80]}: {exc}")
        return ""

    # Save to tmpdir
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in titulo[:50])
    local_path = os.path.join(tmpdir, safe_name or "doc")
    try:
        with open(local_path, "wb") as f:
            f.write(raw)
    except Exception as exc:
        print(f"    ⚠ Erro ao salvar arquivo temporário: {exc}")
        return ""

    fmt = _detect_format(content_type, url, local_path)
    print(f"    Formato detectado: {fmt} ({len(raw) // 1024}KB)")

    if fmt == "pdf":
        text = extract_pdf(local_path)
    elif fmt == "zip":
        text = extract_archive(local_path, "zip")
    elif fmt == "rar":
        text = extract_archive(local_path, "rar")
    elif fmt in ("xlsx", "xls"):
        text = extract_spreadsheet(local_path)
    else:
        print(f"    ⚠ Formato '{fmt}' não suportado — ignorado")
        text = ""

    return text


# ============================================================
# PER-EDITAL PROCESSING
# ============================================================

def process_edital(edital: dict[str, Any], idx: int, total: int) -> None:
    """Download and extract text for one edital. Mutates `edital` in-place."""
    objeto = (edital.get("objeto") or "")[:80]
    print(f"\n[{idx}/{total}] {objeto}")

    docs = edital.get("documentos") or []
    if not docs:
        edital["texto_documentos"] = ""
        print("  Sem documentos listados")
        return

    prioritized = prioritize_docs(docs)
    if not prioritized:
        edital["texto_documentos"] = ""
        print(f"  {len(docs)} documento(s) sem URL válida ou todos inativos")
        return

    to_download = prioritized[:MAX_DOCS_PER_EDITAL]
    print(f"  {len(docs)} documento(s) disponíveis — processando {len(to_download)} prioritários")

    tmpdir = tempfile.mkdtemp(prefix="intel_edital_")
    try:
        all_text_parts: list[str] = []
        # Track (doc_metadata, extracted_text) pairs for structured extraction
        doc_text_pairs: list[tuple[dict[str, Any], str]] = []
        success_count = 0

        for doc in to_download:
            text = download_and_extract(doc, tmpdir)
            if text and text.strip():
                all_text_parts.append(text.strip())
                doc_text_pairs.append((doc, text.strip()))
                success_count += 1
            time.sleep(DOWNLOAD_RATE_LIMIT_S)

        combined = "\n\n---\n\n".join(all_text_parts)

        if len(combined) > MAX_TEXT_PER_EDITAL:
            combined = combined[:MAX_TEXT_PER_EDITAL] + "\n\n[... texto truncado em 60.000 caracteres ...]"

        edital["texto_documentos"] = combined
        print(f"  Extraído: {len(combined):,} chars de {success_count}/{len(to_download)} documentos")

        # ── Structured extraction by document type ──
        if _DOC_TEMPLATES_OK and doc_text_pairs:
            extractions = []
            for doc_meta, text_part in doc_text_pairs:
                doc_titulo = doc_meta.get("titulo") or doc_meta.get("tipo") or ""
                doc_filename = (doc_meta.get("download_url") or "").rsplit("/", 1)[-1]
                detected_type = detect_doc_type(doc_titulo, doc_filename)
                extraction = extract_structured(text_part, detected_type)
                extractions.append(extraction)

            if extractions:
                merged = merge_extractions(extractions)
                total_fields = sum(ext.total_fields for ext in extractions)
                found_count = sum(1 for f in merged.values() if f.found)
                completeness = round(found_count / max(len(merged), 1) * 100, 1) if merged else 0.0
                doc_types_processed = list({
                    ext.doc_type.value for ext in extractions if ext.doc_type != DocType.UNKNOWN
                })

                edital["_structured_extraction"] = {
                    "fields": {
                        name: {
                            "found": f.found,
                            "value": f.value,
                            "confidence": f.confidence,
                        }
                        for name, f in merged.items()
                    },
                    "completeness_pct": completeness,
                    "doc_types_processed": doc_types_processed,
                }
                print(f"  Extração estruturada: {found_count} campos encontrados, {completeness}% completude, tipos: {doc_types_processed}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ============================================================
# FILTERING & SORTING
# ============================================================

def _dedup_key(e: dict[str, Any]) -> str:
    """Generate a dedup key from orgao CNPJ + year + sequential number."""
    orgao = (e.get("orgao_cnpj") or "").replace("/", "").replace(".", "").replace("-", "").strip()
    ano = str(e.get("ano") or e.get("ano_compra") or "")
    seq = str(e.get("sequencial") or e.get("numero_sequencial") or "")
    if orgao and ano and seq:
        return f"{orgao}/{ano}/{seq}"
    # Fallback: normalize objeto text for similarity-based dedup
    obj = (e.get("objeto") or "").lower().strip()
    # Remove Portal de Compras prefix
    for prefix in ["[portal de compras públicas] - ", "[portal de compras publicas] - "]:
        if obj.startswith(prefix):
            obj = obj[len(prefix):]
    valor = e.get("valor_estimado") or 0
    uf = e.get("uf") or ""
    return f"{uf}|{valor}|{obj[:100]}"


def calculate_opportunity_score(
    edital: dict[str, Any],
    capacidade_10x: float,
    victory_profile: Any = None,
) -> float:
    """Score editais for top20 ranking. Higher = better opportunity.

    Args:
        edital: Edital dict with valor_estimado, distancia, status_temporal, etc.
        capacidade_10x: Company capacity (capital_social * 10).
        victory_profile: Optional VictoryProfile from lib.victory_profile.
            When provided and has_data, blends historical fit into the score.
    """
    valor = edital.get('valor_estimado') or 0
    dist_km = (edital.get('distancia') or {}).get('km')
    status = edital.get('status_temporal', 'PLANEJAVEL')

    # Base score = valor normalized to capacity
    if capacidade_10x > 0:
        base_score = min(valor / capacidade_10x, 1.0)
    else:
        base_score = 0

    # Distance penalty
    if dist_km is None:
        dist_penalty = 0.15  # Unknown distance = moderate penalty
    elif dist_km <= 100:
        dist_penalty = 0.0
    elif dist_km <= 300:
        dist_penalty = 0.10
    elif dist_km <= 500:
        dist_penalty = 0.25
    elif dist_km <= 700:
        dist_penalty = 0.40
    else:
        dist_penalty = 0.60  # >700km = heavy penalty

    # Temporal bonus
    temporal_bonus = {'URGENTE': 0.10, 'IMINENTE': 0.05, 'PLANEJAVEL': 0.0, 'SEM_DATA': -0.05}.get(status, 0)

    # Existing score (unchanged when no victory_profile)
    existing_score = base_score * (1 - dist_penalty) + temporal_bonus

    # Victory profile blending
    if _VICTORY_PROFILE_OK and victory_profile is not None and hasattr(victory_profile, 'has_data') and victory_profile.has_data:
        fit_score = score_edital_fit(edital, victory_profile)
        edital['_victory_fit'] = round(fit_score, 4)
        edital['_victory_fit_label'] = format_fit_label(fit_score)
        score = 0.6 * existing_score + 0.4 * fit_score
    else:
        score = existing_score

    # SESSAO_REALIZADA = opportunity lost — exclude entirely
    if status == 'SESSAO_REALIZADA':
        return 0.0

    return round(score, 4)


def select_top_editais(
    editais: list[dict[str, Any]],
    capital_social: float,
    top_n: int,
    victory_profile: Any = None,
) -> list[dict[str, Any]]:
    """
    Filter editais by CNAE compatibility + valor capacity, dedup, sort by opportunity
    score (valor × proximity × urgency), return top N.

    Args:
        victory_profile: Optional VictoryProfile. When provided, blends historical
            fit into opportunity scoring (0.6 existing + 0.4 victory fit).
    """
    capacidade_10x = capital_social * 10
    capacidade_3x = capital_social * 3

    candidates: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for e in editais:
        if not e.get("cnae_compatible"):
            continue
        valor = e.get("valor_estimado")
        # STRICT capacity filter: only include if valor > 0 AND within capacity
        # valor == 0 or None means sigiloso — include as unknown
        if valor is not None and valor > 0 and valor > capacidade_10x:
            continue
        # Skip expired and already-held sessions — only open opportunities
        if e.get("status_temporal") in ("EXPIRADO", "SESSAO_REALIZADA"):
            continue
        # Hard cutoff: >700km AND valor < capacidade_3x — exclude from top20
        dist_km = (e.get('distancia') or {}).get('km')
        if dist_km is not None and dist_km > 700:
            v = valor or 0
            if capacidade_3x > 0 and v < capacidade_3x:
                continue
        # Dedup: skip if we've already seen this edital
        key = _dedup_key(e)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidates.append(e)

    # Score and sort by opportunity score desc
    for e in candidates:
        e['_opportunity_score'] = calculate_opportunity_score(e, capacidade_10x, victory_profile)
    candidates.sort(key=lambda e: e.get('_opportunity_score') or 0, reverse=True)
    return candidates[:top_n]


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download e extração de texto de documentos de editais (PDF, ZIP, RAR, XLS, XLSX).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="JSON",
        help="Caminho para o JSON gerado pelo intel-collect.py",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        metavar="N",
        help="Número de editais top por valor a processar (padrão: 20)",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="JSON",
        help="Caminho do JSON de saída (padrão: sobrescreve --input)",
    )
    parser.add_argument(
        "--preserve-top20",
        action="store_true",
        help="Preservar top20 existente no JSON (não sobrescrever seleção anterior)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path

    # ── Load JSON ──
    print(f"Carregando {input_path}...")
    with open(input_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    empresa = data.get("empresa") or {}
    raw_capital = empresa.get("capital_social", 0)
    # capital_social may arrive as string (e.g. "1232000,00" from OpenCNPJ)
    if isinstance(raw_capital, str):
        capital_social = float(raw_capital.replace(".", "").replace(",", ".") or 0)
    else:
        capital_social = float(raw_capital or 0)

    capacidade = capital_social * 10
    empresa_nome = empresa.get("razao_social") or empresa.get("nome") or "Empresa"

    editais: list[dict[str, Any]] = data.get("editais") or []

    print(f"Empresa: {empresa_nome}")
    print(f"Capital social: R$ {capital_social:,.2f} | Capacidade estimada: R$ {capacidade:,.2f}")
    print(f"Total de editais na base: {len(editais)}")

    # ── Build victory profile from competitive_intel (if available) ──
    victory_profile = None
    if _VICTORY_PROFILE_OK:
        all_contracts: list[dict[str, Any]] = []
        # Collect contracts from competitive_intel across all editais
        for ed in editais:
            ci = ed.get("competitive_intel") or {}
            contracts_list = ci.get("contratos") or ci.get("contracts") or []
            if isinstance(contracts_list, list):
                all_contracts.extend(contracts_list)
        # Also check top-level competitive_intel
        top_ci = data.get("competitive_intel") or {}
        top_contracts = top_ci.get("contratos") or top_ci.get("contracts") or []
        if isinstance(top_contracts, list):
            all_contracts.extend(top_contracts)

        if all_contracts:
            victory_profile = build_victory_profile(all_contracts, capital_social)
            if victory_profile.has_data:
                print(f"Perfil de vitória: {victory_profile.total_contracts} contratos, "
                      f"valor médio R$ {victory_profile.valor_mean:,.0f}, "
                      f"UFs: {list(victory_profile.uf_weights.keys())[:5]}")
            else:
                print(f"Perfil de vitória: apenas {victory_profile.total_contracts} contrato(s) — mínimo 3 necessários, ignorando")
                victory_profile = None

    # ── Filter + select top N ──
    if args.preserve_top20 and data.get("top20"):
        top = data["top20"]
        print(f"\n--preserve-top20: Usando {len(top)} editais existentes")
        # Only process editais that don't have text yet
        to_process = [ed for ed in top if not ed.get("texto_documentos")]
        if to_process:
            print(f"  {len(to_process)} editais sem texto \u2014 processando")
            for i, ed in enumerate(to_process, 1):
                process_edital(ed, i, len(to_process))
        else:
            print("  Todos j\u00e1 t\u00eam texto extra\u00eddo")
        compat_total = sum(1 for e in editais if e.get("cnae_compatible"))
        print(
            f"\nFiltrados: {compat_total} CNAE-compat\u00edveis, "
            f"{len(top)} no top20 preservado"
        )
    else:
        top = select_top_editais(editais, capital_social, args.top, victory_profile)

        compat_total = sum(1 for e in editais if e.get("cnae_compatible"))
        print(
            f"\nFiltrados: {compat_total} CNAE-compat\u00edveis, "
            f"{len(top)} dentro da capacidade \u2192 processando top {args.top}"
        )

        if not top:
            print("\nNenhum edital eleg\u00edvel encontrado. Saindo.")
            data["top20"] = []
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSON salvo: {output_path}")
            return

        print(f"\nProcessando {len(top)} editais (top {args.top} por score, capacidade R$ {capacidade:,.0f})")

        # ── Print top scoring summary ──
        print(f"\n  Top {len(top)} por score (valor x proximidade x urgencia):")
        for rank, ed in enumerate(top, 1):
            score = ed.get('_opportunity_score', 0)
            valor_ed = ed.get('valor_estimado') or 0
            municipio = ed.get('municipio') or ed.get('municipio_orgao') or '?'
            uf_ed = ed.get('uf') or ''
            loc = f"{municipio}/{uf_ed}" if uf_ed else municipio
            dist_km = (ed.get('distancia') or {}).get('km')
            dist_str = f"{dist_km:.0f}km" if dist_km is not None else "dist?"
            status_ed = ed.get('status_temporal') or 'SEM_DATA'
            valor_str = f"R${valor_ed/1e6:.0f}M" if valor_ed >= 1e6 else f"R${valor_ed/1e3:.0f}k" if valor_ed >= 1e3 else f"R${valor_ed:.0f}"
            print(f"    #{rank} score={score:.2f} {valor_str} {loc} ({dist_str}, {status_ed})")

        # ── Process each edital ──
        for i, ed in enumerate(top, 1):
            process_edital(ed, i, len(top))

    # ── Quality scoring ──
    for ed in top:
        texto = ed.get("texto_documentos") or ""
        text_len = len(texto)
        texto_lower = texto.lower()

        # Check for key edital sections in extracted text
        key_sections = {
            "habilitacao": any(kw in texto_lower for kw in ["habilita\u00e7\u00e3o", "habilitacao", "habilita\u00e7"]),
            "qualificacao": any(kw in texto_lower for kw in ["qualifica\u00e7\u00e3o econ\u00f4mic", "qualificacao economic", "patrim\u00f4nio l\u00edquido", "patrimonio liquido", "capital social"]),
            "garantia": any(kw in texto_lower for kw in ["garantia", "cau\u00e7\u00e3o", "cau\u00e7ao", "seguro-garantia"]),
            "prazo": any(kw in texto_lower for kw in ["prazo de execu\u00e7\u00e3o", "prazo de execucao", "meses", "dias corridos"]),
            "sessao": any(kw in texto_lower for kw in ["sess\u00e3o p\u00fablica", "sessao publica", "data da sess\u00e3o", "data da sessao", "abertura da sess\u00e3o"]),
            "visita": any(kw in texto_lower for kw in ["visita t\u00e9cnica", "visita tecnica", "vistoria"]),
            "consorcio": any(kw in texto_lower for kw in ["cons\u00f3rcio", "consorcio"]),
        }
        sections_found = sum(1 for v in key_sections.values() if v)

        if text_len >= 10000 and sections_found >= 3:
            quality = "COMPLETO"
        elif text_len >= 2000 or sections_found >= 1:
            quality = "PARCIAL"
        elif text_len > 0:
            quality = "INSUFICIENTE"
        else:
            quality = "VAZIO"

        ed["extraction_quality"] = quality
        ed["extraction_chars"] = text_len
        ed["extraction_sections"] = key_sections

    # ── Quality summary ──
    quality_counts: dict[str, int] = {}
    for ed in top:
        q = ed.get("extraction_quality", "N/A")
        quality_counts[q] = quality_counts.get(q, 0) + 1

    print(f"\n  Qualidade extra\u00e7\u00e3o: {quality_counts}")

    # ── Update JSON ──
    # Upsert top20 key (exactly 20 max); overflow goes to _backlog
    data["top20"] = top[:20]
    if len(top) > 20:
        data["_backlog"] = top[20:]
    else:
        data["_backlog"] = []

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    docs_extracted = sum(1 for e in top if e.get("texto_documentos"))
    total_chars = sum(len(e.get("texto_documentos") or "") for e in top)

    print(f"\n{'─' * 60}")
    print(f"JSON atualizado: {output_path}")
    print(f"top20: {len(data['top20'])} editais | _backlog: {len(data['_backlog'])} | {docs_extracted} com texto extra\u00eddo | {total_chars:,} chars total")


if __name__ == "__main__":
    main()
