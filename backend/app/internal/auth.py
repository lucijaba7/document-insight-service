import datetime
import logging
from typing import Literal

from app.internal.config import config
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

logger = logging.getLogger(__name__)

bearer = HTTPBearer()


def create_session_token(session_id: str) -> str:
    logger.info(f"Creating session token for id {session_id}")

    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=config.SESSION_TTL
    )
    payload = {"sub": session_id, "exp": expire, "type": "session"}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def get_subject_for_token_type(token: str, expected_type: Literal["session"]) -> str:
    logger.debug(f"Decoding token {token}")
    try:
        data = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Session token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sid = data.get("sub")
    if not sid:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token missing session_id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if data.get("type") != expected_type:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            f"Wrong token type, expected '{expected_type}'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Token validated: {sid}")
    return sid


async def get_session_id_from_token(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    return get_subject_for_token_type(creds.credentials, "session")
