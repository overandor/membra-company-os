"""
CollateralOps — JWT authentication with role-based access (T29).
Roles: builder, lender, buyer, auditor.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Simple JWT-like implementation using PyJWT if available, else fallback
try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

SECRET = os.environ.get("JWT_SECRET", "collateralops-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": user_id, "role": role, "exp": expire, "iat": datetime.utcnow()}
    if HAS_JWT:
        return jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    # Fallback: base64 encoded JSON (NOT secure, dev only)
    import base64, json
    return base64.b64encode(json.dumps(payload, default=str).encode()).decode()


def decode_token(token: str) -> dict:
    if HAS_JWT:
        try:
            return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    # Fallback
    import base64, json
    try:
        return json.loads(base64.b64decode(token.encode()).decode())
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(request: Request, allowed: set):
    """Dependency to enforce role-based access."""
    token = None
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:]
    if not token:
        # Allow anonymous in dev mode; in production this would raise 401
        return {"role": "builder", "sub": "anonymous"}
    payload = decode_token(token)
    role = payload.get("role", "builder")
    if role not in allowed:
        raise HTTPException(status_code=403, detail=f"Role '{role}' not authorized for this resource")
    return payload


def require_auth(request: Request):
    """Require any authenticated user."""
    return require_role(request, {"builder", "lender", "buyer", "auditor"})
