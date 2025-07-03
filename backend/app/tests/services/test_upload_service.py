import pickle
from uuid import UUID

import pytest
from app.models.domain import DocumentSession
from app.services.upload import create_document_session
from fastapi import HTTPException


class DummyUploadFile:
    def __init__(self, filename: str, content_type: str, data: bytes):
        self.filename = filename
        self.content_type = content_type
        self._data = data

    async def read(self) -> bytes:
        return self._data


class DummyPage:
    def __init__(self, text: str):
        self._text = text

    def get_text(self):
        return self._text


class DummyDoc:
    def __init__(self, pages):
        self._pages = pages

    def __iter__(self):
        return iter(self._pages)

    def close(self):
        pass


@pytest.mark.anyio
async def test_invalid_content_type(mocker):
    fake_file = DummyUploadFile("foo.txt", "text/plain", b"not a pdf")
    with pytest.raises(HTTPException) as exc:
        await create_document_session(fake_file)
    assert exc.value.status_code == 400
    assert "Invalid file type" in exc.value.detail


@pytest.mark.anyio
async def test_create_session_success(mocker):
    dummy_bytes = b"%PDF-1.4 dummy content"
    fake_file = DummyUploadFile("foo.pdf", "application/pdf", dummy_bytes)

    pages = [DummyPage("page1"), DummyPage("page2")]
    dummy_doc = DummyDoc(pages)
    mocker.patch("app.services.upload.fitz.open", return_value=dummy_doc)

    calls = []
    stored_sessions = {}

    def fake_setex(name, time, value):
        calls.append((name, time, value))
        stored_sessions[name] = value

    def fake_get(name):
        return stored_sessions.get(name)

    mocker.patch("app.services.session.redis_client.setex", side_effect=fake_setex)
    mocker.patch("app.services.session.redis_client.get", side_effect=fake_get)

    session = await create_document_session(fake_file)

    assert isinstance(session, DocumentSession)
    UUID(session.session_id, version=4)
    assert session.page_texts == ["page1", "page2"]

    assert len(calls) == 1
    name, time_arg, pickled = calls[0]
    assert name == f"session:{session.session_id}"
    assert isinstance(time_arg, int) and time_arg > 0

    stored = pickle.loads(pickled)
    assert stored == ["page1", "page2"]
