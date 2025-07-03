import logging
import pickle
from typing import List
from uuid import uuid4

import numpy as np
from app.internal.redis import redis_client
from app.models.domain import DocumentSession
from fastapi import HTTPException, status

SESSION_TTL = 3600

SESSION_PREFIX = "session:"
EMBEDS_PREFIX = "embeds:"
CHUNKS_PREFIX = "chunks:"

logger = logging.getLogger(__name__)


def get_session_text(session_id: str) -> DocumentSession:
    key = f"{SESSION_PREFIX}{session_id}"
    logger.info(f"Fetching session text from Redis {key}")

    data = redis_client.get(key)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session expired or not found",
        )

    try:
        pages: list[str] = pickle.loads(data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Corrupted session data",
        )

    return DocumentSession(session_id=session_id, page_texts=pages)


def cache_chunks_and_embeddings(
    session_id: str, chunks: List[str], embeddings: np.ndarray
):
    chunks_key = f"{CHUNKS_PREFIX}{session_id}"

    redis_client.delete(chunks_key)

    mapping = {str(i): chunks[i] for i in range(len(chunks))}
    if mapping:
        redis_client.hset(chunks_key, mapping=mapping)
        redis_client.expire(chunks_key, SESSION_TTL)

    embeds_key = f"{EMBEDS_PREFIX}{session_id}"
    redis_client.setex(embeds_key, SESSION_TTL, pickle.dumps(embeddings))

    logger.info(f"Cached session {session_id}: {len(chunks)} chunks")


def load_cached_embeddings(session_id: str) -> np.ndarray:
    key = f"{EMBEDS_PREFIX}{session_id}"

    data = redis_client.get(key)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} expired or not found",
        )

    embeddings = pickle.loads(data)
    return embeddings


def load_cached_chunks(session_id: str, chunk_ids: List[int]) -> List[str]:
    key = f"{CHUNKS_PREFIX}{session_id}"

    results: List[str] = []
    for idx in chunk_ids:
        data = redis_client.hget(key, str(idx))
        if data:
            results.append(data.decode())

    logger.info(f"Finished loading chunks. Retrieved_count: {len(results)}")
    return results


def has_cached_embeddings(session_id: str) -> bool:
    key = f"{CHUNKS_PREFIX}{session_id}"

    return bool(redis_client.exists(key))


def cache_session_text(page_texts: List[str]) -> str:
    session_id = uuid4().hex
    key = f"{SESSION_PREFIX}{session_id}"

    logger.info(f"Creating new session cache entry for key: {key}")

    try:
        redis_client.setex(
            name=key,
            time=SESSION_TTL,
            value=pickle.dumps(page_texts),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create session: {e}",
        )

    return session_id
