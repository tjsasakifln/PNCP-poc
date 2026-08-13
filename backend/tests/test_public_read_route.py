"""HTTP surface for the public_read consumer."""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_public_read_health_never_leaks_dsn():
    from startup.app_factory import create_app

    client = TestClient(create_app())
    with patch.dict("os.environ", {"PUBLIC_READ_V1_DSN": "postgresql://secret@host/db"}, clear=False):
        res = client.get("/v1/public-read/health")
    assert res.status_code == 200
    body = res.json()
    assert body["contract_version"] == "v1.0.0"
    assert "secret" not in res.text
    assert "postgresql://" not in res.text
    assert body["mode"] in {"off", "shadow", "canary", "on"}
