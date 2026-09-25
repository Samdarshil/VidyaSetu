from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Resolves the JWT to a real User row on every request.

    This is the enforcement point: every protected router depends on this
    (or require_role below), so authorization happens on the backend, not
    just by hiding buttons in the frontend.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_error
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_role(*allowed_roles: str):
    """Usage: Depends(require_role("industry", "admin"))

    Raises 403 if the authenticated user's role isn't in allowed_roles.
    A student token can never reach an industry- or admin-only endpoint,
    regardless of what the frontend shows.
    """
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not permitted to access this resource.",
            )
        return user
    return checker
