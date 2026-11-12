import pytest


@pytest.mark.django_db
def test_health_endpoint_is_public_and_reports_ok(api_client):
    response = api_client.get("/api/health/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "fabrisee"
    assert body["database"] == "ok"
    assert body["time_zone"] == "Asia/Manila"
    # Times are reported in Manila time (UTC+08:00).
    assert body["time"].endswith("+08:00")


@pytest.mark.django_db
def test_unknown_api_path_returns_json_404(api_client):
    response = api_client.get("/api/does-not-exist/")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "This API endpoint does not exist.",
        "code": "not_found",
        "fields": {},
    }


def test_non_api_paths_fall_through_to_the_react_app(client, settings, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>FabriSee</title>")
    settings.FRONTEND_DIST_DIR = dist

    response = client.get("/app/projects/12")

    assert response.status_code == 200
    assert b"FabriSee" in response.content
    assert response["Cache-Control"] == "no-cache"


def test_missing_frontend_build_is_reported_outside_debug(client, settings, tmp_path):
    settings.FRONTEND_DIST_DIR = tmp_path / "missing"

    response = client.get("/portal")

    assert response.status_code == 503
