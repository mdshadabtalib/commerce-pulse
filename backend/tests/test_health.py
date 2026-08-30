import httpx

from app.main import create_app


async def test_health_endpoint_returns_service_metadata() -> None:
    app = create_app()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "CommercePulse"
    assert body["version"] == "1.0.0"
    assert body["uptime_seconds"] >= 0
    assert response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"


def test_core_api_routers_are_registered() -> None:
    paths = create_app().openapi()["paths"]

    assert "/api/v1/auth/register" in paths
    assert "/api/v1/organizations" in paths
    assert "/api/v1/datasets/upload" in paths
