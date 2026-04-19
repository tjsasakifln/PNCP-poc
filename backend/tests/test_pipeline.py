"""Tests for routes.pipeline — Pipeline management endpoints.

STORY-250: Backend pipeline CRUD routes with access control.
SYS-023: GET /pipeline uses user-scoped client (get_user_db).
"""

from unittest.mock import Mock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from auth import require_auth
from database import get_user_db
from routes.pipeline import router


async def _noop_check_pipeline_read_access(user):
    """Async no-op mock for _check_pipeline_read_access."""
    return None


async def _noop_check_pipeline_write_access(user):
    """Async no-op mock for _check_pipeline_write_access."""
    return None


async def _noop_check_pipeline_limit(user):
    """Async no-op mock for _check_pipeline_limit (STORY-356)."""
    return None


async def _raise_trial_expired(user):
    """Mock for quota.require_active_plan that simulates an expired-trial block.

    Post-TD-007 `require_active_plan` lives in quota.plan_auth and internally
    calls quota.plan_enforcement.check_quota (not the facade attribute) — that
    path fetches Supabase on test runners, so tests for capability gating must
    stub the dependency at the quota facade level and raise the same 403
    payload the real function would emit on allowed=False.
    """
    raise HTTPException(
        status_code=403,
        detail={
            "message": "Seu trial expirou.",
            "error_code": "trial_expired",
        },
    )


MOCK_USER = {"id": "user-pipeline-uuid", "email": "pipeline@test.com", "role": "authenticated"}
MOCK_USER_2 = {"id": "user-other-uuid", "email": "other@test.com", "role": "authenticated"}
MOCK_MASTER = {"id": "master-uuid", "email": "master@test.com", "role": "authenticated"}
ITEM_ID = "item-uuid-1234"
PNCP_ID = "12345678-1-000001/2026"


def _create_client(user=None, mock_user_db=None):
    """Create test client with auth and user_db overrides.

    Args:
        user: User dict for require_auth override (defaults to MOCK_USER).
        mock_user_db: Mock for get_user_db override. Required for GET /pipeline
            (SYS-023: GET uses user-scoped client). POST/PATCH/DELETE use
            get_supabase() — mock those via @patch("routes.pipeline.get_supabase").
    """
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: (user or MOCK_USER)

    # SYS-023: GET /pipeline uses get_user_db. Override when mock_user_db provided.
    if mock_user_db is not None:
        app.dependency_overrides[get_user_db] = lambda: mock_user_db

    return TestClient(app)


def _mock_sb():
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.upsert.return_value = sb
    sb.update.return_value = sb
    sb.delete.return_value = sb
    sb.eq.return_value = sb
    sb.limit.return_value = sb

    # Handle .not_.in_() chain
    not_mock = Mock()
    not_mock.in_.return_value = sb
    not_mock.is_.return_value = sb
    sb.not_ = not_mock

    sb.in_.return_value = sb
    sb.lte.return_value = sb
    sb.is_.return_value = sb
    sb.order.return_value = sb
    sb.range.return_value = sb
    result = Mock(data=[], count=0)
    sb.execute.return_value = result
    return sb


# Sample pipeline item data
SAMPLE_ITEM = {
    "id": ITEM_ID,
    "user_id": MOCK_USER["id"],
    "pncp_id": PNCP_ID,
    "objeto": "Aquisição de uniformes para guardas municipais",
    "orgao": "Prefeitura de São Paulo",
    "uf": "SP",
    "valor_estimado": 150000.0,
    "data_encerramento": "2026-03-01T23:59:59",
    "link_pncp": "https://pncp.gov.br/app/editais/12345",
    "stage": "descoberta",
    "notes": None,
    "created_at": "2026-02-14T10:00:00",
    "updated_at": "2026-02-14T10:00:00",
}


# ============================================================================
# POST /pipeline — create pipeline item (AC2)
# ============================================================================

class TestCreatePipelineItem:

    @patch("routes.pipeline._check_pipeline_limit", _noop_check_pipeline_limit)
    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_create_success(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/pipeline", json={
            "pncp_id": PNCP_ID,
            "objeto": "Aquisição de uniformes para guardas municipais",
            "orgao": "Prefeitura de São Paulo",
            "uf": "SP",
            "valor_estimado": 150000.0,
            "data_encerramento": "2026-03-01T23:59:59",
            "link_pncp": "https://pncp.gov.br/app/editais/12345",
        })

        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == ITEM_ID
        assert body["pncp_id"] == PNCP_ID
        assert body["stage"] == "descoberta"

    @patch("routes.pipeline._check_pipeline_limit", _noop_check_pipeline_limit)
    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_create_duplicate_returns_existing(self, mock_get_sb):
        """ISSUE-021: Duplicate pncp_id returns 201 with existing item (idempotent upsert)."""
        sb = _mock_sb()
        # Upsert returns empty on conflict (ignore_duplicates=True)
        call_count = [0]
        def _side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return Mock(data=[])  # upsert returns empty on conflict
            return Mock(data=[SAMPLE_ITEM])  # fetch existing returns item
        sb.execute.side_effect = lambda: _side_effect()
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/pipeline", json={
            "pncp_id": PNCP_ID,
            "objeto": "Test",
            "orgao": "Test Org",
            "uf": "SP",
            "link_pncp": "https://pncp.gov.br/test",
        })

        assert resp.status_code == 201
        assert resp.json()["pncp_id"] == PNCP_ID

    def test_create_missing_pncp_id_422(self):
        """Test missing required field returns 422."""
        client = _create_client()

        resp = client.post("/pipeline", json={
            "objeto": "Test",
            "orgao": "Test Org",
            "uf": "SP",
            # Missing pncp_id
        })

        assert resp.status_code == 422

    @patch("routes.pipeline._check_pipeline_limit", _noop_check_pipeline_limit)
    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_create_empty_data_failure(self, mock_get_sb):
        """Test database failure (empty result.data) returns 500."""
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])  # Empty data = failure
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/pipeline", json={
            "pncp_id": PNCP_ID,
            "objeto": "Test",
            "orgao": "Test Org",
            "uf": "SP",
            "link_pncp": "https://pncp.gov.br/test",
        })

        assert resp.status_code == 500
        assert "Falha ao criar item" in resp.json()["detail"]


# ============================================================================
# GET /pipeline — list pipeline items (AC3)
# ISSUE-021 fix: GET now uses admin client (get_supabase) — consistent with
# POST/PATCH/DELETE. Defense-in-depth via .eq("user_id", user_id).
# Tests patch get_supabase (same pattern as POST tests).
# ============================================================================

class TestListPipelineItems:

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_list_success(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM], count=1)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["pncp_id"] == PNCP_ID
        assert body["total"] == 1
        assert body["limit"] == 50
        assert body["offset"] == 0

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_list_with_stage_filter(self, mock_get_sb):
        sb = _mock_sb()
        item_analise = {**SAMPLE_ITEM, "stage": "analise"}
        sb.execute.return_value = Mock(data=[item_analise], count=1)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline?stage=analise")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["stage"] == "analise"

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    def test_list_invalid_stage_422(self):
        client = _create_client()

        resp = client.get("/pipeline?stage=invalid_stage")

        assert resp.status_code == 422
        assert "Stage inválido" in resp.json()["detail"]

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_list_with_pagination(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM], count=10)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline?limit=5&offset=5")

        assert resp.status_code == 200
        body = resp.json()
        assert body["limit"] == 5
        assert body["offset"] == 5
        assert body["total"] == 10

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_list_empty(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0


# ============================================================================
# PATCH /pipeline/{item_id} — update pipeline item (AC4)
# ============================================================================

class TestUpdatePipelineItem:

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_update_stage_success(self, mock_get_sb):
        sb = _mock_sb()
        updated_item = {**SAMPLE_ITEM, "stage": "analise"}
        sb.execute.return_value = Mock(data=[updated_item])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={
            "stage": "analise",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["stage"] == "analise"

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_update_notes_success(self, mock_get_sb):
        sb = _mock_sb()
        updated_item = {**SAMPLE_ITEM, "notes": "Importante: verificar requisitos técnicos"}
        sb.execute.return_value = Mock(data=[updated_item])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={
            "notes": "Importante: verificar requisitos técnicos",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["notes"] == "Importante: verificar requisitos técnicos"

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_update_both_stage_and_notes(self, mock_get_sb):
        sb = _mock_sb()
        updated_item = {**SAMPLE_ITEM, "stage": "preparando", "notes": "Documentos prontos"}
        sb.execute.return_value = Mock(data=[updated_item])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={
            "stage": "preparando",
            "notes": "Documentos prontos",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["stage"] == "preparando"
        assert body["notes"] == "Documentos prontos"

    def test_update_invalid_stage_422(self):
        """Invalid stage triggers Pydantic validation error (422)."""
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={
            "stage": "invalid_stage",
        })

        assert resp.status_code == 422
        # Pydantic returns a list of validation errors
        detail = resp.json()["detail"]
        assert isinstance(detail, list)
        assert detail[0]["loc"] == ["body", "stage"]

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_update_empty_payload_422(self, mock_get_sb):
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={})

        assert resp.status_code == 422
        assert "Nenhum campo para atualizar" in resp.json()["detail"]

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_update_not_found_404(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])  # Empty result = not found
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={
            "stage": "analise",
        })

        assert resp.status_code == 404
        assert "não encontrado" in resp.json()["detail"]


# ============================================================================
# DELETE /pipeline/{item_id} — remove pipeline item (AC5)
# ============================================================================

class TestDeletePipelineItem:

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_delete_success(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.delete(f"/pipeline/{ITEM_ID}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "removido" in body["message"]

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_delete_not_found_404(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])  # Empty result = not found
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.delete(f"/pipeline/{ITEM_ID}")

        assert resp.status_code == 404
        assert "não encontrado" in resp.json()["detail"]


# ============================================================================
# GET /pipeline/alerts — deadline alerts (AC6)
# ============================================================================

class TestPipelineAlerts:

    @patch("routes.pipeline.get_supabase")
    @patch("routes.pipeline._check_pipeline_read_access")
    def test_alerts_success(self, mock_check_read_access, mock_get_sb):
        mock_check_read_access.return_value = None  # Allow access
        sb = _mock_sb()
        # Item with approaching deadline
        alert_item = {**SAMPLE_ITEM, "data_encerramento": "2026-02-16T23:59:59"}
        sb.execute.return_value = Mock(data=[alert_item])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline/alerts")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["total"] == 1
        assert body["items"][0]["pncp_id"] == PNCP_ID

    @patch("routes.pipeline.get_supabase")
    @patch("routes.pipeline._check_pipeline_read_access")
    def test_alerts_empty(self, mock_check_read_access, mock_get_sb):
        mock_check_read_access.return_value = None  # Allow access
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline/alerts")

        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0


# ============================================================================
# Access Control Tests (AC12-13)
# ISSUE-021 fix: GET /pipeline now uses admin client (get_supabase), same as POST.
# Tests patch get_supabase instead of mock_user_db.
# ============================================================================

class TestPipelineAccessControl:

    @patch("routes.pipeline.get_supabase")
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_access_smartlic_pro_allowed(self, mock_has_master, mock_check_quota, mock_get_sb):
        """GTM-FIX-015: SmartLic Pro plan users can access pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="smartlic_pro",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("routes.pipeline.get_supabase")
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_access_maquina_allowed(self, mock_has_master, mock_check_quota, mock_get_sb):
        """Maquina plan users can access pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="maquina",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("routes.pipeline.get_supabase")
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_access_sala_guerra_allowed(self, mock_has_master, mock_check_quota, mock_get_sb):
        """Sala de Guerra plan users can access pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="sala_guerra",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("routes.pipeline.get_supabase")
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_access_free_trial_read_allowed(self, mock_has_master, mock_check_quota, mock_get_sb):
        """STORY-265 AC3: Free trial users can READ pipeline (allow_pipeline=True since STORY-264)."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_access_consultor_agil_denied_403(self, mock_has_master, mock_check_quota):
        """Consultor Ágil users (no allow_pipeline) get 403 with upgrade CTA."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="consultor_agil",
            allowed=True,
            capabilities={"allow_pipeline": False},
        )
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 403

    @patch("routes.pipeline.get_supabase")
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_access_master_bypass(self, mock_has_master, mock_check_quota, mock_get_sb):
        """Master users bypass plan check and can access pipeline."""
        mock_has_master.return_value = True
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client(user=MOCK_MASTER)

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("quota.require_active_plan", new=_raise_trial_expired)
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_create_access_denied_403(self, mock_has_master, mock_check_quota):
        """STORY-265 AC2: Expired free trial cannot POST /pipeline.

        Post-TD-007: quota facade re-exports require_active_plan from plan_auth.
        Route's `from quota import require_active_plan, check_quota` picks up
        patched attribute via late-binding import — both must be mocked so the
        403 path (capability gate) runs instead of hitting Supabase.
        """
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=False,
            capabilities={"allow_pipeline": True},
            trial_expires_at=None,
            error_message="Seu trial expirou.",
        )
        client = _create_client()

        resp = client.post("/pipeline", json={
            "pncp_id": PNCP_ID,
            "objeto": "Test",
            "orgao": "Test Org",
            "uf": "SP",
            "link_pncp": "https://pncp.gov.br/test",
        })

        assert resp.status_code == 403

    @patch("quota.require_active_plan", new=_raise_trial_expired)
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_update_access_denied_403(self, mock_has_master, mock_check_quota):
        """STORY-265 AC2: Expired free trial cannot PATCH /pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=False,
            capabilities={"allow_pipeline": True},
            trial_expires_at=None,
            error_message="Seu trial expirou.",
        )
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={
            "stage": "analise",
        })

        assert resp.status_code == 403

    @patch("quota.require_active_plan", new=_raise_trial_expired)
    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_delete_access_denied_403(self, mock_has_master, mock_check_quota):
        """STORY-265 AC2: Expired free trial cannot DELETE /pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=False,
            capabilities={"allow_pipeline": True},
            trial_expires_at=None,
            error_message="Seu trial expirou.",
        )
        client = _create_client()

        resp = client.delete(f"/pipeline/{ITEM_ID}")

        assert resp.status_code == 403

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    @patch("routes.pipeline.get_supabase")
    def test_alerts_access_read_allowed(self, mock_get_sb, mock_has_master, mock_check_quota):
        """STORY-265 AC3: Free trial (even expired) can read /pipeline/alerts."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=False,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline/alerts")

        assert resp.status_code == 200
