"""Common Pydantic schemas for MEMBRA CompanyOS."""
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class IDResponse(BaseModel):
    id: str


class HealthCheck(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str
    services: Dict[str, str] = {}
