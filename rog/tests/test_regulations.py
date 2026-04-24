import os
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from rog.app.main import create_app


def _has_integration_db() -> bool:
    url = os.getenv("DATABASE_URL", "")
    return url.startswith("postgresql")


@pytest.mark.skipif(not _has_integration_db(), reason="Requires DATABASE_URL pointing to a Postgres database")
def test_upload_and_fetch_regulation() -> None:
    app = create_app()
    client = TestClient(app)

    email = "reguser@example.com"
    password = "StrongPassword123!"

    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]

    files = {
        "file": ("sample.pdf", BytesIO(b"%PDF-1.4 sample"), "application/pdf"),
    }
    data = {
        "name": "Test Regulation",
        "jurisdiction": "IN",
        "authority": "MCA",
        "category": "Company Law",
        "tags": '{"type":"test"}',
        "effective_date": "2026-01-01",
    }
    r = client.post("/api/v1/regulations/upload", data=data, files=files, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    reg_id = r.json()["id"]

    r2 = client.get("/api/v1/regulations", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert any(x["id"] == reg_id for x in r2.json())

    r3 = client.get(f"/api/v1/regulations/{reg_id}", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    body = r3.json()
    assert body["id"] == reg_id
    assert body["name"] == "Test Regulation"
    assert body["versions"][0]["version_number"] == 1

