import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    return TestClient(app)


def test_ask_missing_token(client):
    response = client.post("/ask", data={"question": "What is this?"})
    assert response.status_code == 403 or response.status_code == 401


def test_ask_invalid_token(client):
    response = client.post(
        "/ask",
        data={"question": "What is this?"},
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


def test_ask_empty_question(client):
    response = client.post(
        "/ask",
        data={"question": ""},
        headers={"Authorization": "Bearer validtoken"},
    )

    assert response.status_code in (404, 422, 401)
