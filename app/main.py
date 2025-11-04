from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .prisma_client import connect as prisma_connect, disconnect as prisma_disconnect
from .seed import seed_static
from .routers import health, auth, teams, domains


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="1.0.0")

    # CORS
    origins = settings.api_cors_origins or []
    # Always allow common dev ports and chrome extension
    origins.extend([
        "chrome-extension://*",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:8001",
    ])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(teams.router)
    app.include_router(domains.router)

    return app


app = create_app()


@app.on_event("startup")
async def on_startup():
    await prisma_connect()
    await seed_static()


@app.on_event("shutdown")
async def on_shutdown():
    await prisma_disconnect()


