import logging
import re
from typing import List, Tuple

import faiss
import numpy as np
from fastapi import HTTPException, status
from sentence_transformers import SentenceTransformer

from app.pipelines.qa import run_qa_model
from app.services.session import (
    cache_chunks_and_embeddings,
    get_session_text,
    has_cached_embeddings,
    load_cached_chunks,
    load_cached_embeddings,
)

logger = logging.getLogger(__name__)


MODEL_NAME = "all-MiniLM-L6-v2"
_EMBEDDER = SentenceTransformer(MODEL_NAME)
EMBED_DIM = _EMBEDDER.get_sentence_embedding_dimension()


def chunk_paragraphs(text: List[str]) -> List[str]:
    full_text = "\n\n".join(text)
    paras = [para.strip() for para in re.split(r"\n\s*\n+", full_text) if para.strip()]
    return paras


def embed_chunks(chunks: List[str]) -> np.ndarray:
    return _EMBEDDER.encode(
        chunks,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    idx = faiss.IndexFlatL2(EMBED_DIM)
    idx.add(embeddings)
    return idx


def retrieve_chunks(session_id: str, q_emb: np.ndarray, k: int = 5) -> List[str]:
    embeddings = load_cached_embeddings(session_id)
    idx = build_faiss_index(embeddings)
    _, ids = idx.search(q_emb, k)

    print(idx, ids)
    return load_cached_chunks(session_id, *ids)


def run_rag_pipeline(session_id: str, question: str, k: int = 5) -> Tuple[str, float]:
    logger.info(f"Starting RAG pipeline with modrl {MODEL_NAME}")

    if not has_cached_embeddings(session_id):
        full_text = get_session_text(session_id).page_texts
        chunks = chunk_paragraphs(full_text)
        embeddings = embed_chunks(chunks)
        cache_chunks_and_embeddings(session_id, chunks, embeddings)

    q_emb = _EMBEDDER.encode([question], convert_to_numpy=True)
    chunks = retrieve_chunks(session_id, q_emb, k)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No relevant chunks found for session {session_id}",
        )

    answer, score = run_qa_model(question, chunks)
    logger.info(f"RAG pipeline complete. Answer: {answer}, Score: {score}")
    return answer, score
