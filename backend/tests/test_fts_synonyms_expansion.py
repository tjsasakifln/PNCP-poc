"""STORY-5.4 (TD-SYS-015): synonym expansion tests for datalake_query.

Validates that `_keyword_to_tstoken` expands single-word lexemes using
`data.fts_synonyms.SYNONYMS`, preserves phrase semantics for multi-word
keywords, and stays correctness-safe when a term has no entry in the map.
"""

from data.fts_synonyms import SYNONYMS, expand_term
from datalake_query import _build_tsquery, _keyword_to_tstoken


def test_unknown_term_returns_itself():
    assert expand_term("xyz_does_not_exist") == ("xyz_does_not_exist",)


def test_known_term_is_first_in_expansion():
    result = expand_term("pregao")
    assert result[0] == "pregao"
    assert "pregão" in result


def test_expand_term_dedupes():
    # expand_term dedupes while preserving order (term first, then new synonyms)
    result = expand_term("pregao")
    assert len(result) == len(set(result))


def test_tstoken_single_word_no_synonym_passes_through():
    assert _keyword_to_tstoken("xyz") == "xyz"


def test_tstoken_single_word_with_synonym_is_parenthesized_or():
    token = _keyword_to_tstoken("pregao")
    assert token.startswith("(") and token.endswith(")")
    assert "|" in token
    assert "pregao" in token
    assert "pregão" in token


def test_tstoken_multiword_keeps_phrase_semantics():
    # Phrase queries use <-> operator; synonyms NOT applied for phrases.
    assert _keyword_to_tstoken("pré moldado") == "pré<->moldado"


def test_build_tsquery_or_joins_multiple_keywords_with_synonym_expansion():
    tsquery, websearch = _build_tsquery(["pregao", "construcao"], None)
    assert websearch is None
    assert tsquery is not None
    assert "|" in tsquery
    # Each keyword expansion is parenthesized, so we expect (pregao | ...)
    # somewhere in the output.
    assert "pregão" in tsquery or "pregao" in tsquery


def test_build_tsquery_custom_terms_not_expanded():
    # custom_terms go through websearch_to_tsquery unchanged — no Python expansion.
    tsquery, websearch = _build_tsquery(None, ['"limpeza hospitalar"'])
    assert tsquery is None
    assert websearch == '"limpeza hospitalar"'


def test_synonym_map_has_canonical_modalidade_coverage():
    # Smoke: the map should cover the 4 biggest modalidade confusers.
    for canonical in ("pregao", "pregão", "concorrencia", "concorrência"):
        assert canonical in SYNONYMS
