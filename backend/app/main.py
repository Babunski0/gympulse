from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import attendance, auth, gyms
from app.core.config import get_settings
from app.core.errors import install_error_handlers

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(title="GymPulse API", version="0.1.0")
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

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
