from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db import get_db
from src.models import Release
from src.schemas import ReleaseCreateRequest, ReleaseResponse

router = APIRouter(prefix="/releases", tags=["releases"])


@router.post("", response_model=ReleaseResponse)
def create_release(payload: ReleaseCreateRequest, db: Session = Depends(get_db)):
    release = Release(
        service=payload.service,
        version=payload.version,
        environment=payload.environment,
        status="PENDING",
        target_repo=payload.target.repo,
        target_ref=payload.target.ref,
        target_compose_path=payload.target.composePath,
    )

    db.add(release)
    db.commit()
    db.refresh(release)

    return release


@router.get("/{release_id}", response_model=ReleaseResponse)
def get_release(release_id: str, db: Session = Depends(get_db)):
    release = db.query(Release).filter(Release.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    return release


@router.get("", response_model=list[ReleaseResponse])
def list_releases(db: Session = Depends(get_db)):
    return db.query(Release).order_by(Release.created_at.desc()).all()