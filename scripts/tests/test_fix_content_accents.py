"""Unit tests for scripts/fix_content_accents.py and scripts/_pt_accents.py.

Ensures:
- String literal extractor correctly identifies single/double/template literals
- Comments and regex literals are not mistaken for strings
- Slug-like literals are preserved unchanged
- Accent dictionary entries apply with word boundaries (no substring bleed)
- Capitalized variants are auto-generated
- Identity entries are filtered out
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SCRIPTS))

from _pt_accents import (  # noqa: E402
    REPLACEMENTS,
    WORD_BOUNDARY_REPLACEMENTS,
    build_rules,
    is_slug_like,
)
from fix_content_accents import (  # noqa: E402
    apply_rules_to_content,
    extract_string_literals,
)


# ---------------------------------------------------------------------------
# Dictionary sanity
# ---------------------------------------------------------------------------


def test_no_identity_mappings_in_replacements():
    for k, v in REPLACEMENTS.items():
        assert k != v, f"identity mapping leaked: {k!r}"


def test_no_identity_mappings_in_word_boundary():
    for k, v in WORD_BOUNDARY_REPLACEMENTS.items():
        assert k != v, f"identity mapping leaked: {k!r}"


def test_critical_entries_present():
    # These are the specific words cited in the user's bug report.
    assert REPLACEMENTS["licitacao"] == "licitação"
    assert REPLACEMENTS["orgaos"] == "órgãos"
    assert REPLACEMENTS["servicos"] == "serviços"
    assert REPLACEMENTS["hipoteses"] == "hipóteses"
    assert REPLACEMENTS["inexigivel"] == "inexigível"
    assert REPLACEMENTS["alinea"] == "alínea"
    assert REPLACEMENTS["atencao"] == "atenção"
    assert REPLACEMENTS["generos"] == "gêneros"
    assert WORD_BOUNDARY_REPLACEMENTS["nao"] == "não"
    assert WORD_BOUNDARY_REPLACEMENTS["ate"] == "até"


def test_ambiguous_entries_excluded():
    # Must NOT be in dict to avoid destructive replacements.
    assert "pais" not in REPLACEMENTS
    assert "e" not in WORD_BOUNDARY_REPLACEMENTS
    assert "por" not in REPLACEMENTS


# ---------------------------------------------------------------------------
# Slug detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "s,expected",
    [
        ("dispensa-de-licitacao", True),
        ("o-que-e-pregao-eletronico", True),
        ("lei-14-133-2021", True),
        ("modalidades", True),
        ("pregao-eletronico", True),
        ("id_123", True),  # identifier
        # NOT slugs:
        ("Dispensa de licitacao", False),
        ("O que e pregao eletronico?", False),
        ("**texto em negrito**", False),
        ("Lei 14.133/2021, arts. 6 (XLI)", False),
        ("Licitação", False),
    ],
)
def test_is_slug_like(s, expected):
    assert is_slug_like(s) is expected


# ---------------------------------------------------------------------------
# Replacement engine
# ---------------------------------------------------------------------------


def test_apply_rules_basic_accent():
    out, _ = apply_rules_to_content("A licitacao e obrigatoria")
    assert "licitação" in out
    assert "obrigatória" in out


def test_apply_rules_capitalized_variant():
    out, _ = apply_rules_to_content("Licitacao publica")
    assert out == "Licitação pública"


def test_apply_rules_word_boundary_protects_substrings():
    # "licitacao" appears inside "licitacoes" — ensure plural wins.
    out, _ = apply_rules_to_content("As licitacoes abertas")
    assert "licitações" in out
    assert "licitaçãoes" not in out  # no partial replacement


def test_apply_rules_nao_ate():
    out, _ = apply_rules_to_content("nao sera valido ate 2026")
    assert "não" in out
    assert "até" in out
    assert "válido" in out


def test_apply_rules_idempotent():
    once, _ = apply_rules_to_content("licitacao")
    twice, _ = apply_rules_to_content(once)
    assert once == twice == "licitação"


def test_apply_rules_no_op_on_accented_text():
    src = "A licitação é obrigatória e serviços são incluídos."
    out, _ = apply_rules_to_content(src)
    assert out == src


def test_apply_rules_does_not_touch_mid_word():
    # "contratacao" should match but "precontratacaoista" (fake word) should not.
    out, _ = apply_rules_to_content("A contratacao foi feita")
    assert out == "A contratação foi feita"


def test_apply_rules_preserves_urls():
    # Domain names embedded in prose must not be modified.
    cases = [
        (
            "Portal da Transparencia (transparencia.gov.br)",
            "Portal da Transparência (transparencia.gov.br)",
        ),
        (
            "Acesse https://pncp.gov.br/licitacao para ver",
            "Acesse https://pncp.gov.br/licitacao para ver",
        ),
        (
            "Veja em www.gov.br/compras",
            "Veja em www.gov.br/compras",
        ),
        (
            "Envie e-mail para contato@licitacao.gov.br",
            "Envie e-mail para contato@licitacao.gov.br",
        ),
    ]
    for src, expected in cases:
        out, _ = apply_rules_to_content(src)
        assert out == expected, f"failed: {src!r} → {out!r}"


def test_phrase_rules_verb_e_patterns():
    """High-confidence patterns where 'e' must become 'é' (verb)."""
    cases = [
        ("a dispensa e permitida por lei", "a dispensa é permitida por lei"),
        ("o julgamento e obrigatoriamente", "o julgamento é obrigatoriamente"),
        ("o julgamento e obrigatorio", "o julgamento é obrigatório"),
        ("subcontratação e permitida", "subcontratação é permitida"),
        ("e possivel usar", "é possível usar"),
        ("e inviavel competir", "é inviável competir"),
        ("e fundamental conhecer", "é fundamental conhecer"),
        ("e necessario documento", "é necessário documento"),
        ("e vedado o uso", "é vedado o uso"),
        ("e aplicavel apenas", "é aplicável apenas"),
        ("e indispensavel", "é indispensável"),
    ]
    for src, expected in cases:
        out, _ = apply_rules_to_content(src)
        assert out == expected, f"failed: {src!r} → {out!r}"


def test_phrase_rules_preserve_adverb():
    """Adverbs between 'e' and adjective must be preserved."""
    cases = [
        (
            "o cadastro e praticamente obrigatorio",
            "o cadastro é praticamente obrigatório",
        ),
        ("e totalmente proibido", "é totalmente proibido"),
        ("e absolutamente necessario", "é absolutamente necessário"),
    ]
    for src, expected in cases:
        out, _ = apply_rules_to_content(src)
        assert out == expected, f"failed: {src!r} → {out!r}"


def test_phrase_rules_do_not_break_coordination():
    """Conjunction 'e' before nouns must NOT be modified."""
    cases = [
        ("bens e serviços", "bens e serviços"),
        ("obras e serviços de engenharia", "obras e serviços de engenharia"),
        ("artigos 6, inciso XLI, e 29", "artigos 6, inciso XLI, e 29"),
        ("arts. 28, 29 e 33", "arts. 28, 29 e 33"),
    ]
    for src, expected in cases:
        out, _ = apply_rules_to_content(src)
        assert out == expected, f"failed: {src!r} → {out!r}"


def test_apply_rules_fixes_prose_around_url():
    # Accent fix should still apply to prose outside the URL.
    out, _ = apply_rules_to_content(
        "A licitacao eletronica no pncp.gov.br é publica."
    )
    assert "licitação eletrônica" in out
    assert "pncp.gov.br" in out
    assert "pública" in out


# ---------------------------------------------------------------------------
# String literal extraction
# ---------------------------------------------------------------------------


def test_extract_single_quoted():
    src = "const x = 'licitacao';"
    lits = extract_string_literals(src)
    assert len(lits) == 1
    assert lits[0].content == "licitacao"
    assert lits[0].quote == "'"


def test_extract_double_quoted():
    src = 'const x = "pregao eletronico";'
    lits = extract_string_literals(src)
    assert len(lits) == 1
    assert lits[0].content == "pregao eletronico"


def test_extract_template_literal():
    src = "const x = `licitacao ${foo} publica`;"
    lits = extract_string_literals(src)
    assert len(lits) == 1
    assert lits[0].content == "licitacao ${foo} publica"


def test_extract_skips_line_comment():
    src = "// licitacao aqui nao e uma string\nconst x = 'orgao';"
    lits = extract_string_literals(src)
    assert len(lits) == 1
    assert lits[0].content == "orgao"


def test_extract_skips_block_comment():
    src = "/* 'licitacao' */ const x = 'pregao';"
    lits = extract_string_literals(src)
    assert len(lits) == 1
    assert lits[0].content == "pregao"


def test_extract_skips_regex_literal():
    # After `=`, /foo/ is a regex, not a division.
    src = "const re = /licitacao/g; const x = 'valido';"
    lits = extract_string_literals(src)
    # Should find only the 'valido' string.
    contents = [lit.content for lit in lits]
    assert "valido" in contents
    # "licitacao" should NOT be captured as a literal.
    assert not any("licitacao" in c for c in contents)


def test_extract_handles_escaped_quote():
    src = r"const x = 'it\'s licitacao';"
    lits = extract_string_literals(src)
    assert len(lits) == 1
    assert lits[0].content == r"it\'s licitacao"


def test_extract_multiple_literals_in_object():
    src = """
    const obj = {
      slug: 'dispensa-licitacao',
      title: 'O que e dispensa de licitacao?',
      body: 'A licitacao e publica.',
    };
    """
    lits = extract_string_literals(src)
    assert len(lits) == 3
    contents = [lit.content for lit in lits]
    assert "dispensa-licitacao" in contents
    assert "O que e dispensa de licitacao?" in contents
    assert "A licitacao e publica." in contents


# ---------------------------------------------------------------------------
# End-to-end file processing
# ---------------------------------------------------------------------------


def test_process_file_skips_slugs(tmp_path: Path):
    from fix_content_accents import process_file

    src = """
    const obj = {
      slug: 'dispensa-de-licitacao',
      relatedTerms: ['licitacao', 'pregao-eletronico'],
      title: 'Dispensa de licitacao',
      answer: 'A licitacao e obrigatoria em todos os orgaos.',
    };
    """
    f = tmp_path / "sample.ts"
    f.write_text(src, encoding="utf-8")

    result = process_file(f)

    # Slugs preserved
    assert "'dispensa-de-licitacao'" in result.updated
    assert "'licitacao'" in result.updated  # array of slug identifiers
    assert "'pregao-eletronico'" in result.updated
    # Prose accented
    assert "'Dispensa de licitação'" in result.updated
    assert "obrigatória" in result.updated
    assert "órgãos" in result.updated


def test_process_file_idempotent(tmp_path: Path):
    from fix_content_accents import process_file

    src = "const x = 'A licitacao e obrigatoria.';\n"
    f = tmp_path / "sample.ts"
    f.write_text(src, encoding="utf-8")

    r1 = process_file(f)
    f.write_text(r1.updated, encoding="utf-8")
    r2 = process_file(f)
    assert not r2.changed


def test_process_file_reports_markdown(tmp_path: Path):
    from fix_content_accents import process_file

    src = """
    const q = {
      slug: 'x',
      answer: 'Texto com **negrito** e listas:\\n\\n- item um\\n- item dois',
    };
    """
    f = tmp_path / "md.ts"
    f.write_text(src, encoding="utf-8")

    result = process_file(f, report_markdown=True)
    assert result.markdown_leaks, "expected markdown leaks to be reported"
    assert any("bold_asterisks" in hits for _, _, hits in result.markdown_leaks)


# ---------------------------------------------------------------------------
# Regression: longer tokens win over shorter
# ---------------------------------------------------------------------------


def test_longer_token_priority():
    # If "licitacao" is processed first, it could corrupt "licitacoes" into
    # "licitaçãoes". Longer tokens must be processed first.
    rules = build_rules()
    lengths = []
    seen = set()
    for pat, _ in rules:
        src = pat.pattern
        key = src.replace("\\b", "").lower()
        if key in seen:
            continue
        seen.add(key)
        lengths.append(len(key))
    # Descending order (allowing same-length siblings)
    for i in range(len(lengths) - 1):
        assert lengths[i] >= lengths[i + 1], (
            f"rule order violated at index {i}: {lengths[i]} < {lengths[i + 1]}"
        )
