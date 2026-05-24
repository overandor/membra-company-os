"""MEMBRA CompanyOS — Authentication service with wallet + JWT."""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    verify_password, hash_password, create_access_token, create_refresh_token,
    decode_token, generate_nonce, verify_ethereum_signature, hash_proof
)
from app.core.logging import get_logger
from app.models.user import User, UserRole, Session as UserSession, AuditLog
from app.schemas.user import UserCreate, UserRead, LoginRequest, TokenResponse

settings = get_settings()
logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, data: UserCreate) -> UserRead:
        existing = self.db.query(User).filter(
            (User.email == data.email) | (User.wallet_address == data.wallet_address)
        ).first()
        if existing:
            raise ValueError("User already exists")
        user = User(
            wallet_address=data.wallet_address,
            email=data.email,
            hashed_password=hash_password(data.password) if data.password else None,
            role=UserRole(data.role) if data.role else UserRole.VIEWER,
            display_name=data.display_name,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self._audit("user_registered", user.id, {"wallet": data.wallet_address})
        return UserRead.model_validate(user)

    def authenticate(self, req: LoginRequest) -> Optional[TokenResponse]:
        if req.wallet_address and req.signature and req.nonce:
            if not verify_ethereum_signature(req.wallet_address, req.nonce, req.signature):
                return None
            user = self.db.query(User).filter(User.wallet_address == req.wallet_address).first()
            if not user:
                user = User(
                    wallet_address=req.wallet_address,
                    role=UserRole.VIEWER,
                    display_name=f"Wallet {req.wallet_address[:6]}...",
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            return self._issue_tokens(user)
        elif req.email and req.password:
            user = self.db.query(User).filter(User.email == req.email).first()
            if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
                return None
            return self._issue_tokens(user)
        return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = self.db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            return None
        return create_access_token({"sub": str(user.id), "role": user.role.value})

    def _issue_tokens(self, user: User) -> TokenResponse:
        access = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh = create_refresh_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead.model_validate(user),
        )

    def _audit(self, event_type: str, user_id: Optional[UUID], details: Dict[str, Any]):
        log = AuditLog(event_type=event_type, user_id=user_id, details=details)
        self.db.add(log)
        self.db.commit()
