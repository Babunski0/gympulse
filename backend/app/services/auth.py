from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    verify_password,
)
from app.models import AuthSession, User
from app.schemas.auth import TokenPair

_INVALID_LOGIN = AppError(401, "invalid_credentials", "Email or password is incorrect.")
# Verifying against a real hash keeps login timing similar for unknown emails.
_DUMMY_HASH = hash_password("timing-equalizer")


def register(db: Session, email: str, password: str, full_name: str) -> User:
    user = User(email=email.lower(), password_hash=hash_password(password), full_name=full_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "email_taken", "An account with this email already exists.") from None
    return user


def _issue_tokens(db: Session, user: User) -> TokenPair:
    s = get_settings()
    refresh = new_refresh_token()
    auth_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh),
        expires_at=datetime.now(UTC) + timedelta(days=s.refresh_token_days),
    )
    db.add(auth_session)
    db.flush()
    access = create_access_token(user.id, auth_session.id)
    db.commit()
    return TokenPair(
        access_token=access, refresh_token=refresh, expires_in=s.access_token_minutes * 60
    )


def login(db: Session, email: str, password: str) -> TokenPair:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        verify_password(password, _DUMMY_HASH)
        raise _INVALID_LOGIN
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise _INVALID_LOGIN
    return _issue_tokens(db, user)


def refresh(db: Session, refresh_token: str) -> TokenPair:
    """Rotate: the presented refresh token is revoked and a new session/token pair is issued."""
    auth_session = db.scalar(
        select(AuthSession)
        .where(AuthSession.refresh_token_hash == hash_token(refresh_token))
        .with_for_update()
    )
    now = datetime.now(UTC)
    if auth_session is None or auth_session.revoked_at is not None or auth_session.expires_at < now:
        raise AppError(401, "invalid_refresh_token", "Refresh token is invalid or expired.")
    auth_session.revoked_at = now
    user = db.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        db.commit()
        raise AppError(401, "invalid_refresh_token", "Refresh token is invalid or expired.")
    return _issue_tokens(db, user)


def logout(db: Session, auth_session: AuthSession) -> None:
    auth_session.revoked_at = datetime.now(UTC)
    db.commit()
