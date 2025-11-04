from __future__ import annotations

from .prisma_client import prisma


async def seed_static():
    """Seed static data: teams and domains"""

    # Seed teams
    teams_data = [
        {"name": "General", "external_ref": None, "is_active": True},
        {"name": "Engineering", "external_ref": "eng", "is_active": True},
        {"name": "Product", "external_ref": "product", "is_active": True},
        {"name": "Design", "external_ref": "design", "is_active": True},
    ]

    for team_data in teams_data:
        await prisma.teams.upsert(
            where={"name": team_data["name"]},
            data={
                "create": team_data,
                "update": {}
            }
        )

    # Seed domains
    domains_data = [
        {"key": "engineering", "name": "Engineering", "parent_domain_id": None, "is_active": True},
        {"key": "product", "name": "Product Management", "parent_domain_id": None, "is_active": True},
        {"key": "design", "name": "Design", "parent_domain_id": None, "is_active": True},
        {"key": "marketing", "name": "Marketing", "parent_domain_id": None, "is_active": True},
        {"key": "sales", "name": "Sales", "parent_domain_id": None, "is_active": True},
    ]

    for domain_data in domains_data:
        await prisma.domains.upsert(
            where={"key": domain_data["key"]},
            data={
                "create": domain_data,
                "update": {}
            }
        )

    print("✅ Static data seeded successfully")

