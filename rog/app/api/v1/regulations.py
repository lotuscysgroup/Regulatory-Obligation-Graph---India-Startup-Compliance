from __future__ import annotations

import json
import logging
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from rog.app.api.v1.deps import get_current_user
from rog.app.core.database import get_db
from rog.app.models.regulation import Regulation
from rog.app.models.regulation_version import RegulationVersion
from rog.app.models.user import User
from rog.app.schemas.regulations import RegulationResponse, RegulationVersionResponse
from rog.app.utils.storage import regulation_version_path

router = APIRouter()
logger = logging.getLogger(__name__)


ALLOWED_EXT = {".pdf": "pdf", ".docx": "docx"}


def _parse_tags(tags_raw: str | None) -> dict:
    if not tags_raw:
        return {}
    try:
        val = json.loads(tags_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="tags must be valid JSON")
    if not isinstance(val, dict):
        raise HTTPException(status_code=400, detail="tags must be a JSON object")
    return val


def _validate_file(file: UploadFile, *, max_bytes: int) -> tuple[str, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and DOCX are allowed.")

    if file.size is not None and file.size > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    return suffix, ALLOWED_EXT[suffix]


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=RegulationResponse)
async def upload_regulation(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    jurisdiction: str = Form(...),
    authority: str = Form(...),
    category: str = Form(...),
    tags: str | None = Form(default=None),
    effective_date: date = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RegulationResponse:
    settings = request.app.state.settings
    max_bytes = settings.max_upload_mb * 1024 * 1024
    suffix, file_type = _validate_file(file, max_bytes=max_bytes)
    tags_dict = _parse_tags(tags)

    regulation = Regulation(
        name=name,
        jurisdiction=jurisdiction,
        authority=authority,
        category=category,
        tags=tags_dict,
        created_by=current_user.id,
        is_deleted=False,
    )
    db.add(regulation)
    db.commit()
    db.refresh(regulation)

    next_version = 1
    version_path = regulation_version_path(
        storage_dir=settings.storage_dir,
        regulation_id=str(regulation.id),
        version=next_version,
        ext=suffix,
    )

    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    version_path.write_bytes(content)

    reg_version = RegulationVersion(
        regulation_id=regulation.id,
        version_number=next_version,
        file_path=str(version_path.as_posix()),
        file_type=file_type,
        effective_date=effective_date,
    )
    db.add(reg_version)
    db.commit()
    db.refresh(reg_version)

    logger.info("regulation_uploaded regulation_id=%s version=%s user_id=%s", regulation.id, reg_version.version_number, current_user.id)

    return RegulationResponse(
        id=regulation.id,
        name=regulation.name,
        jurisdiction=regulation.jurisdiction,
        authority=regulation.authority,
        category=regulation.category,
        tags=regulation.tags,
        created_by=regulation.created_by,
        created_at=regulation.created_at,
        is_deleted=regulation.is_deleted,
        versions=[
            RegulationVersionResponse(
                id=reg_version.id,
                version_number=reg_version.version_number,
                file_path=reg_version.file_path,
                file_type=reg_version.file_type,
                effective_date=reg_version.effective_date,
                uploaded_at=reg_version.uploaded_at,
            )
        ],
    )


@router.get("", response_model=list[RegulationResponse])
def list_regulations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[RegulationResponse]:
    regs = db.scalars(select(Regulation).where(Regulation.is_deleted == func.false()).order_by(Regulation.created_at.desc())).all()

    out: list[RegulationResponse] = []
    for r in regs:
        versions = db.scalars(
            select(RegulationVersion).where(RegulationVersion.regulation_id == r.id).order_by(RegulationVersion.version_number.desc())
        ).all()
        out.append(
            RegulationResponse(
                id=r.id,
                name=r.name,
                jurisdiction=r.jurisdiction,
                authority=r.authority,
                category=r.category,
                tags=r.tags,
                created_by=r.created_by,
                created_at=r.created_at,
                is_deleted=r.is_deleted,
                versions=[
                    RegulationVersionResponse(
                        id=v.id,
                        version_number=v.version_number,
                        file_path=v.file_path,
                        file_type=v.file_type,
                        effective_date=v.effective_date,
                        uploaded_at=v.uploaded_at,
                    )
                    for v in versions
                ],
            )
        )
    return out


@router.get("/{regulation_id}", response_model=RegulationResponse)
def get_regulation(
    regulation_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> RegulationResponse:
    r = db.scalar(select(Regulation).where(Regulation.id == regulation_id))
    if r is None or r.is_deleted:
        raise HTTPException(status_code=404, detail="Regulation not found")

    versions = db.scalars(
        select(RegulationVersion).where(RegulationVersion.regulation_id == r.id).order_by(RegulationVersion.version_number.desc())
    ).all()

    return RegulationResponse(
        id=r.id,
        name=r.name,
        jurisdiction=r.jurisdiction,
        authority=r.authority,
        category=r.category,
        tags=r.tags,
        created_by=r.created_by,
        created_at=r.created_at,
        is_deleted=r.is_deleted,
        versions=[
            RegulationVersionResponse(
                id=v.id,
                version_number=v.version_number,
                file_path=v.file_path,
                file_type=v.file_type,
                effective_date=v.effective_date,
                uploaded_at=v.uploaded_at,
            )
            for v in versions
        ],
    )


@router.delete("/{regulation_id}", status_code=status.HTTP_200_OK)
def delete_regulation(
    regulation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    r = db.scalar(select(Regulation).where(Regulation.id == regulation_id))
    if r is None or r.is_deleted:
        raise HTTPException(status_code=404, detail="Regulation not found")

    r.is_deleted = True
    db.add(r)
    db.commit()

    logger.info("regulation_deleted regulation_id=%s user_id=%s", r.id, current_user.id)
    return {"status": "deleted"}

