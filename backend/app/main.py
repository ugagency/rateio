"""FastAPI entrypoint — Motor de Rateio Mutualiza."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import consultas, rateio
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Motor de Rateio — Mutualiza",
        version="0.1.0",
        description="API para cálculo do rateio mensal (LC 213/2025).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(rateio.router)
    app.include_router(consultas.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "repository": settings.rateio_repository}

    return app


app = create_app()
