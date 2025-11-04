from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..prisma_client import prisma
from .. import schemas

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[schemas.Team])
async def get_teams(user=Depends(get_current_user)):
    """Get all teams for the current user"""
    memberships = await prisma.team_memberships.find_many(
        where={"user_id": user.id},
        include={"team": True}
    )
    return [schemas.Team.model_validate(m.team) for m in memberships if m.team]


@router.get("/all", response_model=list[schemas.Team])
async def get_all_teams(user=Depends(get_current_user)):
    """Get all active teams (for selection UI)"""
    teams = await prisma.teams.find_many(where={"is_active": True})
    return [schemas.Team.model_validate(t) for t in teams]

