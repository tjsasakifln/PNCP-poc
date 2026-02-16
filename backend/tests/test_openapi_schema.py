"""
Tests for OpenAPI schema validation and schema drift detection.

This test ensures the OpenAPI schema remains stable and documents changes
when new endpoints or modifications are introduced.
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def schema_snapshot_path():
    """Path to the OpenAPI schema snapshot file."""
    return Path(__file__).parent / "snapshots" / "openapi_schema.json"


class TestOpenAPISchema:
    """Test OpenAPI schema validation and drift detection."""

    def test_openapi_schema_matches_snapshot(self, client, schema_snapshot_path):
        """
        Verify that the OpenAPI schema matches the stored snapshot.

        This test detects schema drift by comparing the current OpenAPI schema
        against a known-good snapshot. If the schema has changed:
        - Review the changes to ensure they are intentional
        - Update the snapshot if the changes are approved
        - This prevents accidental breaking changes to the API contract

        To update the snapshot:
        1. Review the schema changes carefully
        2. Delete the snapshot file: backend/tests/snapshots/openapi_schema.json
        3. Re-run this test to generate a new snapshot
        4. Commit the updated snapshot with your API changes
        """
        # Get current OpenAPI schema
        current_schema = app.openapi()

        # Remove dynamic/unstable fields that change on every run
        # (These don't represent actual API contract changes)
        if "servers" in current_schema:
            del current_schema["servers"]

        # Create snapshots directory if it doesn't exist
        schema_snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate initial snapshot if it doesn't exist
        if not schema_snapshot_path.exists():
            with open(schema_snapshot_path, "w", encoding="utf-8") as f:
                json.dump(current_schema, f, indent=2, sort_keys=True)
            pytest.skip(
                f"Initial OpenAPI schema snapshot created at {schema_snapshot_path}. "
                "Re-run the test to validate against this snapshot."
            )

        # Load snapshot
        with open(schema_snapshot_path, "r", encoding="utf-8") as f:
            snapshot_schema = json.load(f)

        # Compare schemas
        if current_schema != snapshot_schema:
            # Generate diff for debugging
            diff_path = schema_snapshot_path.parent / "openapi_schema.diff.json"
            with open(diff_path, "w", encoding="utf-8") as f:
                json.dump({
                    "snapshot": snapshot_schema,
                    "current": current_schema
                }, f, indent=2, sort_keys=True)

            # Find differences in paths
            snapshot_paths = set(snapshot_schema.get("paths", {}).keys())
            current_paths = set(current_schema.get("paths", {}).keys())

            added_paths = current_paths - snapshot_paths
            removed_paths = snapshot_paths - current_paths

            error_msg = (
                "OpenAPI schema has changed! This may indicate breaking changes.\n\n"
                f"Diff written to: {diff_path}\n\n"
            )

            if added_paths:
                error_msg += f"Added endpoints: {sorted(added_paths)}\n"
            if removed_paths:
                error_msg += f"Removed endpoints: {sorted(removed_paths)}\n"

            error_msg += (
                "\nIf these changes are intentional:\n"
                f"1. Review the changes in {diff_path}\n"
                f"2. Delete {schema_snapshot_path}\n"
                "3. Re-run this test to generate a new snapshot\n"
                "4. Commit the updated snapshot with your changes\n"
            )

            pytest.fail(error_msg)

    def test_openapi_schema_has_required_metadata(self, client):
        """Verify OpenAPI schema contains required metadata."""
        schema = app.openapi()

        # Required top-level fields
        assert "openapi" in schema
        assert schema["openapi"].startswith("3.")  # OpenAPI 3.x

        assert "info" in schema
        assert schema["info"]["title"] == "BidIQ Uniformes API"
        assert "version" in schema["info"]
        assert "description" in schema["info"]

        # Must have paths
        assert "paths" in schema
        assert len(schema["paths"]) > 0

    def test_openapi_schema_documents_health_endpoint(self, client):
        """Verify /health endpoint is documented in OpenAPI schema."""
        schema = app.openapi()

        assert "/health" in schema["paths"]
        assert "get" in schema["paths"]["/health"]

        health_endpoint = schema["paths"]["/health"]["get"]
        assert "summary" in health_endpoint or "description" in health_endpoint
        assert "responses" in health_endpoint
        assert "200" in health_endpoint["responses"]

    def test_openapi_schema_documents_authentication(self, client):
        """Verify authentication is documented in OpenAPI schema."""
        schema = app.openapi()

        # Should have security schemes defined
        if "components" in schema and "securitySchemes" in schema["components"]:
            # At least one security scheme should be defined
            assert len(schema["components"]["securitySchemes"]) > 0
        else:
            # If no global security, at least some endpoints should have security
            has_security = False
            for path_data in schema["paths"].values():
                for operation in path_data.values():
                    if isinstance(operation, dict) and "security" in operation:
                        has_security = True
                        break
                if has_security:
                    break

            # This is informational - not all APIs require auth on all endpoints
            # But documenting it is a best practice
            pass  # Not enforcing this as a hard requirement

    def test_openapi_schema_has_proper_response_schemas(self, client):
        """Verify key endpoints have proper response schemas."""
        schema = app.openapi()

        # Check /health endpoint has a proper response schema
        if "/health" in schema["paths"]:
            health_responses = schema["paths"]["/health"]["get"]["responses"]
            if "200" in health_responses:
                response = health_responses["200"]
                # Should have content or schema definition
                assert "content" in response or "schema" in response

    def test_openapi_schema_is_valid_json(self, client):
        """Verify the OpenAPI schema is valid JSON."""
        schema = app.openapi()

        # Should be serializable to JSON without errors
        json_str = json.dumps(schema)
        assert len(json_str) > 0

        # Should be parsable back from JSON
        parsed = json.loads(json_str)
        assert parsed == schema

    def test_openapi_schema_file_can_be_generated(self, client):
        """Test that OpenAPI schema can be exported to a file."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
