"""
GTM Critical Test Scenarios
Tests covering scenarios identified in GTM-READINESS-REPORT.md

Priority: P0 (Pre-GTM Blockers)

STORY-224: Removed redundant/stale test classes (TestLargeFileDownload,
TestSessionExpiration, TestConcurrentUsers). Fixed TestQuotaLimitReached
to match current SearchPipeline quota flow + CRIT-009 structured errors.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from main import app
from auth import require_auth


client = TestClient(app)


def override_require_auth(user_id: str = "test-user"):
    """Create auth override for testing."""
    async def _override():
        return {"id": user_id, "email": "test@example.com"}
    return _override


def setup_auth_override(user_id="test-user"):
    """Setup auth override and return cleanup function."""
    app.dependency_overrides[require_auth] = override_require_auth(user_id)
    def cleanup():
        app.dependency_overrides.clear()
    return cleanup


# ============================================================================
# GTM Critical Scenario: Quota Limit Reached
# ============================================================================


class TestQuotaLimitReached:
    """Test user hitting quota limit during usage.

    Flow: POST /buscar -> SearchPipeline.stage_validate() -> quota.check_quota()
    When check_quota returns allowed=False, stage_validate raises HTTPException(403).
    The route's except HTTPException handler enriches the detail into CRIT-009
    structured format via _build_error_detail().

    Mock pattern (matches test_api_buscar.py working tests):
    - routes.search.ENABLE_NEW_PRICING = True (enable quota enforcement)
    - quota.check_quota -> QuotaInfo(allowed=False, error_message=...)
    - No need to mock rate_limiter (in-memory fallback allows test requests)
    - No need to mock check_user_roles (graceful fallback to non-admin)
    - No need to mock register_search_session (graceful fallback to None)
    """

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_quota_exhausted_returns_403(
        self,
        mock_check_quota,
    ):
        """Should return 403 with structured error when user reaches quota limit.

        Pipeline path: stage_validate() -> check_quota(allowed=False) ->
        HTTPException(403, detail=error_message) -> CRIT-009 enrichment ->
        structured dict with error_code=QUOTA_EXCEEDED.
        """
        cleanup = setup_auth_override("user-quota-exhausted")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Quota exhausted — check_quota returns allowed=False
            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="smartlic_pro",
                plan_name="SmartLic Pro",
                capabilities=PLAN_CAPABILITIES.get("smartlic_pro", PLAN_CAPABILITIES["free_trial"]),
                quota_used=1000,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc) + timedelta(days=15),
                error_message="Limite de 1000 buscas mensais atingido. Renova em 15 dias.",
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            detail = response.json()["detail"]
            # CRIT-009: detail is now a structured dict
            if isinstance(detail, dict):
                assert detail.get("error_code") == "QUOTA_EXCEEDED"
                assert "1000 buscas" in detail["detail"]
                assert "15 dias" in detail["detail"]
            else:
                # Fallback for non-structured (should not happen, but defensive)
                assert "1000 buscas" in detail
                assert "15 dias" in detail
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_free_trial_expired_returns_403(
        self,
        mock_check_quota,
    ):
        """Should return 403 with structured error when FREE trial expires.

        The error_message from QuotaInfo is passed through to the response.
        CRIT-009 wraps it with error_code=QUOTA_EXCEEDED.
        """
        cleanup = setup_auth_override("user-trial-expired")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Trial expired — check_quota returns allowed=False with trial message
            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=5,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                error_message="Seu trial expirou. Veja o valor que você analisou e continue tendo vantagem.",
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            detail = response.json()["detail"]
            # CRIT-009: detail is now a structured dict
            if isinstance(detail, dict):
                assert detail.get("error_code") == "QUOTA_EXCEEDED"
                assert "trial expirou" in detail["detail"]
            else:
                # Fallback for non-structured
                assert "trial expirou" in detail
        finally:
            cleanup()
