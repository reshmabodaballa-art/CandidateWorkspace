import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def utc_now():
    return datetime.now(timezone.utc)

def new_id():
    return str(uuid.uuid4())

class Base(DeclarativeBase):
    pass

class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    status: Mapped[str] = mapped_column(String(30), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    input_count: Mapped[int] = mapped_column(Integer, default=0)
    output_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

class Checkpoint(Base):
    __tablename__ = "checkpoints"
    endpoint: Mapped[str] = mapped_column(String(100), primary_key=True)
    next_cursor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_successful_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class RawAPIResponse(Base):
    __tablename__ = "raw_api_responses"
    response_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    request_cursor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    next_cursor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class RejectedRecord(Base):
    __tablename__ = "rejected_records"
    reject_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_record: Mapped[dict] = mapped_column(JSON, nullable=False)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    rejected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class OrderHistory(Base):
    __tablename__ = "order_history"
    history_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(String(50), nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"), nullable=False)
    record_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
