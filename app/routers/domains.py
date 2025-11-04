from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..prisma_client import prisma
from .. import schemas

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("", response_model=list[schemas.Domain])
async def get_domains(user=Depends(get_current_user)):
    """Get all domains for the current user"""
    user_domains = await prisma.user_domains.find_many(
        where={"user_id": user.id},
        include={"domain": True}
    )
    return [schemas.Domain.model_validate(ud.domain) for ud in user_domains if ud.domain]


@router.get("/all", response_model=list[schemas.Domain])
async def get_all_domains(user=Depends(get_current_user)):
    """Get all active domains (for selection UI)"""
    domains = await prisma.domains.find_many(where={"is_active": True})
    return [schemas.Domain.model_validate(d) for d in domains]

