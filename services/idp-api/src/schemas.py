from datetime import datetime
from pydantic import BaseModel


class ReleaseTarget(BaseModel):
    repo: str
    ref: str
    composePath: str


class ReleaseCreateRequest(BaseModel):
    service: str
    version: str
    environment: str
    target: ReleaseTarget


class ReleaseResponse(BaseModel):
    id: str
    service: str
    version: str
    environment: str
    status: str
    target_repo: str
    target_ref: str
    target_compose_path: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True