import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import attendance, auth, gyms, progress, training, workouts
from app.core.config import get_settings
from app.core.errors import install_error_handlers

API_PREFIX = "/api/v1"

logger = logging.getLogger("gympulse")


async def catch_unexpected_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": "server_error", "message": "Something went wrong on the server."}
            },
        )


def create_app() -> FastAPI:
    app = FastAPI(title="GymPulse API", version="0.1.0")
    # Added before CORS so it sits inside it: an unexpected crash still gets CORS headers,
    # and the browser shows "server error" instead of a misleading "no connection".
    app.add_middleware(BaseHTTPMiddleware, dispatch=catch_unexpected_errors)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(gyms.router, prefix=API_PREFIX)
    app.include_router(attendance.router, prefix=API_PREFIX)
    app.include_router(training.router, prefix=API_PREFIX)
    app.include_router(workouts.router, prefix=API_PREFIX)
    app.include_router(workouts.summary_router, prefix=API_PREFIX)
    app.include_router(progress.router, prefix=API_PREFIX)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
