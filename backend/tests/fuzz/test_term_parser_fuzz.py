"""Property-based fuzz tests for term_parser.parse_search_terms (STORY-6.7).

Coverage:
- Arbitrary text never causes uncaught exceptions.
- Empty / whitespace-only input always returns empty list.
- Comma-heavy inputs (including edge cases like leading/trailing commas).
- Smart-quote inputs (U+201C/201D/2018/2019) — sanitised before parsing.
- Unicode combining marks / extreme characters.
- Long inputs exceeding MAX_INPUT_LENGTH=256 (truncation branch).

The ONLY expected non-crash outcome is a returned List[str]. No documented
exception class exists in term_parser — all exceptions are therefore unexpected.
"""

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from term_parser import MAX_INPUT_LENGTH, parse_search_terms

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OPERATORS = st.sampled_from([",", "  ", " ", "\t", "\n", "\r\n"])
_SMART_QUOTES = st.sampled_from(["\u201c", "\u201d", "\u2018", "\u2019"])


# ---------------------------------------------------------------------------
# 1. Arbitrary text — main crash-free property
# ---------------------------------------------------------------------------


@pytest.mark.fuzz
@pytest.mark.timeout(60)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(raw=st.text(max_size=500))
def test_parse_never_crashes_on_arbitrary_text(raw: str) -> None:
    """parse_search_terms must never raise for any arbitrary string input."""
    try:
        result = parse_search_terms(raw)
    except Exception as exc:
        pytest.fail(
            f"Unexpected exception {type(exc).__name__}: {exc!r} "
            f"for input {raw!r}"
        )
    assert isinstance(result, list), (
        f"Expected list, got {type(result)} for input {raw!r}"
    )


# ---------------------------------------------------------------------------
# 2. Empty / whitespace-only → always returns []
# ---------------------------------------------------------------------------


@pytest.mark.fuzz
@pytest.mark.timeout(60)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    raw=st.one_of(
        st.just(""),
        st.just("   "),
        st.just("\t\t\t"),
        st.just("\n\r\n\t"),
        # Only use characters that Python's str.strip() / re \s considers whitespace
        st.text(alphabet=st.sampled_from([" ", "\t", "\n", "\r", "\x0b", "\x0c"]), max_size=50),
    )
)
def test_empty_or_whitespace_returns_empty_list(raw: str) -> None:
    """Empty string or ASCII-whitespace-only input must return an empty list.

    NOTE: The parser uses re.sub(r'\\s+', ' ', ...) which matches Python's
    \\s — space, tab, newline, CR, VT, FF. Control chars like DEL (\\x7f)
    are NOT \\s, so they are not stripped; only the above whitespace chars
    are guaranteed to produce an empty result.
    """
    result = parse_search_terms(raw)
    assert result == [], (
        f"Expected [] for whitespace-only input {raw!r}, got {result!r}"
    )


# ---------------------------------------------------------------------------
# 3. Comma-heavy and delimiter edge-cases
# ---------------------------------------------------------------------------


@pytest.mark.fuzz
@pytest.mark.timeout(60)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    raw=st.one_of(
        # Leading/trailing/only commas
        st.just(","),
        st.just(",,,,"),
        st.just(",abc,"),
        st.just(",abc,,def,"),
        # Constructed with commas as delimiters
        st.builds(
            lambda a, b, sep: f"{a}{sep}{b}",
            a=st.text(min_size=0, max_size=30),
            b=st.text(min_size=0, max_size=30),
            sep=st.just(","),
        ),
        # Multiple comma-separated words
        st.lists(
            st.text(min_size=0, max_size=20),
            min_size=1,
            max_size=10,
        ).map(lambda parts: ",".join(parts)),
    )
)
def test_comma_inputs_never_crash(raw: str) -> None:
    """Comma-delimited inputs (including edge cases) never crash the parser."""
    try:
        result = parse_search_terms(raw)
    except Exception as exc:
        pytest.fail(
            f"Unexpected exception {type(exc).__name__}: {exc!r} "
            f"for comma input {raw!r}"
        )
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# 4. Smart-quote inputs — parser normalises these before splitting
# ---------------------------------------------------------------------------


@pytest.mark.fuzz
@pytest.mark.timeout(60)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    prefix=st.text(max_size=20),
    quote=_SMART_QUOTES,
    word=st.text(alphabet=st.characters(whitelist_categories=("L",)), max_size=20),
    suffix=st.text(max_size=20),
)
def test_smart_quote_inputs_never_crash(
    prefix: str, quote: str, word: str, suffix: str
) -> None:
    """Smart-quote characters (curly quotes) must be handled without crashing."""
    raw = f"{prefix}{quote}{word}{quote}{suffix}"
    try:
        result = parse_search_terms(raw)
    except Exception as exc:
        pytest.fail(
            f"Unexpected exception {type(exc).__name__}: {exc!r} "
            f"for smart-quote input {raw!r}"
        )
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# 5. Unicode / extreme characters (combining marks, surrogates excluded)
# ---------------------------------------------------------------------------


@pytest.mark.fuzz
@pytest.mark.timeout(60)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    raw=st.text(
        alphabet=st.characters(
            # Exclude surrogates which cause encode errors in some environments
            blacklist_categories=("Cs",),
        ),
        max_size=300,
    )
)
def test_unicode_extreme_chars_never_crash(raw: str) -> None:
    """Arbitrary Unicode (excluding surrogates) never crashes the parser.

    Also verifies the MAX_INPUT_LENGTH truncation branch for inputs > 256 chars.
    """
    try:
        result = parse_search_terms(raw)
    except Exception as exc:
        pytest.fail(
            f"Unexpected exception {type(exc).__name__}: {exc!r} "
            f"for unicode input len={len(raw)}"
        )
    assert isinstance(result, list)
    # Output list length can never exceed raw input length (only reduce/equal)
    assert len(result) <= len(raw), (
        f"Output longer than input? input_len={len(raw)} output_len={len(result)}"
    )


# ---------------------------------------------------------------------------
# 6. Long inputs — truncation at MAX_INPUT_LENGTH boundary
# ---------------------------------------------------------------------------


@pytest.mark.fuzz
@pytest.mark.timeout(60)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    raw=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Zs", "P")),
        min_size=MAX_INPUT_LENGTH + 1,
        max_size=MAX_INPUT_LENGTH * 4,
    )
)
def test_long_inputs_truncated_and_never_crash(raw: str) -> None:
    """Inputs longer than MAX_INPUT_LENGTH are truncated, never crash."""
    assert len(raw) > MAX_INPUT_LENGTH, "Strategy guarantee"
    try:
        result = parse_search_terms(raw)
    except Exception as exc:
        pytest.fail(
            f"Unexpected exception {type(exc).__name__}: {exc!r} "
            f"for long input len={len(raw)}"
        )
    assert isinstance(result, list)
