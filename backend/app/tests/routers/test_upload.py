from unittest.mock import patch

from app.main import app
from app.models.domain import DocumentSession
from fastapi.testclient import TestClient

client = TestClient(app)


def make_pdf_bytes():
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


@patch("app.routers.upload.create_document_session")
@patch("app.routers.upload.create_session_token")
def test_upload_endpoint_success(mock_token, mock_service):
    dummy_session = DocumentSession(session_id="sess123", page_texts=["a", "b"])
    mock_service.return_value = dummy_session
    mock_token.return_value = "jwt_token"

    files = {"file": ("test.pdf", make_pdf_bytes(), "application/pdf")}

    resp = client.post("/upload", files=files)

    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "session_token": "jwt_token",
        "session_id": "sess123",
        "text": ["a", "b"],
    }
    mock_service.assert_called_once()
    mock_token.assert_called_once_with("sess123")


def test_upload_endpoint_bad_file_type():
    files = {"file": ("foo.txt", b"hello", "text/plain")}
    resp = client.post("/upload", files=files)
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]
