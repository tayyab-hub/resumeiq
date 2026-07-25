"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.error_codes import RATE_LIMITED, TOO_MANY_ATTEMPTS
from app.core.exceptions import AppError
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import normalise_email
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.security.dependencies import client_ip, get_current_user
from app.security.rate_limit import SECONDS_PER_HOUR, limiter
from app.security.tokens import create_access_token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])

REFRESH_COOKIE_NAME = "resumeiq_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        path=REFRESH_COOKIE_PATH,
        httponly=True,  # unreadable by JavaScript, so an XSS payload cannot steal it
        secure=settings.is_production,
        # The frontend and API are on different registrable domains in
        # production, so the cookie must be SameSite=None. That is safe only
        # because Secure is set and the CORS origin allowlist is strict.
        samesite="none" if settings.is_production else "lax",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def _login_response(db: Session, response: Response, user: User) -> TokenResponse:
    access_token, expires_in = create_access_token(user.id)
    raw_refresh, max_age = auth_service.issue_refresh_token(db, user.id)
    _set_refresh_cookie(response, raw_refresh, max_age)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserPublic.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    ip_key = f"register:{client_ip(request)}"
    retry_after = limiter.check(ip_key, settings.register_max_per_hour, SECONDS_PER_HOUR)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
        raise AppError(RATE_LIMITED, retry_after=retry_after)

    limiter.hit(ip_key, SECONDS_PER_HOUR)
    user = auth_service.register(
        db, full_name=payload.full_name, email=payload.email, password=payload.password
    )
    return _login_response(db, response, user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    # Keyed on both email and IP: one attacker cannot lock out an account from
    # many addresses, and one address cannot spray many accounts.
    email_key = f"login:email:{normalise_email(payload.email)}"
    ip_key = f"login:ip:{client_ip(request)}"
    window = settings.login_window_seconds

    for key in (email_key, ip_key):
        retry_after = limiter.check(key, settings.login_max_attempts, window)
        if retry_after is not None:
            response.headers["Retry-After"] = str(retry_after)
            raise AppError(TOO_MANY_ATTEMPTS, retry_after=retry_after)

    try:
        user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    except AppError:
        # Only failures are counted, so a legitimate user is never throttled.
        limiter.hit(email_key, window)
        limiter.hit(ip_key, window)
        raise

    limiter.reset(email_key)
    limiter.reset(ip_key)
    return _login_response(db, response, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    user = auth_service.redeem_refresh_token(db, raw_token)
    # Rotate: the presented token is revoked and a new one issued, so a stolen
    # refresh token has a short useful life.
    auth_service.revoke(db, raw_token)
    return _login_response(db, response, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    auth_service.revoke(db, request.cookies.get(REFRESH_COOKIE_NAME))
    _clear_refresh_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
