"""UX-427: Testes de coerência setor×resumo e unicidade de chave de cache.

AC5: Verifica que sector_name/termos_busca corretos são passados ao LLM
     (sem depender de call de rede — testa o pipeline de parâmetros).
AC6: Confirma que 3 setores distintos (vestuario, engenharia, saude)
     produzem chaves de cache diferentes, evitando colisão que causava
     o resumo errado.

Root cause (UX-427): _build_cache_params e _compute_cache_key omitiam
termos_busca, causando colisão entre buscas com termos diferentes mas
mesmo setor_id (ou setor_id=None).
"""

import hashlib
import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(
    ufs=None,
    setor_id=None,
    termos_busca=None,
    data_inicial="2026-01-01",
    data_final="2026-01-31",
    status=None,
    modalidades=None,
    modo_busca="publicacao",
):
    """Build a minimal BuscaRequest-like object for unit tests."""
    from schemas import BuscaRequest

    return BuscaRequest(
        ufs=ufs or ["SP"],
        setor_id=setor_id,
        termos_busca=termos_busca,
        data_inicial=data_inicial,
        data_final=data_final,
        modo_busca=modo_busca,
        modalidades=modalidades or [],
    )


# ---------------------------------------------------------------------------
# AC5: _build_cache_params includes termos_busca
# ---------------------------------------------------------------------------

class TestBuildCacheParamsIncludesTermos:
    """AC5: _build_cache_params must expose termos_busca so downstream
    compute_search_hash produces distinct keys per search terms."""

    def test_termos_busca_present_in_params(self):
        from pipeline.cache_manager import _build_cache_params

        req = _make_request(setor_id=None, termos_busca="levantamento topográfico")
        params = _build_cache_params(req)

        assert "termos_busca" in params
        assert params["termos_busca"] == "levantamento topográfico"

    def test_termos_busca_none_when_not_provided(self):
        from pipeline.cache_manager import _build_cache_params

        req = _make_request(setor_id="vestuario", termos_busca=None)
        params = _build_cache_params(req)

        assert "termos_busca" in params
        assert params["termos_busca"] is None

    def test_dates_present_in_params(self):
        from pipeline.cache_manager import _build_cache_params

        req = _make_request(data_inicial="2026-01-10", data_final="2026-01-20")
        params = _build_cache_params(req)

        assert params["data_inicial"] == "2026-01-10"
        assert params["data_final"] == "2026-01-20"

    def test_two_different_terms_produce_different_hash(self):
        """Key fix: same setor/UFs but different termos_busca → different hash."""
        from pipeline.cache_manager import _build_cache_params
        from cache.enums import compute_search_hash

        req_uniformes = _make_request(setor_id=None, termos_busca="uniforme escolar")
        req_engenharia = _make_request(setor_id=None, termos_busca="levantamento topográfico")

        hash1 = compute_search_hash(_build_cache_params(req_uniformes))
        hash2 = compute_search_hash(_build_cache_params(req_engenharia))

        assert hash1 != hash2, (
            "Searches with different termos_busca must produce different cache hashes "
            "(root cause of UX-427: wrong sector in AI summary)"
        )

    def test_same_terms_produce_same_hash(self):
        """Sanity: identical requests must still hit the same cache."""
        from pipeline.cache_manager import _build_cache_params
        from cache.enums import compute_search_hash

        req1 = _make_request(setor_id=None, termos_busca="drenagem pluvial")
        req2 = _make_request(setor_id=None, termos_busca="drenagem pluvial")

        assert compute_search_hash(_build_cache_params(req1)) == compute_search_hash(_build_cache_params(req2))


# ---------------------------------------------------------------------------
# AC6: 3 setores distintos → chaves de cache distintas (InMemory + Supabase)
# ---------------------------------------------------------------------------

class TestAC6ThreeSectorsDistinctKeys:
    """AC6: vestuario, engenharia, saude all produce distinct cache keys.

    Covers both InMemory key (_compute_cache_key) and Supabase key
    (_build_cache_params + compute_search_hash).
    """

    @pytest.mark.parametrize("setores", [
        ["vestuario", "engenharia", "saude"],
        ["informatica", "limpeza", "alimentos"],
    ])
    def test_sector_ids_produce_distinct_inmemory_keys(self, setores):
        from pipeline.cache_manager import _compute_cache_key

        keys = [_compute_cache_key(_make_request(setor_id=s)) for s in setores]
        assert len(keys) == len(set(keys)), (
            f"Sectors {setores} must produce distinct InMemory cache keys"
        )

    @pytest.mark.parametrize("setores", [
        ["vestuario", "engenharia", "saude"],
    ])
    def test_sector_ids_produce_distinct_supabase_hashes(self, setores):
        from pipeline.cache_manager import _build_cache_params
        from cache.enums import compute_search_hash

        hashes = [
            compute_search_hash(_build_cache_params(_make_request(setor_id=s)))
            for s in setores
        ]
        assert len(hashes) == len(set(hashes)), (
            f"Sectors {setores} must produce distinct Supabase cache hashes"
        )

    def test_sector_and_termos_busca_both_differentiate(self):
        """sector_id=vestuario vs sector_id=None + termos_busca='uniforme' → different keys."""
        from pipeline.cache_manager import _build_cache_params, _compute_cache_key
        from cache.enums import compute_search_hash

        req_setor = _make_request(setor_id="vestuario", termos_busca=None)
        req_termos = _make_request(setor_id=None, termos_busca="uniforme")

        assert _compute_cache_key(req_setor) != _compute_cache_key(req_termos)
        assert (
            compute_search_hash(_build_cache_params(req_setor))
            != compute_search_hash(_build_cache_params(req_termos))
        )


# ---------------------------------------------------------------------------
# InMemory per-UF key uniqueness
# ---------------------------------------------------------------------------

class TestInMemoryCacheKeyPerUF:
    """_compute_cache_key_per_uf must differentiate on termos_busca."""

    def test_different_terms_different_per_uf_key(self):
        from pipeline.cache_manager import _compute_cache_key_per_uf

        req_a = _make_request(setor_id=None, termos_busca="terraplenagem")
        req_b = _make_request(setor_id=None, termos_busca="uniformes escolares")

        key_a = _compute_cache_key_per_uf(req_a, "SP")
        key_b = _compute_cache_key_per_uf(req_b, "SP")

        assert key_a != key_b

    def test_same_terms_same_per_uf_key(self):
        from pipeline.cache_manager import _compute_cache_key_per_uf

        req1 = _make_request(setor_id="engenharia", termos_busca=None)
        req2 = _make_request(setor_id="engenharia", termos_busca=None)

        assert _compute_cache_key_per_uf(req1, "RS") == _compute_cache_key_per_uf(req2, "RS")


# ---------------------------------------------------------------------------
# LLM prompt robustness: gerar_resumo passes sector name in user prompt
# ---------------------------------------------------------------------------

class TestGerarResumoSectorInPrompt:
    """AC5 complement: gerar_resumo must include sector label in user prompt
    so the LLM anchors its summary even when called without cache-side fix."""

    def test_sector_name_in_user_prompt(self):
        """The user prompt sent to OpenAI must contain the sector name."""
        from llm import gerar_resumo

        captured_messages = []

        mock_choice = MagicMock()
        mock_choice.message.parsed = MagicMock(
            resumo_executivo="Resumo de engenharia",
            total_oportunidades=1,
            valor_total=100000.0,
            destaques=[],
            alerta_urgencia=None,
        )
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None

        def capture_call(**kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            return mock_response

        licitacoes = [
            {
                "objetoCompra": "Pavimentação e drenagem urbana",
                "nomeOrgao": "Prefeitura SP",
                "uf": "SP",
                "municipio": "São Paulo",
                "valorTotalEstimado": 500000.0,
                "dataAberturaProposta": "2026-02-01",
            }
        ]

        with patch("llm.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.beta.chat.completions.parse.side_effect = capture_call

            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                gerar_resumo(
                    licitacoes,
                    sector_name="Engenharia, Projetos e Obras",
                    setor_id="engenharia",
                )

        assert captured_messages, "OpenAI must be called with messages"
        user_msg = next(
            (m["content"] for m in captured_messages if m["role"] == "user"), ""
        )
        assert "Engenharia" in user_msg or "engenharia" in user_msg.lower(), (
            f"User prompt must contain sector name 'Engenharia'. Got: {user_msg[:300]}"
        )

    def test_termos_busca_in_user_prompt(self):
        """When termos_busca is set, it must appear in the user prompt."""
        from llm import gerar_resumo

        captured_messages = []

        mock_choice = MagicMock()
        mock_choice.message.parsed = MagicMock(
            resumo_executivo="Resumo",
            total_oportunidades=1,
            valor_total=0.0,
            destaques=[],
            alerta_urgencia=None,
        )
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None

        def capture(**kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            return mock_response

        licitacoes = [
            {
                "objetoCompra": "Serviço de limpeza",
                "nomeOrgao": "Prefeitura RJ",
                "uf": "RJ",
                "municipio": "Rio de Janeiro",
                "valorTotalEstimado": 100000.0,
                "dataAberturaProposta": "2026-02-01",
            }
        ]

        with patch("llm.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.beta.chat.completions.parse.side_effect = capture

            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                gerar_resumo(
                    licitacoes,
                    sector_name="licitações",
                    termos_busca="limpeza urbana varrição",
                )

        user_msg = next(
            (m["content"] for m in captured_messages if m["role"] == "user"), ""
        )
        assert "limpeza urbana varrição" in user_msg, (
            f"User prompt must contain termos_busca. Got: {user_msg[:300]}"
        )


# ---------------------------------------------------------------------------
# Regression: gerar_resumo_fallback uses sector_name correctly
# ---------------------------------------------------------------------------

class TestGerarResumoFallbackSector:
    """AC5 regression: gerar_resumo_fallback must mention sector name in output."""

    def test_fallback_uses_sector_name(self):
        from llm import gerar_resumo_fallback

        licitacoes = [
            {
                "objetoCompra": "Obra de pavimentação",
                "nomeOrgao": "Prefeitura de Curitiba",
                "uf": "PR",
                "municipio": "Curitiba",
                "valorTotalEstimado": 200000.0,
                "dataAberturaProposta": "2026-03-01T10:00:00",
                "modalidade": "Tomada de Preços",
            }
        ]
        resumo = gerar_resumo_fallback(
            licitacoes,
            sector_name="Engenharia, Projetos e Obras",
        )

        # The insight_setorial field should reference the correct sector
        assert resumo is not None
        combined = " ".join([
            resumo.resumo_executivo or "",
            resumo.insight_setorial or "",
        ]).lower()
        assert "engenharia" in combined or "obras" in combined, (
            f"Fallback summary must reference the searched sector. Got: {combined[:400]}"
        )

    @pytest.mark.parametrize("sector_name,expected_keyword", [
        ("Vestuário e Uniformes", "vestuário"),
        ("Engenharia, Projetos e Obras", "engenharia"),
        ("Saúde e Medicamentos", "saúde"),
    ])
    def test_fallback_three_sectors_parametrized(self, sector_name, expected_keyword):
        """AC6: test with 3 distinct sectors — fallback summary must reference correct sector."""
        from llm import gerar_resumo_fallback

        licitacoes = [
            {
                "objetoCompra": f"Licitação de {sector_name}",
                "nomeOrgao": "Órgão Público",
                "uf": "SP",
                "municipio": "São Paulo",
                "valorTotalEstimado": 100000.0,
                "dataAberturaProposta": "2026-03-01T10:00:00",
                "modalidade": "Pregão Eletrônico",
            }
        ]
        resumo = gerar_resumo_fallback(
            licitacoes,
            sector_name=sector_name,
        )

        combined = " ".join([
            resumo.resumo_executivo or "",
            resumo.insight_setorial or "",
        ]).lower()

        assert expected_keyword.lower() in combined, (
            f"[AC6] Fallback for sector '{sector_name}' must mention '{expected_keyword}'. "
            f"Got: {combined[:300]}"
        )
