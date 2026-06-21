"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from app.database import init_db

app = FastAPI(
    title="youtube_sum",
    description="YouTube Summarization Agent — summarize videos with local LLMs",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["api"])


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


if __name__ == "__main__":
    import uvicorn

    from app.config import settings

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
