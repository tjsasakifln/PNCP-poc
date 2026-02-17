"""Tests for routes.pipeline — Pipeline management endpoints.

STORY-250: Backend pipeline CRUD routes with access control.
"""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from routes.pipeline import router


MOCK_USER = {"id": "user-pipeline-uuid", "email": "pipeline@test.com", "role": "authenticated"}
MOCK_USER_2 = {"id": "user-other-uuid", "email": "other@test.com", "role": "authenticated"}
MOCK_MASTER = {"id": "master-uuid", "email": "master@test.com", "role": "authenticated"}
ITEM_ID = "item-uuid-1234"
PNCP_ID = "12345678-1-000001/2026"


def _create_client(user=None):
    """Create test client with auth overrides.

    Args:
        user: User dict for require_auth override (defaults to MOCK_USER).
    """
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: (user or MOCK_USER)
    return TestClient(app)


def _mock_sb():
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.update.return_value = sb
    sb.delete.return_value = sb
    sb.eq.return_value = sb

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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
    @patch("routes.pipeline.get_supabase")
    def test_create_duplicate_409(self, mock_get_sb):
        """Test duplicate pncp_id for same user returns 409."""
        sb = _mock_sb()
        # Simulate unique constraint violation
        sb.execute.side_effect = Exception("duplicate key value violates unique constraint")
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/pipeline", json={
            "pncp_id": PNCP_ID,
            "objeto": "Test",
            "orgao": "Test Org",
            "uf": "SP",
            "link_pncp": "https://pncp.gov.br/test",
        })

        assert resp.status_code == 409
        assert "já está no seu pipeline" in resp.json()["detail"]

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
    @patch("routes.pipeline.get_supabase")
    def test_create_duplicate_23505_error_code(self, mock_get_sb):
        """Test PostgreSQL unique violation error code 23505."""
        sb = _mock_sb()
        sb.execute.side_effect = Exception("ERROR: duplicate key; sqlstate: 23505")
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/pipeline", json={
            "pncp_id": PNCP_ID,
            "objeto": "Test",
            "orgao": "Test Org",
            "uf": "SP",
            "link_pncp": "https://pncp.gov.br/test",
        })

        assert resp.status_code == 409

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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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
# ============================================================================

class TestListPipelineItems:

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
    @patch("routes.pipeline.get_supabase")
    def test_list_invalid_stage_422(self, mock_get_sb):
        client = _create_client()

        resp = client.get("/pipeline?stage=invalid_stage")

        assert resp.status_code == 422
        assert "Stage inválido" in resp.json()["detail"]

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
    @patch("routes.pipeline.get_supabase")
    def test_update_empty_payload_422(self, mock_get_sb):
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={})

        assert resp.status_code == 422
        assert "Nenhum campo para atualizar" in resp.json()["detail"]

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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

    @patch("routes.pipeline._check_pipeline_access", lambda user: None)
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
    @patch("routes.pipeline._check_pipeline_access")
    def test_alerts_success(self, mock_check_access, mock_get_sb):
        mock_check_access.return_value = None  # Allow access
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
    @patch("routes.pipeline._check_pipeline_access")
    def test_alerts_empty(self, mock_check_access, mock_get_sb):
        mock_check_access.return_value = None  # Allow access
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
# ============================================================================

class TestPipelineAccessControl:

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    @patch("routes.pipeline.get_supabase")
    def test_access_smartlic_pro_allowed(self, mock_get_sb, mock_has_master, mock_check_quota):
        """GTM-FIX-015: SmartLic Pro plan users can access pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="smartlic_pro")
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    @patch("routes.pipeline.get_supabase")
    def test_access_maquina_allowed(self, mock_get_sb, mock_has_master, mock_check_quota):
        """Maquina plan users can access pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="maquina")
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    @patch("routes.pipeline.get_supabase")
    def test_access_sala_guerra_allowed(self, mock_get_sb, mock_has_master, mock_check_quota):
        """Sala de Guerra plan users can access pipeline."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="sala_guerra")
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    @patch("routes.pipeline.get_supabase")
    def test_access_free_trial_denied_403(self, mock_get_sb, mock_has_master, mock_check_quota):
        """Free trial users get 403 with upgrade CTA."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="free_trial")
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 403
        body = resp.json()
        assert body["detail"]["error_code"] == "pipeline_not_available"
        assert body["detail"]["upgrade_cta"] == "Assinar SmartLic Pro"
        assert body["detail"]["suggested_plan"] == "smartlic_pro"

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    @patch("routes.pipeline.get_supabase")
    def test_access_consultor_agil_denied_403(self, mock_get_sb, mock_has_master, mock_check_quota):
        """Consultor Ágil users get 403 with upgrade CTA."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="consultor_agil")
        client = _create_client()

        resp = client.get("/pipeline")

        assert resp.status_code == 403

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    @patch("routes.pipeline.get_supabase")
    def test_access_master_bypass(self, mock_get_sb, mock_has_master, mock_check_quota):
        """Master users bypass plan check and can access pipeline."""
        mock_has_master.return_value = True
        # Don't need to set check_quota since master bypasses it
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client(user=MOCK_MASTER)

        resp = client.get("/pipeline")

        assert resp.status_code == 200

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_create_access_denied_403(self, mock_has_master, mock_check_quota):
        """Access control applies to POST /pipeline as well."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="free_trial")
        client = _create_client()

        resp = client.post("/pipeline", json={
            "pncp_id": PNCP_ID,
            "objeto": "Test",
            "orgao": "Test Org",
            "uf": "SP",
            "link_pncp": "https://pncp.gov.br/test",
        })

        assert resp.status_code == 403

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_update_access_denied_403(self, mock_has_master, mock_check_quota):
        """Access control applies to PATCH /pipeline/{item_id}."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="free_trial")
        client = _create_client()

        resp = client.patch(f"/pipeline/{ITEM_ID}", json={
            "stage": "analise",
        })

        assert resp.status_code == 403

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_delete_access_denied_403(self, mock_has_master, mock_check_quota):
        """Access control applies to DELETE /pipeline/{item_id}."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="free_trial")
        client = _create_client()

        resp = client.delete(f"/pipeline/{ITEM_ID}")

        assert resp.status_code == 403

    @patch("quota.check_quota")
    @patch("authorization.has_master_access")
    def test_alerts_access_denied_403(self, mock_has_master, mock_check_quota):
        """Access control applies to GET /pipeline/alerts."""
        mock_has_master.return_value = False
        mock_check_quota.return_value = Mock(plan_id="free_trial")
        client = _create_client()

        resp = client.get("/pipeline/alerts")

        assert resp.status_code == 403
