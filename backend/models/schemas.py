import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger,
    Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


# ── 1. API Keys ───────────────────────────────────────────────────────────────
class APIKey(Base):
    __tablename__ = "api_keys"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash     = Column(String(64),  nullable=False, unique=True)
    key_prefix   = Column(String(8),   nullable=False)
    name         = Column(String(100), nullable=False)
    plan         = Column(String(20),  nullable=False, default="demo")
    rate_limit   = Column(Integer,     nullable=False, default=10)
    is_active    = Column(Boolean,     nullable=False, default=True)
    created_at   = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_used_at = Column(TIMESTAMP, nullable=True)
    revoked_at   = Column(TIMESTAMP, nullable=True)
    expires_at   = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index("idx_api_keys_hash",   "key_hash",  unique=True),
        Index("idx_api_keys_active", "is_active"),
    )


# ── 2. Documents ──────────────────────────────────────────────────────────────
class Document(Base):
    __tablename__ = "documents"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id        = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    original_name     = Column(String(255), nullable=False)
    mime_type         = Column(String(100), nullable=False)
    file_size_bytes   = Column(BigInteger,  nullable=False)
    storage_path      = Column(Text,        nullable=False)
    page_count        = Column(Integer,     nullable=True)
    word_count        = Column(Integer,     nullable=True)
    language          = Column(String(10),  nullable=True)
    checksum          = Column(String(64),  nullable=False)
    uploaded_at       = Column(TIMESTAMP, nullable=False, server_default=func.now())
    expires_at        = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index("idx_documents_api_key",  "api_key_id"),
        Index("idx_documents_checksum", "checksum"),
        Index("idx_documents_uploaded", "uploaded_at"),
    )


# ── 3. Extraction Jobs ────────────────────────────────────────────────────────
class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id        = Column(UUID(as_uuid=True), ForeignKey("documents.id"),  nullable=False)
    api_key_id         = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"),   nullable=False)
    status             = Column(String(20),  nullable=False, default="queued")
    schema_name        = Column(String(50),  nullable=True)
    requested_fields   = Column(JSONB,       nullable=False)
    include_confidence = Column(Boolean,     nullable=False, default=False)
    celery_task_id     = Column(String(255), nullable=True)
    queued_at          = Column(TIMESTAMP, nullable=False, server_default=func.now())
    started_at         = Column(TIMESTAMP, nullable=True)
    completed_at       = Column(TIMESTAMP, nullable=True)
    processing_ms      = Column(Integer,     nullable=True)
    error_code         = Column(String(50),  nullable=True)
    error_message      = Column(Text,        nullable=True)
    batch_id           = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("idx_jobs_document_id", "document_id"),
        Index("idx_jobs_api_key",     "api_key_id"),
        Index("idx_jobs_status",      "status"),
        Index("idx_jobs_batch",       "batch_id"),
        Index("idx_jobs_queued_at",   "queued_at"),
    )


# ── 4. Extraction Results ─────────────────────────────────────────────────────
class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id            = Column(UUID(as_uuid=True), ForeignKey("extraction_jobs.id"), nullable=False, unique=True)
    extracted_fields  = Column(JSONB,       nullable=False)
    confidence_scores = Column(JSONB,       nullable=True)
    raw_ai_response   = Column(Text,        nullable=True)
    tokens_used       = Column(Integer,     nullable=True)
    model_version     = Column(String(50),  nullable=False)
    created_at        = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_results_job_id",    "job_id", unique=True),
        Index("idx_results_created_at","created_at"),
    )


# ── 5. Usage Logs ─────────────────────────────────────────────────────────────
class UsageLog(Base):
    __tablename__ = "usage_logs"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id        = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    endpoint          = Column(String(100), nullable=False)
    method            = Column(String(10),  nullable=False)
    status_code       = Column(Integer,     nullable=False)
    error_code        = Column(String(50),  nullable=True)
    file_size_bytes   = Column(BigInteger,  nullable=True)
    processing_ms     = Column(Integer,     nullable=True)
    tokens_used       = Column(Integer,     nullable=True)
    ip_address        = Column(INET,        nullable=True)
    request_id        = Column(String(50),  nullable=False)
    created_at        = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_usage_api_key", "api_key_id", "created_at"),
        Index("idx_usage_created", "created_at"),
        Index("idx_usage_status",  "status_code"),
    )