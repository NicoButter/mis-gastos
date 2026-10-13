from rest_framework.test import APIClient


def test_openapi_schema_is_public_and_versioned():
    response = APIClient().get("/api/v1/schema/")

    assert response.status_code == 200
    assert "Mis Gastos API" in response.content.decode()
