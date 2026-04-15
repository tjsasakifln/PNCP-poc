"""Contract tests for Stripe webhook event payloads.

We commit four representative event types (invoice.paid,
customer.subscription.deleted, customer.subscription.updated,
checkout.session.completed). All of them share the top-level Event
envelope (``id``, ``object``, ``type``, ``data.object``, etc.), and the
schema captures the union of fields observed across samples.

No live test is provided: Stripe does not expose a public live endpoint
that emits arbitrary event types. Drift is detected by re-recording a
sample (see ``docs/qa/contract-tests.md``) when Stripe bumps
``api_version``.
"""

from __future__ import annotations

import pytest

from .contract_validator import validate_shape


SNAPSHOT_FILES = [
    "stripe/invoice_paid.json",
    "stripe/customer_subscription_deleted.json",
    "stripe/customer_subscription_updated.json",
    "stripe/checkout_session_completed.json",
]


@pytest.mark.contract
@pytest.mark.parametrize("snapshot_file", SNAPSHOT_FILES)
def test_stripe_snapshot_matches_schema(snapshot_file, stripe_schema, load_snapshot):
    data = load_snapshot(snapshot_file)
    result = validate_shape(data["response"], stripe_schema)
    assert result.valid, (
        f"Snapshot {snapshot_file} drifted from schema:\n  - "
        + "\n  - ".join(result.errors)
    )


@pytest.mark.contract
def test_stripe_event_envelope_required_fields(stripe_schema):
    """The webhook handler in backend/webhooks/stripe.py relies on these
    fields to dispatch events. They MUST remain required across versions.
    """

    required = set(stripe_schema.get("required", []))
    for field in ("id", "object", "type", "data", "created", "livemode"):
        assert field in required, f"Stripe envelope missing required field: {field}"

    data_schema = stripe_schema["properties"]["data"]
    assert data_schema["type"] == "object"
    assert "object" in set(data_schema.get("required", [])), (
        "data.object must remain required — webhook handlers dereference it directly"
    )


@pytest.mark.contract
@pytest.mark.parametrize(
    "snapshot_file,expected_type",
    [
        ("stripe/invoice_paid.json", "invoice.paid"),
        ("stripe/customer_subscription_deleted.json", "customer.subscription.deleted"),
        ("stripe/customer_subscription_updated.json", "customer.subscription.updated"),
        ("stripe/checkout_session_completed.json", "checkout.session.completed"),
    ],
)
def test_stripe_event_type_field_is_string(snapshot_file, expected_type, load_snapshot):
    snap = load_snapshot(snapshot_file)["response"]
    assert snap["type"] == expected_type
    assert isinstance(snap["data"]["object"], dict)
