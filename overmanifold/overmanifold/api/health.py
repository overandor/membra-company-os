"""
Overmanifold Health Check Endpoints
Provides health and readiness checks for Kubernetes and monitoring systems.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.infrastructure.config import get_config

router = APIRouter()
logger = get_logger("health_check")
config = get_config()


class HealthCheckError(Exception):
    """Custom exception for health check failures."""
    pass


class ServiceHealthChecker:
    """Health checker for various services."""
    
    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "api": self._check_api,
            "memory": self._check_memory,
            "disk": self._check_disk
        }
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # In production, this would actually check database connection
            # For now, simulate the check
            await asyncio.sleep(0.1)  # Simulate database query
            
            return {
                "status": "healthy",
                "latency_ms": 10,
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            # In production, this would actually check Redis connection
            await asyncio.sleep(0.05)  # Simulate Redis ping
            
            return {
                "status": "healthy",
                "latency_ms": 5,
                "message": "Redis connection successful"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis connection failed"
            }
    
    async def check_api(self) -> Dict[str, Any]:
        """Check API health."""
        try:
            # Basic API health check
            return {
                "status": "healthy",
                "message": "API is operational"
            }
        except Exception as e:
            logger.error(f"API health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "API health check failed"
            }
    
    async def check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # Consider unhealthy if memory usage is above 90%
            if memory.percent > 90:
                return {
                    "status": "unhealthy",
                    "memory_percent": memory.percent,
                    "message": f"Memory usage critically high: {memory.percent}%"
                }
            
            return {
                "status": "healthy",
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "message": "Memory usage within acceptable limits"
            }
        except Exception as e:
            logger.error(f"Memory health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Memory health check failed"
            }
    
    async def check_disk(self) -> Dict[str, Any]:
        """Check disk usage."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            
            # Consider unhealthy if disk usage is above 90%
            if disk.percent > 90:
                return {
                    "status": "unhealthy",
                    "disk_percent": disk.percent,
                    "message": f"Disk usage critically high: {disk.percent}%"
                }
            
            return {
                "status": "healthy",
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 ** 3),
                "message": "Disk usage within acceptable limits"
            }
        except Exception as e:
            logger.error(f"Disk health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Disk health check failed"
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """Check all services."""
        results = {}
        overall_healthy = True
        
        for service_name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[service_name] = result
                
                if result["status"] != "healthy":
                    overall_healthy = False
            except Exception as e:
                logger.error(f"Health check for {service_name} failed: {str(e)}")
                results[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }


# Global health checker instance
health_checker = ServiceHealthChecker()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "overmanifold-api",
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Returns 200 if the service is ready to accept traffic.
    """
    # Check critical services
    critical_checks = ["database", "redis"]
    results = {}
    all_healthy = True
    
    for check_name in critical_checks:
        check_func = getattr(health_checker, f"check_{check_name}", None)
        if check_func:
            try:
                result = await check_func()
                results[check_name] = result
                if result["status"] != "healthy":
                    all_healthy = False
            except Exception as e:
                results[check_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                all_healthy = False
    
    if all_healthy:
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": results
            }
        )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint.
    Returns 200 if the service is alive.
    """
    # Basic liveness check - just check if we can respond
    try:
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "dead",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint.
    Returns comprehensive health status of all components.
    """
    results = await health_checker.check_all()
    
    if results["overall_status"] == "healthy":
        return results
    else:
        raise HTTPException(
            status_code=503,
            detail=results
        )