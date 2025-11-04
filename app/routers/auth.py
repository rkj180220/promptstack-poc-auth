from __future__ import annotations

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext

from ..config import settings
from ..prisma_client import prisma
from ..auth import create_access_token, get_current_user, validate_token as validate_token_func
from .. import schemas

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user_with_context(user) -> schemas.UserWithContext:
    """Get user with teams and domains"""
    # Get teams
    memberships = await prisma.team_memberships.find_many(
        where={"user_id": user.id},
        include={"team": True}
    )
    teams = [schemas.Team.model_validate(m.team) for m in memberships if m.team]

    # Get domains
    user_domains = await prisma.user_domains.find_many(
        where={"user_id": user.id},
        include={"domain": True}
    )
    domains = [schemas.Domain.model_validate(ud.domain) for ud in user_domains if ud.domain]

    return schemas.UserWithContext(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        teams=teams,
        domains=domains
    )


@router.post("/register", response_model=schemas.LoginResponse)
async def register(register_data: schemas.RegisterRequest):
    """Register a new user"""
    # Check if user already exists
    existing_user = await prisma.users.find_unique(where={"email": register_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with hashed password
    password_hash = get_password_hash(register_data.password)
    user = await prisma.users.create(
        data={
            "email": register_data.email,
            "name": register_data.name,
            "password_hash": password_hash
        }
    )

    # Add to default team and domain
    team = await prisma.teams.find_unique(where={"name": "General"})
    if team:
        await prisma.team_memberships.create(
            data={"user_id": user.id, "team_id": team.id}
        )

    eng = await prisma.domains.find_unique(where={"key": "engineering"})
    if eng:
        await prisma.user_domains.create(
            data={"user_id": user.id, "domain_id": eng.id}
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    user_context = await get_user_with_context(user)

    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_context
    )


@router.post("/login", response_model=schemas.LoginResponse)
async def login(login_data: schemas.LoginRequest):
    """Login with email and password"""
    # Find user by email
    user = await prisma.users.find_unique(where={"email": login_data.email})

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    user_context = await get_user_with_context(user)

    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_context
    )


@router.post("/validate", response_model=schemas.ValidateTokenResponse)
async def validate_token(request: schemas.ValidateTokenRequest):
    """
    Validate a JWT token and return user context.
    This endpoint is used by other microservices to validate tokens.
    """
    result = await validate_token_func(request.token)

    if result["valid"] and result["user"]:
        user_context = await get_user_with_context(result["user"])
        return schemas.ValidateTokenResponse(
            valid=True,
            user=user_context,
            error=None
        )
    else:
        return schemas.ValidateTokenResponse(
            valid=False,
            user=None,
            error=result.get("error", "Invalid token")
        )


@router.get("/me", response_model=schemas.UserWithContext)
async def get_me(user=Depends(get_current_user)):
    """Get current user with context (teams and domains)"""
    return await get_user_with_context(user)

