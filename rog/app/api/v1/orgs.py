from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from rog.app.api.v1.deps import get_current_user
from rog.app.core.database import get_db
from rog.app.models.membership import Membership
from rog.app.models.organization import Organization
from rog.app.models.role import Role
from rog.app.models.user import User
from rog.app.schemas.orgs import OrganizationCreate

router = APIRouter()


def _get_or_create_owner_role(db: Session) -> Role:
    role = db.scalar(select(Role).where(Role.name == "owner"))
    if role is None:
        role = Role(name="owner", permissions={"*": True})
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_org(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    existing = db.scalar(select(Organization).where(Organization.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Organization name already exists")

    org = Organization(name=payload.name, industry=payload.industry, jurisdiction=payload.jurisdiction)
    db.add(org)
    db.commit()
    db.refresh(org)

    owner_role = _get_or_create_owner_role(db)
    membership = Membership(user_id=current_user.id, organization_id=org.id, role_id=owner_role.id)
    db.add(membership)
    db.commit()

    return {"id": str(org.id), "name": org.name, "industry": org.industry, "jurisdiction": org.jurisdiction}


@router.get("/list")
def list_orgs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    q = (
        select(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == current_user.id)
        .order_by(Organization.created_at.desc())
    )
    orgs = db.scalars(q).all()
    return [{"id": str(o.id), "name": o.name, "industry": o.industry, "jurisdiction": o.jurisdiction} for o in orgs]

