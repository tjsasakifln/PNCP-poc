"""Tests for DEBT-120 AC5-AC7: Pipeline search_id traceability.

Verifies that pipeline items can store and return the search_id
that originated them, providing search-to-pipeline traceability.
"""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from database import get_user_db
from routes.pipeline import router


async def _noop_check_pipeline_read_access(user):
    return None


async def _noop_check_pipeline_write_access(user):
    return None


async def _noop_check_pipeline_limit(user):
    return None


MOCK_USER = {"id": "user-debt120-uuid", "email": "debt120@test.com", "role": "authenticated"}


def _mock_sb():
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.update.return_value = sb
    sb.delete.return_value = sb
    sb.eq.return_value = sb
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


def _create_client(user=None, mock_user_db=None):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: (user or MOCK_USER)
    # Only inject get_user_db for GET tests (SYS-023). POST uses get_supabase().
    if mock_user_db is not None:
        app.dependency_overrides[get_user_db] = lambda: mock_user_db
    return TestClient(app)


SAMPLE_ITEM_WITH_SEARCH_ID = {
    "id": "item-uuid-debt120",
    "user_id": MOCK_USER["id"],
    "pncp_id": "99999999-1-000001/2026",
    "objeto": "Serviço de manutenção predial",
    "orgao": "Prefeitura de Curitiba",
    "uf": "PR",
    "valor_estimado": 250000.0,
    "data_encerramento": "2026-04-01T23:59:59",
    "link_pncp": "https://pncp.gov.br/app/editais/99999",
    "stage": "descoberta",
    "notes": None,
    "search_id": "srch_abc123xyz",
    "created_at": "2026-03-10T10:00:00",
    "updated_at": "2026-03-10T10:00:00",
    "version": 1,
}

SAMPLE_ITEM_NO_SEARCH_ID = {
    **SAMPLE_ITEM_WITH_SEARCH_ID,
    "id": "item-uuid-no-search",
    "pncp_id": "88888888-1-000001/2026",
    "search_id": None,
}


class TestPipelineSearchIdTraceability:
    """DEBT-120 AC5-AC7: search_id field on pipeline_items."""

    @patch("routes.pipeline._check_pipeline_limit", _noop_check_pipeline_limit)
    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_ac6_create_with_search_id(self, mock_get_sb):
        """AC6: search_id is saved when adding item to pipeline."""
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM_WITH_SEARCH_ID])
        mock_get_sb.return_value = sb

        client = _create_client()
        resp = client.post("/pipeline", json={
            "pncp_id": "99999999-1-000001/2026",
            "objeto": "Serviço de manutenção predial",
            "orgao": "Prefeitura de Curitiba",
            "uf": "PR",
            "valor_estimado": 250000.0,
            "search_id": "srch_abc123xyz",
        })

        assert resp.status_code == 201
        body = resp.json()
        assert body["search_id"] == "srch_abc123xyz"

        # Verify search_id was included in the insert call
        insert_call = sb.insert.call_args
        assert insert_call is not None
        insert_data = insert_call[0][0]
        assert insert_data["search_id"] == "srch_abc123xyz"

    @patch("routes.pipeline._check_pipeline_limit", _noop_check_pipeline_limit)
    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_ac6_create_without_search_id(self, mock_get_sb):
        """AC6: search_id defaults to None when not provided."""
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM_NO_SEARCH_ID])
        mock_get_sb.return_value = sb

        client = _create_client()
        resp = client.post("/pipeline", json={
            "pncp_id": "88888888-1-000001/2026",
            "objeto": "Serviço de manutenção predial",
        })

        assert resp.status_code == 201
        body = resp.json()
        assert body["search_id"] is None

        # Verify search_id was included as None in the insert
        insert_call = sb.insert.call_args
        insert_data = insert_call[0][0]
        assert insert_data["search_id"] is None

    @patch("routes.pipeline._check_pipeline_limit", _noop_check_pipeline_limit)
    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_ac7_response_includes_search_id(self, mock_get_sb):
        """AC7: PipelineItemResponse includes search_id field."""
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM_WITH_SEARCH_ID])
        mock_get_sb.return_value = sb

        client = _create_client()
        resp = client.post("/pipeline", json={
            "pncp_id": "99999999-1-000001/2026",
            "objeto": "Serviço de manutenção predial",
            "search_id": "srch_abc123xyz",
        })

        assert resp.status_code == 201
        body = resp.json()
        # Verify the field exists in response
        assert "search_id" in body
        assert body["search_id"] == "srch_abc123xyz"

    def test_ac7_schema_search_id_optional(self):
        """AC7: search_id is Optional in PipelineItemCreate."""
        from schemas import PipelineItemCreate

        # Should work without search_id
        item = PipelineItemCreate(pncp_id="test-123", objeto="Test object")
        assert item.search_id is None

        # Should work with search_id
        item_with = PipelineItemCreate(
            pncp_id="test-456",
            objeto="Test object",
            search_id="srch_test",
        )
        assert item_with.search_id == "srch_test"

    def test_ac7_schema_search_id_max_length(self):
        """AC7: search_id respects max_length=100."""
        from schemas import PipelineItemCreate
        from pydantic import ValidationError

        try:
            PipelineItemCreate(
                pncp_id="test-789",
                objeto="Test object",
                search_id="x" * 101,
            )
            assert False, "Should have raised ValidationError for too-long search_id"
        except ValidationError as e:
            assert "search_id" in str(e)

    def test_ac7_response_model_has_search_id(self):
        """AC7: PipelineItemResponse model includes search_id."""
        from schemas import PipelineItemResponse

        resp = PipelineItemResponse(
            id="uuid-1",
            user_id="user-1",
            pncp_id="test-123",
            objeto="Test",
            stage="descoberta",
            created_at="2026-03-10T00:00:00",
            updated_at="2026-03-10T00:00:00",
            search_id="srch_test",
        )
        assert resp.search_id == "srch_test"

        # Also works without search_id
        resp_none = PipelineItemResponse(
            id="uuid-2",
            user_id="user-1",
            pncp_id="test-456",
            objeto="Test",
            stage="descoberta",
            created_at="2026-03-10T00:00:00",
            updated_at="2026-03-10T00:00:00",
        )
        assert resp_none.search_id is None
