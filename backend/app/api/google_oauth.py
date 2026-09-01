"""
Google OAuth2 authentication endpoints.

Flow:
  1. GET /login/google          → redirect to Google consent screen
  2. GET /login/google/callback → exchange code, create user in Supabase + local DB, redirect to frontend with JWT
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config import settings
from app.core.database import get_db
from app.core.supabase import get_supabase_client
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Google endpoint constants ───────────────────────────────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# In-memory CSRF state store (use Redis / DB in production)
_oauth_states: dict[str, float] = {}

# In-memory auth code store (use Redis in production)
_auth_codes: dict[str, dict] = {}


def _cleanup_expired_states() -> None:
    """Remove state entries older than 10 minutes."""
    cutoff = datetime.now(timezone.utc).timestamp() - 600
    expired = [k for k, v in _oauth_states.items() if v < cutoff]
    for k in expired:
        _oauth_states.pop(k, None)


def _build_callback_url(request: Request) -> str:
    """Derive the callback URL from the incoming request."""
    return str(request.base_url).rstrip("/") + "/api/v1/login/google/callback"


# ── Initiate Google OAuth ───────────────────────────────────────────────
@router.get("/login/google")
def login_google(request: Request):
    """Redirect the user to Google's OAuth 2.0 consent screen."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured on the server")

    _cleanup_expired_states()

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(timezone.utc).timestamp()

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _build_callback_url(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


# ── Google OAuth callback ──────────────────────────────────────────────
@router.get("/login/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Handle the redirect from Google after user consent.
    Exchanges the authorization code for tokens, creates the user in
    Supabase (admin API) and the local DB, then redirects to the frontend
    with a signed JWT.
    """
    frontend = settings.FRONTEND_URL.rstrip("/")

    # ── Error from Google ───────────────────────────────────────────────
    if error:
        return RedirectResponse(url=f"{frontend}?auth_error={error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # ── CSRF check ──────────────────────────────────────────────────────
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    _oauth_states.pop(state, None)

    callback_url = _build_callback_url(request)

    # ── Exchange code for tokens ────────────────────────────────────────
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": callback_url,
                "grant_type": "authorization_code",
            },
        )

    if token_resp.status_code != 200:
        logger.error("Google token exchange failed: %s", token_resp.text)
        return RedirectResponse(url=f"{frontend}?auth_error=token_exchange_failed")

    access_token = token_resp.json().get("access_token")
    if not access_token:
        return RedirectResponse(url=f"{frontend}?auth_error=no_access_token")

    # ── Fetch Google user profile ───────────────────────────────────────
    async with httpx.AsyncClient() as client:
        info_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if info_resp.status_code != 200:
        return RedirectResponse(url=f"{frontend}?auth_error=userinfo_failed")

    google_user = info_resp.json()
    email: str = google_user.get("email", "")
    name: str = google_user.get("name", "")
    google_id: str = google_user.get("id", "")
    picture: str = google_user.get("picture", "")

    if not email:
        return RedirectResponse(url=f"{frontend}?auth_error=no_email_from_google")

    # ── Find or create user ─────────────────────────────────────────────
    local_user = db.query(User).filter(User.email == email).first()

    if local_user:
        # Existing user — update name if it was missing
        if name and not local_user.name:
            local_user.name = name
            db.commit()
        supabase_uid = local_user.supabase_uid
    else:
        # New user → create in Supabase + local DB
        supabase_uid = _create_supabase_user(email, name, google_id)
        local_user = User(
            supabase_uid=supabase_uid,
            email=email,
            name=name,
            preferred_language="en",
        )
        db.add(local_user)
        db.commit()
        db.refresh(local_user)

    # ── Issue a JWT (same shape as Supabase JWTs) ───────────────────────
    now = datetime.now(timezone.utc)
    jwt_payload = {
        "sub": supabase_uid,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
        "user_metadata": {
            "name": name,
            "picture": picture,
            "provider": "google",
        },
    }
    token = jwt.encode(jwt_payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

    # ── Redirect to frontend with auth code ───────────────────────────
    auth_code = secrets.token_urlsafe(32)
    _auth_codes[auth_code] = {
        "auth_token": token,
        "auth_name": name,
        "auth_email": email,
        "auth_user_id": local_user.id,
        "auth_provider": "google",
        "exp": datetime.now(timezone.utc).timestamp() + 60
    }
    
    params = urlencode({"auth_code": auth_code})
    return RedirectResponse(url=f"{frontend}?{params}")


class ExchangeRequest(BaseModel):
    code: str


@router.post("/auth/exchange")
def exchange_code(req: ExchangeRequest):
    """Exchange single-use auth code for JWT."""
    cutoff = datetime.now(timezone.utc).timestamp()
    expired = [k for k, v in _auth_codes.items() if v.get("exp", 0) < cutoff]
    for k in expired:
        _auth_codes.pop(k, None)

    if req.code not in _auth_codes:
        raise HTTPException(status_code=400, detail="Invalid or expired authorization code")

    data = _auth_codes.pop(req.code)
    data.pop("exp", None)
    return data


# ── Helpers ─────────────────────────────────────────────────────────────

def _create_supabase_user(email: str, name: str, google_id: str) -> str:
    """
    Create a user in Supabase via the admin API.
    Returns the Supabase UID (falls back to a generated UUID).
    """
    supa = get_supabase_client()
    if not supa:
        return str(uuid.uuid4())

    try:
        result = supa.auth.admin.create_user(
            {
                "email": email,
                "email_confirm": True,
                "user_metadata": {
                    "name": name,
                    "provider": "google",
                    "google_id": google_id,
                },
            }
        )
        return result.user.id
    except Exception as exc:
        exc_msg = str(exc).lower()
        if "already" in exc_msg or "exists" in exc_msg or "duplicate" in exc_msg:
            # User already exists in Supabase — try to find their UID
            return _find_supabase_uid_by_email(supa, email)
        logger.warning("Supabase user creation failed: %s", exc)
        return str(uuid.uuid4())


def _find_supabase_uid_by_email(supa, email: str) -> str:
    """Look up an existing Supabase user by email. Falls back to a generated UUID."""
    try:
        users = supa.auth.admin.list_users()
        for u in users:
            if hasattr(u, "email") and u.email == email:
                return u.id
    except Exception as exc:
        logger.warning("Supabase user lookup failed: %s", exc)
    return str(uuid.uuid4())

