from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


async def app_exception_handler(request: Request, exc: AppException):

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def generic_exception_handler(request: Request, exc: Exception):

    logger.error(f"Unhandled error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )