"""
UX-403: Filtro de esfera — behavior aligned with current filter/core.py implementation.

Current behavior (as of filter refactoring):
- esferas=None or esferas=[] → filter skipped, all bids pass
- esferas=["F","E","M"] → filter IS applied (all-esferas no longer skips)
- Unknown esferas are rejected (no fail-open) unless keyword fallback matches
- Stats has "rejeitadas_esfera" but NOT "esfera_indeterminada"
"""

from filter import aplicar_todos_filtros


def _make_bid(esfera_id=None, nome_orgao=None, uf="SP"):
    """Create a minimal bid dict for testing."""
    bid = {
        "uf": uf,
        "dataPublicacao": "2026-03-01",
        "dataAbertura": "2026-03-15",
    }
    if esfera_id is not None:
        bid["esferaId"] = esfera_id
    if nome_orgao is not None:
        bid["nomeOrgao"] = nome_orgao
    return bid


class TestAC1AllEsferasSkipsFilter:
    """AC1: Esfera filter behavior when selecting all/none esferas."""

    def test_esferas_none_skips_filter(self):
        """esferas=None skips filter entirely — all bids pass esfera check."""
        bids = [
            _make_bid(esfera_id="F"),
            _make_bid(esfera_id="E"),
            _make_bid(esfera_id="M"),
            _make_bid(nome_orgao="Empresa desconhecida"),
        ]
        _, stats_none = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=None
        )
        assert stats_none["rejeitadas_esfera"] == 0

    def test_all_three_esferas_applies_filter(self):
        """esferas=["F","E","M"] applies the filter (does not skip).

        NOTE: Selecting all 3 esferas no longer skips the filter.
        Bids with known esferaId that match pass; others use keyword fallback.
        """
        bids = [
            _make_bid(esfera_id="F"),
            _make_bid(esfera_id="E"),
            _make_bid(esfera_id="M"),
        ]
        _, stats_all = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F", "E", "M"]
        )
        # All 3 have known esferaIds that match — no rejections
        assert stats_all["rejeitadas_esfera"] == 0

    def test_all_three_esferas_lowercase(self):
        """Lowercase ["f","e","m"] should also be handled."""
        bids = [
            _make_bid(esfera_id="F"),
            _make_bid(esfera_id="E"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["f", "e", "m"]
        )
        # Both bids have known esferaIds matching (case-insensitive)
        assert stats["rejeitadas_esfera"] == 0

    def test_all_three_esferas_mixed_case(self):
        """Mixed case ["F","e","M"] should also be handled."""
        bids = [
            _make_bid(esfera_id="E"),
            _make_bid(esfera_id="F"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F", "e", "M"]
        )
        assert stats["rejeitadas_esfera"] == 0

    def test_subset_still_applies_filter(self):
        """Subset like ["F","E"] should still apply the filter."""
        bids = [
            _make_bid(esfera_id="M"),
            _make_bid(esfera_id="F"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F", "E"]
        )
        # M bid has known esferaId="M" not in ["F","E"] -> rejected
        assert stats["rejeitadas_esfera"] == 1


class TestAC2FailOpenUndeterminedSphere:
    """AC2: Bids with undetermined sphere — current behavior (reject unless keyword match)."""

    def test_undetermined_esfera_no_keyword_match_rejected(self):
        """Bid without esferaId and without keyword match should be rejected."""
        bids = [
            _make_bid(esfera_id="F"),
            _make_bid(nome_orgao="Entidade XYZ"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F"]
        )
        # "Entidade XYZ" doesn't match any keyword -> rejected
        assert stats["rejeitadas_esfera"] == 1

    def test_known_esfera_passes_filter(self):
        """Bid with known esferaId that matches is accepted."""
        bid = _make_bid(esfera_id="F")
        bids = [bid]
        aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F"]
        )
        # esferaId="F" is in esferas=["F"] -> accepted, no mutation expected

    def test_keyword_match_passes_esfera_filter(self):
        """Bid matched by keyword fallback (e.g. 'ministerio') passes esfera filter."""
        # "Ministerio da Saude" matches keyword "ministerio" -> esfera F -> accepted
        bid = _make_bid(nome_orgao="Ministerio da Saude")
        bids = [bid]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F"]
        )
        assert stats["rejeitadas_esfera"] == 0

    def test_fail_open_does_not_increment_rejeitadas(self):
        """Municipal keyword match passes municipal filter."""
        bids = [
            _make_bid(nome_orgao="Prefeitura Municipal de Campinas"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["M"]
        )
        # "prefeitura" -> esfera M -> accepted
        assert stats["rejeitadas_esfera"] == 0

    def test_multiple_undetermined_bids(self):
        """Multiple bids with unmatched esferas are all rejected."""
        bids = [
            _make_bid(nome_orgao="Org A"),
            _make_bid(nome_orgao="Org B"),
            _make_bid(nome_orgao="Org C"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F"]
        )
        # None of these match "federal" keywords -> all rejected
        assert stats["rejeitadas_esfera"] == 3


class TestAC6EsferaIndeterminadaStats:
    """AC6: stats tracking for esfera filter — updated for current keys."""

    def test_rejeitadas_esfera_zero_when_all_match(self):
        """No rejections when all bids have matching known spheres."""
        bids = [
            _make_bid(esfera_id="F"),
            _make_bid(esfera_id="E"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F", "E"]
        )
        assert stats["rejeitadas_esfera"] == 0

    def test_indeterminada_count_incremented(self):
        """Unmatched bids increment rejeitadas_esfera."""
        bids = [
            _make_bid(esfera_id="F"),
            _make_bid(nome_orgao="Org A"),
            _make_bid(nome_orgao="Org B"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["F"]
        )
        # 2 bids have no matching esfera and no keyword match
        assert stats["rejeitadas_esfera"] == 2

    def test_rejeitadas_zero_when_filter_skipped(self):
        """When esferas=None (no filter), no esfera rejections."""
        bids = [
            _make_bid(nome_orgao="Unknown org"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=None
        )
        assert stats["rejeitadas_esfera"] == 0

    def test_rejeitadas_zero_when_none(self):
        """When esferas=None, no esfera rejections."""
        bids = [
            _make_bid(nome_orgao="Unknown org"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=None
        )
        assert stats["rejeitadas_esfera"] == 0

    def test_keyword_match_not_counted_as_rejected(self):
        """Bids matched by keyword fallback are NOT rejected."""
        bids = [
            _make_bid(nome_orgao="Prefeitura de Sao Paulo"),
        ]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}, esferas=["M"]
        )
        assert stats["rejeitadas_esfera"] == 0

    def test_stats_key_always_present(self):
        """rejeitadas_esfera key always present in stats dict."""
        bids = [_make_bid(esfera_id="F")]
        _, stats = aplicar_todos_filtros(
            bids, ufs_selecionadas={"SP"}
        )
        assert "rejeitadas_esfera" in stats
