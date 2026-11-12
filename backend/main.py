"""Main entry point for Cart Detective FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import router as api_router
from backend.config import settings
from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    yield


app = FastAPI(
    title="Cart Detective API",
    description="Autonomous product research and verification engine.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "cart-detective",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }
