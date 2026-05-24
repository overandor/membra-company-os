"""User, auth, session schemas."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = "viewer"
    wallet_address: Optional[str] = None
    is_active: bool = True
    metadata_json: Optional[Dict[str, Any]] = {}


class UserCreate(UserBase):
    password: Optional[str] = None


class UserRead(UserBase):
    id: str
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None


class LoginRequest(BaseModel):
    wallet_address: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    signature: Optional[str] = None
    nonce: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserRead] = None


class NonceResponse(BaseModel):
    nonce: str
    expires_at: datetime


class AuditLogRead(BaseModel):
    id: str
    event_type: str
    user_id: Optional[str] = None
    wallet_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}
    proof_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
