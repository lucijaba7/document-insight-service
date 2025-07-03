import logging
from functools import lru_cache
from typing import List, Tuple

from transformers import Pipeline, pipeline

from app.services.session import get_session_text

logger = logging.getLogger(__name__)

MODEL_NAME = "distilbert-base-uncased-distilled-squad"


@lru_cache()
def get_qa_pipeline() -> Pipeline:
    logger.info(f"Loading QA model {MODEL_NAME}")

    return pipeline("question-answering", model=MODEL_NAME, tokenizer=MODEL_NAME)


def run_qa_model(question: str, contexts: List[str]) -> Tuple[str, float]:
    qa = get_qa_pipeline()
    context = "\n\n".join(contexts)

    try:
        out = qa(question=question, context=context)
        answer = out.get("answer", "").strip()
        score = float(out.get("score", 0.0))

        return answer, score
    except Exception:
        logger.exception("QA pipeline inference failed")

        raise


def run_qa_pipeline(session_id: str, question: str) -> Tuple[str, float]:
    page_texts = get_session_text(session_id).page_texts

    answer, score = run_qa_model(question, page_texts)
    logger.info(
        f"QA pipeline complete for session {session_id}. "
        f"Answer: {answer}, Score: {score}"
    )
    return answer, score
