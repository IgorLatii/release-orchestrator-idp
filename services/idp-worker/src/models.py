from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from src.db import Base


class Release(Base):
    __tablename__ = "releases"

    id = Column(String, primary_key=True)
    service = Column(String, nullable=False)
    version = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    status = Column(String, nullable=False)

    target_repo = Column(String, nullable=False)
    target_ref = Column(String, nullable=False)
    target_compose_path = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    error_message = Column(Text, nullable=True)


class ReleaseStep(Base):
    __tablename__ = "release_steps"

    id = Column(String, primary_key=True)
    release_id = Column(String, ForeignKey("releases.id"), nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)