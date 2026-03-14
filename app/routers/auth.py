from fastapi import APIRouter

from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.services import cognito


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    return cognito.login(email=payload.email, password=payload.password)


@router.post("/signup")
def signup(payload: SignupRequest) -> dict:
    cognito.signup(email=payload.email, password=payload.password)
    return {"ok": True}


@router.post("/logout")
def logout() -> dict:
    return {"ok": True}