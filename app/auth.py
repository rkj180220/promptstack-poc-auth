from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError
import requests
from .config import settings
from .prisma_client import prisma


_jwks_cache: dict | None = None


def _load_jwks() -> dict | None:
    """Load JWKS for OIDC token validation"""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    if settings.oidc_jwks_url:
        try:
            resp = requests.get(settings.oidc_jwks_url, timeout=5)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            return _jwks_cache
        except Exception:
            return None
    return None


async def _get_or_create_user(email: str, name: str):
    """Get existing user or create new one with default team and domain"""
    user = await prisma.users.find_unique(where={"email": email})
    if user:
        if name and user.name != name:
            user = await prisma.users.update(where={"id": user.id}, data={"name": name})
        return user

    # Create new user
    user = await prisma.users.create(data={"email": email, "name": name or email.split("@")[0]})

    # Ensure default team and domain
    team = await prisma.teams.find_unique(where={"name": "General"})
    if team:
        await prisma.team_memberships.upsert(
            where={"user_id_team_id": {"user_id": user.id, "team_id": team.id}},
            data={"create": {"user_id": user.id, "team_id": team.id}, "update": {}},
        )

    eng = await prisma.domains.find_unique(where={"key": "engineering"})
    if eng:
        await prisma.user_domains.upsert(
            where={"user_id_domain_id": {"user_id": user.id, "domain_id": eng.id}},
            data={"create": {"user_id": user.id, "domain_id": eng.id}, "update": {}},
        )

    return user


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
    x_user_name: Optional[str] = Header(None),
):
    """
    Get current user from dev headers or JWT token.
    Supports local JWT and OIDC JWT.
    """
    # Dev header mode
    if settings.allow_dev_headers and (x_user_email or x_user_name):
        if not x_user_email:
            raise HTTPException(status_code=400, detail="X-User-Email required")
        return await _get_or_create_user(x_user_email, x_user_name or x_user_email)

    # JWT mode - try our local JWT first, then OIDC
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]

        # Try local JWT first
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            email = payload.get("sub")
            if email:
                user = await prisma.users.find_unique(where={"email": email})
                if user:
                    return user
        except Exception:
            pass

        # Fall back to OIDC if configured
        if settings.oidc_issuer:
            try:
                jwks = _load_jwks()
                options = {"verify_aud": bool(settings.oidc_audience)}
                payload = jwt.decode(
                    token,
                    jwks,
                    options=options,
                    audience=settings.oidc_audience,
                    issuer=settings.oidc_issuer,
                )
                email = payload.get("email")
                name = payload.get("name") or email
                if not email:
                    raise HTTPException(status_code=401, detail="Token missing email claim")
                return await _get_or_create_user(email, name)
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid token")

    # Anonymous not allowed
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def validate_token(token: str) -> dict:
    """
    Validate a JWT token and return user context.
    Returns dict with 'valid', 'user', and 'error' keys.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email = payload.get("sub")
        if not email:
            return {"valid": False, "user": None, "error": "Token missing subject"}

        user = await prisma.users.find_unique(where={"email": email})
        if not user:
            return {"valid": False, "user": None, "error": "User not found"}

        return {"valid": True, "user": user, "error": None}
    except JWTError as e:
        return {"valid": False, "user": None, "error": str(e)}
    except Exception as e:
        return {"valid": False, "user": None, "error": str(e)}

