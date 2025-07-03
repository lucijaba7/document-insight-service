import logging

from app.internal.auth import create_session_token
from app.models.upload import UploadResponse
from app.services.upload import create_document_session
from fastapi import APIRouter, File, UploadFile, status

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a PDF, extract text, and start a session",
)
async def upload_and_extract(file: UploadFile = File(...)):
    session = await create_document_session(file)
    pages = session.page_texts
    token = create_session_token(session.session_id)

    return UploadResponse(
        session_token=token,
        session_id=session.session_id,
        text=pages,
    )
