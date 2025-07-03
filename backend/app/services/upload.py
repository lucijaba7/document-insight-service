import logging

import fitz
from app.models.domain import DocumentSession
from app.services.session import cache_session_text, get_session_text
from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)


async def create_document_session(upload_file: UploadFile) -> DocumentSession:
    logger.info(f"Starting session creation for uploaded file {upload_file.filename}")

    if upload_file.content_type != "application/pdf":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a PDF.",
        )

    try:
        pdf_bytes = await upload_file.read()
    except Exception as e:
        logger.exception("Error reading upload")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read PDF: {e}",
        )

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_texts = [page.get_text() for page in doc]
        doc.close()
    except Exception as e:
        logger.exception("Error extracting text from PDF")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text: {e}",
        )

    session_id = cache_session_text(page_texts)

    logger.info(f"Created session {session_id} with {len(page_texts)} pages")

    return get_session_text(session_id)
