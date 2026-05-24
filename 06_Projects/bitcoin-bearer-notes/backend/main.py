"""CoinPack Redemption API - FastAPI Application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time

from core.config import settings
from models.database import init_db
from api.routes import router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting CoinPack API", version="0.1.0", env=settings.ENV)
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down CoinPack API")


app = FastAPI(
    title="CoinPack Redemption API",
    description="Bitcoin-backed denominated bearer notes on Solana",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Request/response logging."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
        client_ip=request.client.host if request.client else None,
    )
    return response


# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred"},
    )


# Routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "CoinPack Redemption API",
        "version": "0.1.0",
        "description": "Bitcoin-backed denominated bearer notes on Solana",
        "docs": "/docs" if settings.DEBUG else None,
        "endpoints": {
            "health": "/api/v1/health",
            "notes": "/api/v1/notes",
            "claims": "/api/v1/claims",
            "reserves": "/api/v1/reserves",
            "stats": "/api/v1/stats",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
