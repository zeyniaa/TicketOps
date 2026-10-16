import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, utcnow

def uid(): return uuid.uuid4().hex

class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    csrf: Mapped[str] = mapped_column(String(64), default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    customer: Mapped[str] = mapped_column(String(100), default="Pelanggan demo")
    order_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="baru", index=True)
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    team: Mapped[str] = mapped_column(String(40), default="customer_care")
    priority: Mapped[str] = mapped_column(String(4), default="P3")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (UniqueConstraint("ticket_id", "revision"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict] = mapped_column(JSON)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Draft(Base):
    __tablename__ = "drafts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30))
    policy_refs: Mapped[list] = mapped_column(JSON, default=list)
    missing_information: Mapped[list] = mapped_column(JSON, default=list)
    review_flags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    model_version: Mapped[str] = mapped_column(String(100), default="template-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    category: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    code: Mapped[str] = mapped_column(String(40))
    facts: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("workspace_id", "code"),)

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    changes: Mapped[dict] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(Text, default="Koreksi operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20), default="analysis")
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    stage: Mapped[str] = mapped_column(String(40), default="Menunggu")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    result: Mapped[dict] = mapped_column(JSON)
