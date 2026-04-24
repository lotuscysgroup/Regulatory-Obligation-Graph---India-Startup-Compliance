import os

import pytest
from fastapi.testclient import TestClient

from rog.app.main import create_app


def _has_integration_db() -> bool:
    url = os.getenv("DATABASE_URL", "")
    return url.startswith("postgresql")


@pytest.mark.skipif(not _has_integration_db(), reason="Requires DATABASE_URL pointing to a Postgres database")
def test_register_and_login_roundtrip() -> None:
    app = create_app()
    client = TestClient(app)

    email = "user1@example.com"
    password = "StrongPassword123!"

    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "User One"})
    assert r.status_code in (201, 400)
    if r.status_code == 201:
        body = r.json()
        assert body["email"] == email

    r2 = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200
    token = r2.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

