from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


class Firm(Base):
    __tablename__ = "firms"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="trader")
    firm_id = Column(Integer, ForeignKey("firms.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiCredential(Base):
    __tablename__ = "api_credentials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    environment = Column(String(10), nullable=False, default="demo")
    api_key = Column(String(255), nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    enforcement_level = Column(String(20), default="guard")
    max_risk_at_stop_pct = Column(Float, default=1.0)
    max_leverage = Column(Float, default=3.0)
    max_adds = Column(Integer, default=1)
    add_cooldown_seconds = Column(Integer, default=600)
    max_trades_per_day = Column(Integer, default=10)
    max_consecutive_losses = Column(Integer, default=3)
    strict_stop_widening_block = Column(Boolean, default=True)
    allowlist_symbols = Column(JSON, default=["PI_XBTUSD"])
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPolicy(Base):
    __tablename__ = "user_policies"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="inactive")
    mode = Column(String(20), default="training")
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(80), nullable=False)
    action = Column(String(80), nullable=False)
    symbol = Column(String(30), nullable=True)
    payload = Column(JSON, default={})
    guard_result = Column(String(20), nullable=False, default="allow")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StabilityScoreSnapshot(Base):
    __tablename__ = "stability_scores"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    sub_scores = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(String(80), nullable=False)
    action = Column(String(40), nullable=False)
    details = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
