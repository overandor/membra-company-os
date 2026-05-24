"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.services.auth import AuthService
from app.schemas.user import UserCreate, UserRead, LoginRequest, TokenResponse, NonceResponse
from app.core.security import generate_nonce

router = APIRouter()


@router.post("/nonce/{wallet_address}", response_model=NonceResponse)
def get_nonce(wallet_address: str):
    return NonceResponse(nonce=generate_nonce(), expires_at=None)


@router.post("/register", response_model=UserRead)
def register(data: UserCreate, db: Session = Depends(get_db)):
    svc = AuthService(db)
    try:
        return svc.register_user(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    svc = AuthService(db)
    result = svc.authenticate(data)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    svc = AuthService(db)
    new_access = svc.refresh_access_token(refresh_token)
    if not new_access:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {"access_token": new_access}
