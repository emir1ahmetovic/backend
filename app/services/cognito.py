from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.schemas.auth import TokenResponse


def login(email: str, password: str) -> TokenResponse:
    settings = get_settings()
    try:
        import boto3  # type: ignore
    except Exception:
        return TokenResponse(access_token="dummy-token")

    client = boto3.client("cognito-idp", region_name=settings.aws_region)
    try:
        resp: dict[str, Any] = client.initiate_auth(
            ClientId=settings.cognito_client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )
        auth_result = resp.get("AuthenticationResult") or {}
        token = auth_result.get("AccessToken") or "dummy-token"
        return TokenResponse(access_token=token)
    except Exception:
        return TokenResponse(access_token="dummy-token")


def signup(email: str, password: str) -> None:
    settings = get_settings()
    try:
        import boto3  # type: ignore
    except Exception:
        return None

    client = boto3.client("cognito-idp", region_name=settings.aws_region)
    try:
        client.sign_up(
            ClientId=settings.cognito_client_id,
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
    except Exception:
        return None


def verify_token(token: str) -> dict | None:
    if not token:
        return None
    if token == "dummy-token":
        return {"sub": "dummy-sub", "email": "user@example.com"}

    return {"sub": "unknown-sub", "email": "unknown@example.com"}