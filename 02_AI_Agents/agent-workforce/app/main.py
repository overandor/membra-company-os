from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from prometheus_client import make_asgi_app
import sentry_sdk
from app.core.config import settings
from app.core.logging import get_logger
from app.routers import agents, users, streaming, schedules
from app.db.base import init_db

logger = get_logger("main")

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup", env=settings.app_env)
    await init_db()
    logger.info("db_initialized")
    yield
    logger.info("app_shutdown")

app = FastAPI(
    title="Agent Workforce Platform",
    description="A proprietary multi-agent system with 30 LLM agents featuring Stripe billing, Twilio notifications, Email, GitHub repo creation, and Vercel deployment capabilities.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
app.include_router(agents.router)
app.include_router(users.router)
app.include_router(streaming.router)
app.include_router(schedules.router)

@app.get("/dashboard", response_class=FileResponse)
async def dashboard():
    return "app/static/dashboard.html"

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "agents_count": 30,
        "endpoints": {
            "docs": "/docs",
            "agents": "/agents/",
            "metrics": "/metrics",
        },
        "status": "operational",
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "env": settings.app_env}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
