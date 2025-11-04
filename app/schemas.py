from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class Team(BaseModel):
    id: str
    name: str
    external_ref: Optional[str] = None
    is_active: bool

    model_config = dict(from_attributes=True)


class Domain(BaseModel):
    id: str
    key: str
    name: str
    parent_domain_id: Optional[str] = None
    is_active: bool

    model_config = dict(from_attributes=True)


class User(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = dict(from_attributes=True)


class UserWithContext(User):
    teams: List[Team] = []
    domains: List[Domain] = []


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserWithContext


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class ValidateTokenRequest(BaseModel):
    token: str


class ValidateTokenResponse(BaseModel):
    valid: bool
    user: Optional[UserWithContext] = None
    error: Optional[str] = None
from __future__ import annotations

from prisma import Prisma

prisma = Prisma()


async def connect():
    if not prisma.is_connected():
        await prisma.connect()


async def disconnect():
    if prisma.is_connected():
        await prisma.disconnect()

