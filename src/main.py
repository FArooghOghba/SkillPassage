"""Main FastAPI application initialization."""
from fastapi import FastAPI

from src.api.router import router as api_router


app = FastAPI(
    title="SkillPassage",
    description="FastAPI-based online marketplace platform for professionals.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


app.include_router(router=api_router)
