import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from app.internal.logging import configure_logging
from app.routers.ask import router as ask_router
from app.routers.upload import router as upload_router

logger = logging.getLogger(__name__)

configure_logging()

app = FastAPI()
app.add_middleware(CorrelationIdMiddleware)

app.include_router(upload_router)
app.include_router(ask_router)


@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code} {exc.detail}")
    return await http_exception_handler(request, exc)
