import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models import AuthSession, User
from app.models.user import Role

_bearer = HTTPBearer(auto_error=False)

DB = Annotated[Session, Depends(get_db)]


def _unauthorized() -> AppError:
    return AppError(401, "unauthorized", "Missing, invalid or expired access token.")


def get_auth_context(
    db: DB, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> tuple[User, AuthSession]:
    if creds is None:
        raise _unauthorized()
    payload = decode_access_token(creds.credentials)
    if payload is None:
        raise _unauthorized()
    auth_session = db.get(AuthSession, uuid.UUID(payload["sid"]))
    if auth_session is None or auth_session.revoked_at is not None:
        raise _unauthorized()
    user = db.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user, auth_session


def get_current_user(ctx: Annotated[tuple[User, AuthSession], Depends(get_auth_context)]) -> User:
    return ctx[0]


def require_gym_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != Role.GYM_ADMIN:
        raise AppError(403, "forbidden", "Only gym administrators can do this.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_gym_admin)]
