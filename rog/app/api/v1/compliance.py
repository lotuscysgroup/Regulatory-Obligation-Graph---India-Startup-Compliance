from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from rog.app.api.v1.deps import get_current_user
from rog.app.core.database import get_db
from rog.app.models.company import Company
from rog.app.models.company_document import CompanyDocument
from rog.app.models.user import User
from rog.app.schemas.compliance import AlertResponse, CompanyCreate, CompanyResponse, ComplianceStatusResponse
from rog.app.services.alert_generator import AlertGenerator
from rog.app.services.compliance_matcher import ComplianceMatcher
from rog.app.utils.storage import company_document_path

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXT = {".pdf": "pdf", ".docx": "docx"}


def _validate_file(file: UploadFile, *, max_bytes: int) -> tuple[str, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and DOCX are allowed.")
    if file.size is not None and file.size > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    return suffix, ALLOWED_EXT[suffix]


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> CompanyResponse:
    company = Company(name=payload.name, industry=payload.industry, jurisdiction=payload.jurisdiction)
    db.add(company)
    db.commit()
    db.refresh(company)
    return CompanyResponse(id=company.id, name=company.name, industry=company.industry, jurisdiction=company.jurisdiction)


@router.post("/companies/{company_id}/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_company_document(
    company_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    company = db.scalar(select(Company).where(Company.id == company_id))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    settings = request.app.state.settings
    max_bytes = settings.max_upload_mb * 1024 * 1024
    suffix, file_type = _validate_file(file, max_bytes=max_bytes)
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    safe_name = (file.filename or f"doc{suffix}").replace(" ", "_")
    path = company_document_path(storage_dir=settings.storage_dir, company_id=str(company_id), filename=safe_name)
    path.write_bytes(content)

    doc = CompanyDocument(
        company_id=company_id,
        file_name=safe_name,
        file_type=file_type,
        file_path=str(path.as_posix()),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    matcher = ComplianceMatcher(db)
    matched_count = matcher.match_company_document(company_id=company_id, file_path=doc.file_path, file_type=doc.file_type)
    alert_count = AlertGenerator(db).run_for_company(company_id)
    db.commit()

    logger.info(
        "company_document_uploaded company_id=%s doc_id=%s matched=%s alerts=%s",
        company_id,
        doc.id,
        matched_count,
        alert_count,
    )
    return {"document_id": str(doc.id), "matched_obligations": matched_count, "alerts_created": alert_count}


@router.get("/companies/{company_id}", response_model=list[ComplianceStatusResponse])
def get_company_compliance(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ComplianceStatusResponse]:
    matcher = ComplianceMatcher(db)
    statuses = matcher.get_company_compliance(company_id)
    return [
        ComplianceStatusResponse(
            company_id=s.company_id,
            obligation_id=s.obligation_id,
            status=s.status,
            risk_level=s.risk_level,
            last_checked=s.last_checked,
        )
        for s in statuses
    ]


@router.get("/companies/{company_id}/high-risk", response_model=list[ComplianceStatusResponse])
def get_high_risk_obligations(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ComplianceStatusResponse]:
    matcher = ComplianceMatcher(db)
    statuses = matcher.get_high_risk_obligations(company_id)
    return [
        ComplianceStatusResponse(
            company_id=s.company_id,
            obligation_id=s.obligation_id,
            status=s.status,
            risk_level=s.risk_level,
            last_checked=s.last_checked,
        )
        for s in statuses
    ]


@router.get("/companies/{company_id}/non-compliant", response_model=list[ComplianceStatusResponse])
def get_non_compliant_obligations(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ComplianceStatusResponse]:
    matcher = ComplianceMatcher(db)
    statuses = matcher.get_non_compliant_obligations(company_id)
    return [
        ComplianceStatusResponse(
            company_id=s.company_id,
            obligation_id=s.obligation_id,
            status=s.status,
            risk_level=s.risk_level,
            last_checked=s.last_checked,
        )
        for s in statuses
    ]


@router.get("/companies/{company_id}/alerts", response_model=list[AlertResponse])
def get_company_alerts(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertResponse]:
    alerts = AlertGenerator(db).get_company_alerts(company_id)
    return [
        AlertResponse(
            id=a.id,
            company_id=a.company_id,
            obligation_id=a.obligation_id,
            alert_type=a.alert_type,
            message=a.message,
            due_date=a.due_date,
            status=a.status,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.get("/companies/{company_id}/alerts/active", response_model=list[AlertResponse])
def get_active_alerts(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertResponse]:
    alerts = AlertGenerator(db).get_active_alerts(company_id)
    return [
        AlertResponse(
            id=a.id,
            company_id=a.company_id,
            obligation_id=a.obligation_id,
            alert_type=a.alert_type,
            message=a.message,
            due_date=a.due_date,
            status=a.status,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.get("/companies/{company_id}/alerts/overdue", response_model=list[AlertResponse])
def get_overdue_alerts(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertResponse]:
    alerts = AlertGenerator(db).get_overdue_alerts(company_id)
    return [
        AlertResponse(
            id=a.id,
            company_id=a.company_id,
            obligation_id=a.obligation_id,
            alert_type=a.alert_type,
            message=a.message,
            due_date=a.due_date,
            status=a.status,
            created_at=a.created_at,
        )
        for a in alerts
    ]

