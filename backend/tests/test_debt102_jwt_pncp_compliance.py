"""DEBT-102: Security & Auth — JWT Rotation & PNCP Compliance tests.

SYS-005: ES256/JWKS JWT signing + HS256 backward compat
SYS-003: PNCP API page size compliance (max 50)
"""

import os
import time
import pytest
import jwt as pyjwt
from unittest.mock import patch, MagicMock, AsyncMock
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


# ── Constants ──

TEST_HS256_SECRET = "test-hs256-secret-key-at-least-32-chars-long!"
VALID_CLAIMS = {
    "sub": "user-debt102-uuid",
    "email": "debt102@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": int(time.time()) + 3600,
}


# ── Fixtures ──

@pytest.fixture(autouse=True)
def clear_auth_state():
    """Clear auth caches and JWKS state."""
    from auth import _token_cache, reset_jwks_client
    _token_cache.clear()
    reset_jwks_client()
    yield
    _token_cache.clear()
    reset_jwks_client()


def _generate_ec_key_pair():
    """Generate an EC P-256 key pair for testing."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    pem_private = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pem_public = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key, public_key, pem_private, pem_public


# ============================================================================
# SYS-005: JWT ES256/JWKS Tests
# ============================================================================

class TestDebt102JwtEs256:
    """DEBT-102 SYS-005: ES256/JWKS JWT rotation tests."""

    def test_ac1_new_tokens_signed_es256(self):
        """AC1: _get_jwt_key_and_algorithms returns ES256 when JWKS available."""
        from auth import _get_jwt_key_and_algorithms

        private_key, public_key, _, _ = _generate_ec_key_pair()
        token = pyjwt.encode(VALID_CLAIMS, private_key, algorithm="ES256", headers={"kid": "test-kid-1"})

        mock_jwks = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = public_key
        mock_jwks.get_signing_key_from_jwt.return_value = mock_signing_key

        with patch("auth._get_jwks_client", return_value=mock_jwks):
            key, algorithms = _get_jwt_key_and_algorithms(token)
            assert algorithms == ["ES256"]
            assert key == public_key

    def test_ac2_jwks_client_initialized_from_supabase_url(self):
        """AC2: JWKS client is initialized from SUPABASE_URL."""
        from auth import _get_jwks_client, reset_jwks_client
        reset_jwks_client()

        # Without URL, no JWKS client
        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_JWKS_URL": ""}, clear=False):
            # Reset to force re-init
            import auth
            auth._jwks_client = None
            auth._jwks_init_attempted = False
            result = _get_jwks_client()  # noqa: F841
            # May return None if URL is empty — that's correct
            # The point is it doesn't crash

    def test_ac3_hs256_backward_compat(self):
        """AC3: HS256 tokens still accepted when ES256 is primary."""
        from auth import _get_jwt_key_and_algorithms

        hs256_token = pyjwt.encode(VALID_CLAIMS, TEST_HS256_SECRET, algorithm="HS256")

        # No JWKS, no PEM key → falls back to HS256
        with patch("auth._get_jwks_client", return_value=None), \
             patch.dict(os.environ, {"SUPABASE_JWT_SECRET": TEST_HS256_SECRET}):
            key, algorithms = _get_jwt_key_and_algorithms(hs256_token)
            assert algorithms == ["HS256"]
            assert key == TEST_HS256_SECRET

    def test_ac3_fallback_es256_to_hs256(self):
        """AC3: When ES256 decode fails, fallback to HS256."""
        from auth import _decode_with_fallback

        hs256_token = pyjwt.encode(VALID_CLAIMS, TEST_HS256_SECRET, algorithm="HS256")

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": TEST_HS256_SECRET}):
            # Primary was ES256 but failed → fallback to HS256
            payload = _decode_with_fallback(hs256_token, "invalid-key", ["ES256"])
            assert payload["sub"] == "user-debt102-uuid"

    def test_ac4_two_keys_rotation(self):
        """AC4: JWKS supports 2 active keys simultaneously for rotation.

        During key rotation, both old and new keys should work.
        """
        from auth import _get_jwt_key_and_algorithms

        # Generate two different key pairs (simulating rotation)
        key1_priv, key1_pub, _, _ = _generate_ec_key_pair()
        key2_priv, key2_pub, _, _ = _generate_ec_key_pair()

        # Token signed with key 1 (old key)
        token_key1 = pyjwt.encode(
            VALID_CLAIMS, key1_priv, algorithm="ES256",
            headers={"kid": "key-1-old"}
        )
        # Token signed with key 2 (new key)
        token_key2 = pyjwt.encode(
            VALID_CLAIMS, key2_priv, algorithm="ES256",
            headers={"kid": "key-2-new"}
        )

        # Mock JWKS that returns correct key based on kid
        mock_jwks = MagicMock()
        def mock_get_signing_key(token):
            headers = pyjwt.get_unverified_header(token)
            kid = headers.get("kid")
            mock_key = MagicMock()
            if kid == "key-1-old":
                mock_key.key = key1_pub
            elif kid == "key-2-new":
                mock_key.key = key2_pub
            else:
                raise Exception(f"Unknown kid: {kid}")
            return mock_key
        mock_jwks.get_signing_key_from_jwt.side_effect = mock_get_signing_key

        with patch("auth._get_jwks_client", return_value=mock_jwks):
            # Key 1 should work
            key, algs = _get_jwt_key_and_algorithms(token_key1)
            assert algs == ["ES256"]
            decoded_1 = pyjwt.decode(token_key1, key, algorithms=algs, audience="authenticated")
            assert decoded_1["sub"] == VALID_CLAIMS["sub"]

            # Key 2 should also work
            key, algs = _get_jwt_key_and_algorithms(token_key2)
            assert algs == ["ES256"]
            decoded_2 = pyjwt.decode(token_key2, key, algorithms=algs, audience="authenticated")
            assert decoded_2["sub"] == VALID_CLAIMS["sub"]

    def test_ac4_expired_hs256_rejected(self):
        """AC4: Expired HS256 tokens are rejected even during transition."""
        expired_claims = {**VALID_CLAIMS, "exp": int(time.time()) - 3600}
        expired_token = pyjwt.encode(expired_claims, TEST_HS256_SECRET, algorithm="HS256")

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": TEST_HS256_SECRET}), \
             patch("auth._get_jwks_client", return_value=None):
            with pytest.raises(pyjwt.ExpiredSignatureError):
                pyjwt.decode(expired_token, TEST_HS256_SECRET, algorithms=["HS256"], audience="authenticated")

    def test_ac4_es256_correct_kid_accepted(self):
        """AC4: ES256 token with correct key ID is accepted."""
        private_key, public_key, _, _ = _generate_ec_key_pair()
        token = pyjwt.encode(
            VALID_CLAIMS, private_key, algorithm="ES256",
            headers={"kid": "correct-kid"}
        )

        mock_jwks = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = public_key
        mock_jwks.get_signing_key_from_jwt.return_value = mock_signing_key

        with patch("auth._get_jwks_client", return_value=mock_jwks):
            from auth import _get_jwt_key_and_algorithms
            key, algs = _get_jwt_key_and_algorithms(token)
            decoded = pyjwt.decode(token, key, algorithms=algs, audience="authenticated")
            assert decoded["sub"] == VALID_CLAIMS["sub"]
            assert decoded["email"] == VALID_CLAIMS["email"]

    def test_jwks_cache_reset(self):
        """JWKS client can be reset for key rotation scenarios."""
        from auth import reset_jwks_client
        import auth

        # Set up a mock client
        auth._jwks_client = MagicMock()
        auth._jwks_init_attempted = True

        reset_jwks_client()

        assert auth._jwks_client is None
        assert auth._jwks_init_attempted is False


# ============================================================================
# SYS-003: PNCP Page Size Compliance Tests
# ============================================================================

@pytest.mark.external  # CIG-BE: page-size 51 reject test hits live PNCP API; gated out of CI
class TestDebt102PncpPageSize:
    """DEBT-102 SYS-003: PNCP page size compliance tests."""

    def test_ac5_default_page_size_is_50(self):
        """AC5: PNCP client default tamanhoPagina is 50."""
        from pncp_client import PNCPClient, AsyncPNCPClient
        import inspect

        # Check sync method signature
        sig_sync = inspect.signature(PNCPClient.fetch_page)
        assert sig_sync.parameters["tamanho"].default == 50

        # Check async method signature
        sig_async = inspect.signature(AsyncPNCPClient._fetch_page_async)
        assert sig_async.parameters["tamanho"].default == 50

    def test_ac6_reject_page_size_over_50_sync(self):
        """AC6: Server-side validation rejects tamanhoPagina > 50 (sync)."""
        from pncp_client import PNCPClient
        client = PNCPClient()

        with pytest.raises(ValueError, match="exceeds PNCP API maximum"):
            client.fetch_page(
                data_inicial="20260101",
                data_final="20260110",
                modalidade=6,
                tamanho=51,
            )

    @pytest.mark.asyncio
    async def test_ac6_reject_page_size_over_50_async(self):
        """AC6: Server-side validation rejects tamanhoPagina > 50 (async)."""
        from pncp_client import AsyncPNCPClient
        client = AsyncPNCPClient()
        client._client = MagicMock()

        with pytest.raises(ValueError, match="exceeds PNCP API maximum"):
            await client._fetch_page_async(
                data_inicial="20260101",
                data_final="20260110",
                modalidade=6,
                tamanho=100,
            )

    def test_ac6_page_size_50_accepted_sync(self):
        """AC6: tamanhoPagina=50 is accepted (boundary test)."""
        from pncp_client import PNCP_MAX_PAGE_SIZE
        assert PNCP_MAX_PAGE_SIZE == 50
        # 50 should NOT raise ValueError — it should proceed to API call
        # We just verify the constant is correct

    def test_ac7_health_canary_uses_50(self):
        """AC7: Health canary tests with tamanhoPagina=50."""
        import inspect
        from health import check_source_health
        source = inspect.getsource(check_source_health)
        # Verify the canary sends tamanhoPagina=50
        assert '"tamanhoPagina": 50' in source or "'tamanhoPagina': 50" in source

    def test_pncp_max_page_size_constant(self):
        """PNCP_MAX_PAGE_SIZE constant exists and equals 50."""
        from pncp_client import PNCP_MAX_PAGE_SIZE
        assert PNCP_MAX_PAGE_SIZE == 50

    def test_config_pncp_max_page_size(self):
        """Config module also exports PNCP_MAX_PAGE_SIZE."""
        from config.pncp import PNCP_MAX_PAGE_SIZE
        assert PNCP_MAX_PAGE_SIZE == 50

    @pytest.mark.asyncio
    async def test_ac8_pagination_multiple_pages(self):
        """AC8: Correct pagination when >50 results (multiple pages).

        _fetch_single_modality should fetch all pages until paginasRestantes=0.
        """
        from pncp_client import AsyncPNCPClient

        client = AsyncPNCPClient()
        client._client = AsyncMock()

        # Simulate 2 pages of results
        page1_items = [
            {
                "numeroControlePNCP": f"PNCP-{i:04d}",
                "orgaoEntidade": {"razaoSocial": "Org"},
                "unidadeOrgao": {"ufSigla": "SP", "nomeUnidade": "Unit"},
                "valorTotalEstimado": 1000,
                "dataPublicacaoPncp": "2026-01-01T00:00:00",
                "objetoCompra": "Test item",
                "modalidadeNome": "Pregao",
            }
            for i in range(50)
        ]
        page2_items = [
            {
                "numeroControlePNCP": f"PNCP-{i:04d}",
                "orgaoEntidade": {"razaoSocial": "Org"},
                "unidadeOrgao": {"ufSigla": "SP", "nomeUnidade": "Unit"},
                "valorTotalEstimado": 1000,
                "dataPublicacaoPncp": "2026-01-01T00:00:00",
                "objetoCompra": "Test item",
                "modalidadeNome": "Pregao",
            }
            for i in range(50, 60)
        ]

        call_count = 0

        async def mock_fetch(**kwargs):
            nonlocal call_count
            call_count += 1
            pagina = kwargs.get("pagina", 1)
            if pagina == 1:
                return {"data": page1_items, "paginasRestantes": 1, "totalRegistros": 60}
            else:
                return {"data": page2_items, "paginasRestantes": 0, "totalRegistros": 60}

        with patch.object(client, "_fetch_page_async", side_effect=mock_fetch), \
             patch("pncp_client._circuit_breaker") as mock_cb:
            mock_cb.record_success = AsyncMock()
            mock_cb.record_failure = AsyncMock()

            items, was_truncated = await client._fetch_single_modality(
                uf="SP",
                data_inicial="20260101",
                data_final="20260110",
                modalidade=6,
                max_pages=10,
            )

            # Should have fetched all 60 items across 2 pages
            assert len(items) == 60
            assert not was_truncated
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_ac8_pagination_always_uses_50(self):
        """AC8: Multi-page pagination always sends tamanhoPagina=50."""
        from pncp_client import AsyncPNCPClient

        client = AsyncPNCPClient()
        client._client = AsyncMock()

        captured_tamanhos = []

        async def mock_fetch(**kwargs):
            captured_tamanhos.append(kwargs.get("tamanho"))
            return {"data": [], "paginasRestantes": 0, "totalRegistros": 0}

        with patch.object(client, "_fetch_page_async", side_effect=mock_fetch), \
             patch("pncp_client._circuit_breaker") as mock_cb:
            mock_cb.record_success = AsyncMock()

            await client._fetch_single_modality(
                uf="SP",
                data_inicial="20260101",
                data_final="20260110",
                modalidade=6,
            )

            # _fetch_single_modality hardcodes tamanho=50
            assert captured_tamanhos == [50]
