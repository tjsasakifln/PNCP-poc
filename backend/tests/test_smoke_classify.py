from ops.smoke_classify import classify_probe, is_healthy


def test_railway_fallback_is_edge_not_app():
    result = classify_probe(404, {"x-railway-fallback": "true"}, "/health/live")
    assert result == "edge_fallback"
    assert is_healthy(result) is False


def test_app_500_is_unhealthy():
    assert classify_probe(500, {}, "/health/live") == "app_unhealthy"
    assert classify_probe(503, {}, "/v1/buscar") == "app_unhealthy"


def test_unknown_404_is_not_healthy():
    result = classify_probe(404, {}, "/this-route-does-not-exist")
    assert result == "not_found"
    assert is_healthy(result) is False


def test_health_200_is_healthy():
    assert classify_probe(200, {}, "/health/live") == "ok"
    assert is_healthy("ok") is True


def test_health_404_without_fallback_is_app_unhealthy():
    assert classify_probe(404, {}, "/health/live") == "app_unhealthy"
