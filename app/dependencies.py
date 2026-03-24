import uuid
from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Mock dependency that simulates checking a token and returning user data.
    Will be replaced with proper JWT verification.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.models.user import User

    # Map token to deterministic guest user for test/dev environment
    if token == "dummy-token":
        email = "dummy-user@example.com"
        first_name = "Dummy"
        last_name = "User"
    else:
        email = f"user-{token}@example.com"
        first_name = "Token"
        last_name = "User"

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            user_id=uuid.uuid4(),
            email=email,
            password_hash="not-used",
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "user_id": user.user_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
