"""Resend webhook HMAC signature verification tests.

Validates Svix-format signature verification on POST /v1/trial-emails/webhook.
Security: fail-closed when secret missing, signature invalid, or timestamp stale.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def fake_secret():
    """Generate a known whsec_<base64> secret for signing test payloads."""
    raw = b"\x01" * 32
    return f"whsec_{base64.b64encode(raw).decode()}", raw


def _sign(secret_raw: bytes, svix_id: str, ts: int, body: bytes) -> str:
    payload = f"{svix_id}.{ts}.".encode("utf-8") + body
    sig = base64.b64encode(hmac.new(secret_raw, payload, hashlib.sha256).digest()).decode()
    return f"v1,{sig}"


@pytest.fixture
def client(fake_secret):
    """TestClient with RESEND_WEBHOOK_SECRET set."""
    secret_str, _ = fake_secret
    with patch.dict(os.environ, {"RESEND_WEBHOOK_SECRET": secret_str}):
        from main import app
        yield TestClient(app)


def test_valid_signature_processes_webhook(client, fake_secret):
    """Valid Svix signature → handler called → 200."""
    _, raw = fake_secret
    body = json.dumps({"type": "email.opened", "data": {"email_id": "res-1"}}).encode()
    ts = int(time.time())
    headers = {
        "svix-id": "msg_test_1",
        "svix-timestamp": str(ts),
        "svix-signature": _sign(raw, "msg_test_1", ts, body),
        "content-type": "application/json",
    }
    with patch(
        "services.trial_email_sequence.handle_resend_webhook",
        new=AsyncMock(return_value=True),
    ):
        r = client.post("/v1/trial-emails/webhook", content=body, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] in ("processed", "skipped", "ignored")


def test_missing_signature_header_rejected(client):
    """No svix-signature header → 401 (fail-closed)."""
    body = json.dumps({"type": "email.opened", "data": {}}).encode()
    r = client.post(
        "/v1/trial-emails/webhook",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 401


def test_missing_secret_rejects_all(fake_secret):
    """RESEND_WEBHOOK_SECRET unset → all events rejected with 401."""
    _, raw = fake_secret
    body = json.dumps({"type": "email.opened", "data": {}}).encode()
    ts = int(time.time())
    with patch.dict(os.environ, {"RESEND_WEBHOOK_SECRET": ""}, clear=False):
        # Force re-read by reimporting? env is read at request time, so this works.
        from main import app
        c = TestClient(app)
        r = c.post(
            "/v1/trial-emails/webhook",
            content=body,
            headers={
                "svix-id": "msg",
                "svix-timestamp": str(ts),
                "svix-signature": _sign(raw, "msg", ts, body),
                "content-type": "application/json",
            },
        )
    assert r.status_code == 401


def test_tampered_body_rejected(client, fake_secret):
    """Signature computed for body A, request sends body B → 401."""
    _, raw = fake_secret
    original = json.dumps({"type": "email.opened", "data": {"email_id": "1"}}).encode()
    tampered = json.dumps({"type": "email.bounced", "data": {"email_id": "EVIL"}}).encode()
    ts = int(time.time())
    headers = {
        "svix-id": "msg",
        "svix-timestamp": str(ts),
        "svix-signature": _sign(raw, "msg", ts, original),
        "content-type": "application/json",
    }
    r = client.post("/v1/trial-emails/webhook", content=tampered, headers=headers)
    assert r.status_code == 401


def test_replay_old_timestamp_rejected(client, fake_secret):
    """Timestamp >5 min old → 401 (replay protection)."""
    _, raw = fake_secret
    body = json.dumps({"type": "email.opened", "data": {}}).encode()
    stale_ts = int(time.time()) - 600  # 10 min ago
    headers = {
        "svix-id": "msg",
        "svix-timestamp": str(stale_ts),
        "svix-signature": _sign(raw, "msg", stale_ts, body),
        "content-type": "application/json",
    }
    r = client.post("/v1/trial-emails/webhook", content=body, headers=headers)
    assert r.status_code == 401


def test_wrong_secret_rejected(client):
    """Signature signed with different secret → 401."""
    other_secret = b"\xff" * 32
    body = json.dumps({"type": "email.opened", "data": {}}).encode()
    ts = int(time.time())
    headers = {
        "svix-id": "msg",
        "svix-timestamp": str(ts),
        "svix-signature": _sign(other_secret, "msg", ts, body),
        "content-type": "application/json",
    }
    r = client.post("/v1/trial-emails/webhook", content=body, headers=headers)
    assert r.status_code == 401


def test_multiple_signatures_one_valid(client, fake_secret):
    """Header with multiple `v1,sig` entries — accept if ANY matches (key rotation)."""
    _, raw = fake_secret
    other = b"\xab" * 32
    body = json.dumps({"type": "email.opened", "data": {}}).encode()
    ts = int(time.time())
    bad_sig = _sign(other, "msg", ts, body)  # wrong key first
    good_sig = _sign(raw, "msg", ts, body)
    headers = {
        "svix-id": "msg",
        "svix-timestamp": str(ts),
        "svix-signature": f"{bad_sig} {good_sig}",
        "content-type": "application/json",
    }
    with patch(
        "services.trial_email_sequence.handle_resend_webhook",
        new=AsyncMock(return_value=True),
    ):
        r = client.post("/v1/trial-emails/webhook", content=body, headers=headers)
    assert r.status_code == 200
