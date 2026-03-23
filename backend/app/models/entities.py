from datetime import datetime
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ProtocolStatus, ProtocolType, TaskStatus


class Protocol(Base):
    __tablename__ = "protocols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    protocol_type: Mapped[str] = mapped_column(String(30), default=ProtocolType.standard.value)
    status: Mapped[str] = mapped_column(String(50), default=ProtocolStatus.uploaded.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    draft_saved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    normalized_docx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_docx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bitrix_smart_process_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bitrix_publish_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    topics = relationship("Topic", back_populates="protocol", cascade="all,delete-orphan")
    tasks = relationship("TaskCandidate", back_populates="protocol", cascade="all,delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    protocol_id: Mapped[int] = mapped_column(ForeignKey("protocols.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    source_type: Mapped[str] = mapped_column(String(20), default="auto")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    protocol = relationship("Protocol", back_populates="topics")
    tasks = relationship("TaskCandidate", back_populates="topic")


class TaskCandidate(Base):
    __tablename__ = "task_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    protocol_id: Mapped[int] = mapped_column(ForeignKey("protocols.id"), index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    source_fragment: Mapped[str] = mapped_column(Text, default="")
    normalized_text: Mapped[str] = mapped_column(Text, default="")
    topic_auto_candidate: Mapped[str | None] = mapped_column(String(255), nullable=True)
    topic_candidate_list: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    assignee_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assignee_b24_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assignee_b24_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deadline_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deadline_iso: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=TaskStatus.draft.value)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    bitrix_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    protocol = relationship("Protocol", back_populates="tasks")
    topic = relationship("Topic", back_populates="tasks")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    protocol_id: Mapped[int | None] = mapped_column(ForeignKey("protocols.id"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
