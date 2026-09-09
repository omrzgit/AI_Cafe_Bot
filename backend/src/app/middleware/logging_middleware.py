import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({elapsed:.1f}ms)"
    )
    return response
