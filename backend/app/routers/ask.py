import logging

from app.internal.auth import get_session_id_from_token
from app.models.ask import AskRequest, MultiAskResponse, SingleModelAnswer
from app.pipelines.ner import extract_entities
from app.pipelines.qa import run_qa_pipeline
from app.pipelines.rag import run_rag_pipeline
from fastapi import APIRouter, Depends, Form, status
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/ask",
    response_model=MultiAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question over an existing document session",
)
async def ask(
    req: AskRequest = Form(..., description="Your question text"),
    creds: HTTPAuthorizationCredentials = Depends(get_session_id_from_token),
):
    session_id = creds

    answer, score = run_qa_pipeline(session_id, req.question)

    simple_qa = SingleModelAnswer(
        model_name="Full-Context QA (DistilBERT-SQuAD)",
        description="Runs a DistilBERT-based QA model directly over the entire session text "
        "concatenated into one context.",
        answer=answer,
        score=score,
        entities=extract_entities(answer),
    )

    answer, score = run_rag_pipeline(session_id, req.question)

    rag_answer = SingleModelAnswer(
        model_name="RAG-Augmented QA (MiniLM + DistilBERT-SQuAD)",
        description="First embeds and retrieves the top-k most relevant text chunks via "
        "a MiniLM embedding + FAISS index, then runs the same DistilBERT-SQuAD "
        "QA model on those chunks to produce a more focused answer.",
        answer=answer,
        score=score,
        entities=extract_entities(answer),
    )

    return MultiAskResponse(results=[simple_qa, rag_answer])
