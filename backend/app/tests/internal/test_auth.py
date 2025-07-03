import datetime

import pytest
from app.internal.auth import (
    create_session_token,
    get_session_id_from_token,
    get_subject_for_token_type,
)
from app.internal.config import config
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt


def test_create_session_token_contains_sub_and_type_and_exp():
    sid = "session123"
    token = create_session_token(sid)
    payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    assert payload["sub"] == sid
    assert payload["type"] == "session"

    exp = datetime.datetime.fromtimestamp(payload["exp"], datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = exp - now

    assert abs(delta.total_seconds() - config.SESSION_TTL) < 60


def test_get_subject_for_token_type_valid():
    sid = "abc-session"
    token = create_session_token(sid)
    assert get_subject_for_token_type(token, "session") == sid


def test_get_subject_for_token_type_expired(mocker):
    mocker.patch.object(config, "SESSION_TTL", -1)
    token = create_session_token("x")
    with pytest.raises(HTTPException) as exc:
        get_subject_for_token_type(token, "session")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Session token expired"


def test_get_subject_for_token_type_invalid_token():
    with pytest.raises(HTTPException) as exc:
        get_subject_for_token_type("not.a.valid.token", "session")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid session token"


def test_get_subject_for_token_type_missing_sub():
    sid = "missing-sub"
    token = create_session_token(sid)
    payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    del payload["sub"]
    bad_token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

    with pytest.raises(HTTPException) as exc:
        get_subject_for_token_type(bad_token, "session")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Token missing session_id"


def test_get_subject_for_token_type_wrong_type():
    sid = "wrong-type"

    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=config.SESSION_TTL
    )
    payload = {"sub": sid, "exp": expire, "type": "access"}
    bad_token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

    with pytest.raises(HTTPException) as exc:
        get_subject_for_token_type(bad_token, "session")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Wrong token type, expected 'session'"


@pytest.mark.anyio
async def test_get_session_id_from_token_valid():
    sid = "dep-session"
    token = create_session_token(sid)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    result = await get_session_id_from_token(creds)
    assert result == sid


@pytest.mark.anyio
async def test_get_session_id_from_token_invalid():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")
    with pytest.raises(HTTPException) as exc:
        await get_session_id_from_token(creds)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid session token"
