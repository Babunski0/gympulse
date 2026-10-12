from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import DB, CurrentUser, get_auth_context
from app.core.rate_limit import rate_limited
from app.schemas.auth import (
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokenPair,
    UserOut,
    UserUpdateIn,
)
from app.services import auth as auth_service

router = APIRouter(tags=["auth"])


@router.post(
    "/auth/register",
    status_code=201,
    response_model=UserOut,
    dependencies=[Depends(rate_limited("auth"))],
)
def register(body: RegisterIn, db: DB):
    return auth_service.register(db, body.email, body.password, body.full_name)


@router.post("/auth/login", response_model=TokenPair, dependencies=[Depends(rate_limited("auth"))])
def login(body: LoginIn, db: DB):
    return auth_service.login(db, body.email, body.password)


@router.post(
    "/auth/refresh", response_model=TokenPair, dependencies=[Depends(rate_limited("auth"))]
)
def refresh(body: RefreshIn, db: DB):
    return auth_service.refresh(db, body.refresh_token)


@router.post("/auth/logout", status_code=204)
def logout(db: DB, ctx: Annotated[tuple, Depends(get_auth_context)]):
    auth_service.logout(db, ctx[1])
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def get_me(user: CurrentUser):
    return user


@router.put("/me", response_model=UserOut)
def update_me(body: UserUpdateIn, user: CurrentUser, db: DB):
    user.full_name = body.full_name.strip()
    db.commit()
    return user
