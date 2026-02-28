"""
Tests for STORY-320: Trial Paywall (Paywall Suave Dia 7).

AC13: get_trial_phase() logic — day calculation, phase determination
AC14: _apply_trial_paywall() — result truncation and metadata
AC2:  trial-status endpoint — trial_phase and trial_day fields in response
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from main import app
from auth import require_auth
from database import get_db
from quota import (
    QuotaInfo,
    PLAN_CAPABILITIES,
    get_quota_reset_date,
    get_trial_phase,
    TrialPhaseInfo,
)
import schemas
from schemas import (
    BuscaResponse,
    ResumoEstrategico,
    LicitacaoItem,
)


# ============================================================================
# Shared fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def setup_auth_override():
    """Auth override shared by all test classes that use HTTP requests."""
    app.dependency_overrides[require_auth] = lambda: {
        "id": "test-user-story320",
        "email": "paywall@example.com",
    }
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db


def _make_quota_info(
    plan_id: str = "free_trial",
    trial_expires_at: datetime | None = None,
    quota_used: int = 0,
) -> QuotaInfo:
    """Helper: build a QuotaInfo with sensible defaults."""
    plan_caps = PLAN_CAPABILITIES.get(plan_id, PLAN_CAPABILITIES["free_trial"])
    return QuotaInfo(
        allowed=True,
        plan_id=plan_id,
        plan_name=plan_id,
        capabilities=plan_caps,
        quota_used=quota_used,
        quota_remaining=1000 - quota_used,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=trial_expires_at,
        error_message=None,
    )


def _make_licitacao(i: int) -> LicitacaoItem:
    """Helper: build a minimal LicitacaoItem for paywall tests."""
    return LicitacaoItem(
        pncp_id=f"PNCP-{i:05d}",
        objeto=f"Objeto licitacao {i}",
        orgao=f"Orgao {i}",
        uf="SP",
        valor=10000.0 * i,
        link=f"https://pncp.gov.br/item/{i}",
    )


def _make_busca_response(n_results: int) -> BuscaResponse:
    """Helper: build a BuscaResponse with n_results licitacoes."""
    licitacoes = [_make_licitacao(i) for i in range(1, n_results + 1)]
    resumo = ResumoEstrategico(
        resumo_executivo=f"Encontradas {n_results} licitacoes.",
        total_oportunidades=n_results,
        valor_total=float(n_results * 10000),
    )
    return BuscaResponse(
        resumo=resumo,
        licitacoes=licitacoes,
        excel_available=False,
        quota_used=1,
        quota_remaining=999,
        total_raw=n_results,
        total_filtrado=n_results,
        freshness="live",
    )


# ============================================================================
# AC13: TestGetTrialPhase
# ============================================================================


class TestGetTrialPhase:
    """Tests for get_trial_phase() in quota.py (STORY-320 AC13)."""

    def test_day_1_full_access(self):
        """Trial day 1 (expires_at = now + 13.5 days): phase=full_access, day=1.

        Formula: trial_start = expires_at - 14 days
                 elapsed = now - trial_start
                 current_day = elapsed.days + 1
        With expires_at = now + 13.5d: trial_start = now - 0.5d → elapsed.days=0 → day=1.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=13, hours=12)
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=expires_at)

        with patch("quota.check_quota", return_value=mock_quota):
            result = get_trial_phase("test-user-day1")

        assert result["phase"] == "full_access"
        assert result["day"] == 1

    def test_day_7_full_access(self):
        """Trial day 7 (expires_at = now + 7.5 days): phase=full_access (boundary — TRIAL_PAYWALL_DAY=7).

        elapsed.days = 6 → current_day = 7; paywall activates at day > 7.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=7, hours=12)
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=expires_at)

        with patch("quota.check_quota", return_value=mock_quota):
            result = get_trial_phase("test-user-day7")

        assert result["phase"] == "full_access"
        assert result["day"] == 7

    def test_day_8_limited_access(self):
        """Trial day 8 (expires_at = now + 6.5 days): phase=limited_access.

        elapsed.days = 7 → current_day = 8; 8 > TRIAL_PAYWALL_DAY(7) → limited.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=6, hours=12)
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=expires_at)

        with patch("quota.check_quota", return_value=mock_quota):
            result = get_trial_phase("test-user-day8")

        assert result["phase"] == "limited_access"
        assert result["day"] == 8

    def test_day_14_limited_access(self):
        """Trial day 14 (expires_at = now + 0.5 days): phase=limited_access.

        elapsed.days = 13 → current_day = 14; last day of 14-day trial.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=expires_at)

        with patch("quota.check_quota", return_value=mock_quota):
            result = get_trial_phase("test-user-day14")

        assert result["phase"] == "limited_access"
        assert result["day"] == 14

    def test_paid_user_not_trial(self):
        """Paid user (plan_id != free_trial): phase=not_trial."""
        mock_quota = _make_quota_info(plan_id="smartlic_pro", trial_expires_at=None)

        with patch("quota.check_quota", return_value=mock_quota):
            result = get_trial_phase("test-user-paid")

        assert result["phase"] == "not_trial"
        assert result["day"] == 0

    def test_feature_flag_disabled(self):
        """When TRIAL_PAYWALL_ENABLED=False, always returns full_access regardless of day."""
        # Even day 12 (limited_access territory) should return full_access
        expires_at = datetime.now(timezone.utc) + timedelta(days=2)
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=expires_at)

        with patch("quota.check_quota", return_value=mock_quota):
            with patch("config.TRIAL_PAYWALL_ENABLED", False):
                result = get_trial_phase("test-user-flag-off")

        assert result["phase"] == "full_access"
        assert result["day"] == 0
        assert result["days_remaining"] == 999

    def test_no_trial_expires_at(self):
        """Trial user with trial_expires_at=None: phase=full_access (no data → fail-open)."""
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=None)

        with patch("quota.check_quota", return_value=mock_quota):
            result = get_trial_phase("test-user-no-expiry")

        assert result["phase"] == "full_access"
        assert result["day"] == 0

    def test_quota_error_graceful(self):
        """When check_quota raises an exception, fail-open → full_access."""
        with patch("quota.check_quota", side_effect=Exception("DB unavailable")):
            result = get_trial_phase("test-user-quota-error")

        assert result["phase"] == "full_access"
        assert result["day"] == 0
        assert result["days_remaining"] == 999


# ============================================================================
# AC14: TestApplyTrialPaywall
# ============================================================================


class TestApplyTrialPaywall:
    """Tests for _apply_trial_paywall() in routes/search.py (STORY-320 AC14)."""

    def _call_paywall(self, response: BuscaResponse, user: dict, phase: str = "limited_access") -> BuscaResponse:
        """Helper: call _apply_trial_paywall with a given phase (flag always enabled).

        Both imports happen inside the function body, so we patch at the source modules:
          - get_feature_flag → config.get_feature_flag
          - get_trial_phase  → quota.get_trial_phase
        """
        from routes.search import _apply_trial_paywall

        phase_info = TrialPhaseInfo(phase=phase, day=8, days_remaining=6)
        with patch("quota.get_trial_phase", return_value=phase_info):
            with patch("config.get_feature_flag", return_value=True):
                return _apply_trial_paywall(response, user)

    def test_paywall_truncates_to_10(self):
        """25 results in limited_access → 10, paywall_applied=True, total_before_paywall=25."""
        response = _make_busca_response(25)
        user = {"id": "test-user-limited"}

        result = self._call_paywall(response, user, phase="limited_access")

        assert len(result.licitacoes) == 10
        assert result.paywall_applied is True
        assert result.total_before_paywall == 25

    def test_no_paywall_under_limit(self):
        """5 results in limited_access → 5, paywall_applied=False (under max)."""
        response = _make_busca_response(5)
        user = {"id": "test-user-under-limit"}

        result = self._call_paywall(response, user, phase="limited_access")

        assert len(result.licitacoes) == 5
        assert result.paywall_applied is False
        assert result.total_before_paywall is None

    def test_no_paywall_full_access(self):
        """Day 1 (full_access) → no truncation regardless of result count."""
        response = _make_busca_response(50)
        user = {"id": "test-user-full-access"}

        result = self._call_paywall(response, user, phase="full_access")

        assert len(result.licitacoes) == 50
        assert result.paywall_applied is False
        assert result.total_before_paywall is None

    def test_no_paywall_paid_user(self):
        """not_trial phase → no truncation."""
        response = _make_busca_response(100)
        user = {"id": "test-user-paid"}

        result = self._call_paywall(response, user, phase="not_trial")

        assert len(result.licitacoes) == 100
        assert result.paywall_applied is False

    def test_no_paywall_flag_disabled(self):
        """TRIAL_PAYWALL_ENABLED=False → no truncation even for limited_access users."""
        from routes.search import _apply_trial_paywall

        response = _make_busca_response(25)
        user = {"id": "test-user-flag-disabled"}

        # Patch get_feature_flag at source (config module) to return False
        with patch("config.get_feature_flag", return_value=False):
            result = _apply_trial_paywall(response, user)

        assert len(result.licitacoes) == 25
        assert result.paywall_applied is False

    def test_summary_count_updated(self):
        """resumo.total_oportunidades should be updated to TRIAL_PAYWALL_MAX_RESULTS after paywall."""
        response = _make_busca_response(25)
        assert response.resumo.total_oportunidades == 25
        user = {"id": "test-user-summary"}

        result = self._call_paywall(response, user, phase="limited_access")

        # Summary count must reflect visible results, not original count
        assert result.resumo.total_oportunidades == 10
        assert result.paywall_applied is True

    def test_paywall_exactly_at_limit(self):
        """Exactly 10 results in limited_access → no truncation (not over limit)."""
        response = _make_busca_response(10)
        user = {"id": "test-user-exact-limit"}

        result = self._call_paywall(response, user, phase="limited_access")

        assert len(result.licitacoes) == 10
        assert result.paywall_applied is False
        assert result.total_before_paywall is None

    def test_paywall_missing_user_id(self):
        """Missing user id → fail-open, no truncation."""
        from routes.search import _apply_trial_paywall

        response = _make_busca_response(25)
        user = {}  # no "id" key

        with patch("config.get_feature_flag", return_value=True):
            result = _apply_trial_paywall(response, user)

        assert len(result.licitacoes) == 25
        assert result.paywall_applied is False


# ============================================================================
# AC2: TestTrialStatusEndpoint
# ============================================================================


class TestTrialStatusEndpoint:
    """Tests for GET /v1/trial-status — trial_phase and trial_day fields (STORY-320 AC2)."""

    def test_trial_status_includes_phase(self, client, mock_db):
        """GET /v1/trial-status for day-8 trial user returns trial_phase='limited_access' and trial_day=8.

        expires_at = now + 6.5d → trial_start = now - 7.5d → elapsed.days=7 → day=8.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=6, hours=12)
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=expires_at)

        with patch("quota.check_quota", return_value=mock_quota):
            response = client.get("/v1/trial-status")

        assert response.status_code == 200
        data = response.json()

        assert "trial_phase" in data
        assert "trial_day" in data
        assert data["trial_phase"] == "limited_access"
        assert data["trial_day"] == 8

    def test_trial_status_full_access_phase(self, client, mock_db):
        """GET /v1/trial-status for day-2 trial user returns trial_phase='full_access'.

        expires_at = now + 12.5d → trial_start = now - 1.5d → elapsed.days=1 → day=2.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=12, hours=12)
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=expires_at)

        with patch("quota.check_quota", return_value=mock_quota):
            response = client.get("/v1/trial-status")

        assert response.status_code == 200
        data = response.json()

        assert data["trial_phase"] == "full_access"
        assert data["trial_day"] == 2

    def test_trial_status_paid_user(self, client, mock_db):
        """GET /v1/trial-status for paid user returns trial_phase='not_trial' and trial_day=0."""
        mock_quota = _make_quota_info(plan_id="smartlic_pro", trial_expires_at=None)

        with patch("quota.check_quota", return_value=mock_quota):
            response = client.get("/v1/trial-status")

        assert response.status_code == 200
        data = response.json()

        assert data["trial_phase"] == "not_trial"
        assert data["trial_day"] == 0

    def test_trial_status_fields_present_always(self, client, mock_db):
        """trial_phase and trial_day fields are always present in the response schema."""
        mock_quota = _make_quota_info(plan_id="free_trial", trial_expires_at=None)

        with patch("quota.check_quota", return_value=mock_quota):
            response = client.get("/v1/trial-status")

        assert response.status_code == 200
        data = response.json()

        # Fields must always be present (not optional / missing)
        assert "trial_phase" in data
        assert "trial_day" in data
        # When no trial_expires_at → full_access fallback
        assert data["trial_phase"] == "full_access"
        assert data["trial_day"] == 0
