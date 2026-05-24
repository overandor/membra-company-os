"""
Overmanifold FastAPI Server
Production-ready API server with middleware, error handling, and monitoring.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import time
import uuid

from overmanifold.api.health import router as health_router
from overmanifold.infrastructure.logging_config import (
    setup_logging,
    get_logger,
    get_error_handler,
    RequestLogger,
    REQUEST_ID
)
from overmanifold.infrastructure.config import get_config
from overmanifold.validation.validators import validator


# Setup logging
setup_logging()
logger = get_logger("api_server")
error_handler = get_error_handler(logger)
request_logger = RequestLogger(logger)
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Overmanifold API server", extra={
        "environment": config.environment.value,
        "debug": config.debug,
        "log_level": config.log_level
    })
    
    yield
    
    # Shutdown
    logger.info("Shutting down Overmanifold API server")


# Create FastAPI application
app = FastAPI(
    title="Overmanifold Protocol API",
    description="Civilization-scale cryptographic-economic coordination architecture",
    version="1.0.0",
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None,
    openapi_url="/openapi.json" if config.debug else None,
    lifespan=lifespan
)


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Request/response logging middleware."""
    start_time = time.time()
    
    # Log request
    request_id = request_logger.log_request(
        method=request.method,
        path=str(request.url.path),
        headers=dict(request.headers),
        query_params=dict(request.query_params)
    )
    
    # Set request ID in context
    REQUEST_ID.set(request_id)
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        request_logger.log_response(
            request_id=request_id,
            status_code=response.status_code,
            response_time_ms=process_time * 1000,
            response_length=response.headers.get("content-length")
        )
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        
        # Log error
        request_logger.log_error(request_id, e, {
            "method": request.method,
            "path": str(request.url.path),
            "process_time_ms": process_time * 1000
        })
        
        # Return error response
        error_response = error_handler.handle_internal_error(e, {
            "request_id": request_id,
            "path": str(request.url.path)
        })
        
        return JSONResponse(
            status_code=error_response["status_code"],
            content=error_response
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": logger.logger.logger.handlers[0].formatter.format(
                logger.logger.makeRecord(
                    logger.logger.name, 40, '', 0, str(exc.detail), (), None, False
                )
            ) if logger.logger.logger.handlers else None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    error_response = error_handler.handle_internal_error(exc, {
        "path": str(request.url.path),
        "method": request.method
    })
    
    return JSONResponse(
        status_code=error_response["status_code"],
        content=error_response
    )


# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Overmanifold Protocol API",
        "version": "1.0.0",
        "status": "operational",
        "environment": config.environment.value,
        "documentation": "/docs" if config.debug else "Documentation disabled in production",
        "health": "/health"
    }


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://overmanifold.io/logo.png"
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "overmanifold.api.server:app",
        host=config.api.host,
        port=config.api.port,
        workers=config.api.workers if not config.debug else 1,
        reload=config.debug,
        log_level=config.log_level.lower(),
        access_log=True
    )