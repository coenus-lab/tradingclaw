from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    create_token,
    decrypt_secret,
    encrypt_secret,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from app.models.entities import ApiCredential, AuditLog, Event, Policy, StabilityScoreSnapshot, User, UserPolicy
from app.rules.engine import evaluate_guard, update_counters_after_event
from app.schemas.common import CredentialIn, EventIn, GuardEvaluateIn, KrakenOrderIn, LoginIn, PolicyIn, RegisterIn, ScoreOut
from app.scoring.service import calculate_stability_score

router = APIRouter(prefix="/v1")


def _authorize_user(user_id: int, current_user: User) -> None:
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(403, "access to another user is forbidden")


@router.post("/auth/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "email exists")
    user = User(email=payload.email, password_hash=hash_password(payload.password), role="trader")
    db.add(user)
    db.commit()
    return {"id": user.id}


@router.post("/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    return {"token": create_token(str(user.id)), "user_id": user.id, "role": user.role}


@router.post("/credentials")
def save_credentials(
    payload: CredentialIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cred = ApiCredential(
        user_id=current_user.id,
        environment=payload.environment,
        api_key=payload.api_key,
        api_secret_encrypted=encrypt_secret(payload.api_secret),
    )
    db.add(cred)
    db.add(AuditLog(actor_user_id=current_user.id, target_user_id=current_user.id, entity_type="credential", entity_id="new", action="create"))
    db.commit()
    return {"ok": True}


@router.post("/events")
def create_event(
    payload: EventIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = Event(
        user_id=current_user.id,
        event_type=payload.event_type,
        action=payload.action,
        symbol=payload.symbol,
        payload=payload.payload,
        guard_result=payload.payload.get("guard_result", "allow"),
        reason=payload.payload.get("reason"),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    update_counters_after_event(event)
    return {"id": event.id, "created_at": event.created_at}


@router.post("/guard/evaluate")
def guard_evaluate(
    payload: GuardEvaluateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    guard_payload = {**payload.model_dump(), "user_id": current_user.id}
    decision, reasons, allowed_actions = evaluate_guard(db, guard_payload)
    event = Event(
        user_id=current_user.id,
        event_type="guard_check",
        action=payload.action,
        symbol=payload.symbol,
        payload=guard_payload,
        guard_result=decision,
        reason="; ".join(reasons),
    )
    db.add(event)
    db.commit()
    update_counters_after_event(event)
    return {"decision": decision, "reasons": reasons, "allowed_actions": allowed_actions}


@router.get("/users/{user_id}/score", response_model=ScoreOut)
def get_score(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _authorize_user(user_id, current_user)
    latest = db.query(StabilityScoreSnapshot).filter(StabilityScoreSnapshot.user_id == user_id).order_by(desc(StabilityScoreSnapshot.created_at)).first()
    if not latest:
        latest = calculate_stability_score(db, user_id)
    return ScoreOut(score=latest.score, sub_scores=latest.sub_scores, last_updated=latest.created_at)


@router.get("/users/{user_id}/events")
def get_events(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _authorize_user(user_id, current_user)
    events = db.query(Event).filter(Event.user_id == user_id).order_by(desc(Event.created_at)).limit(10).all()
    return [
        {
            "id": e.id,
            "action": e.action,
            "guard_result": e.guard_result,
            "reason": e.reason,
            "created_at": e.created_at,
        }
        for e in events
    ]


# Admin endpoints
@router.post("/admin/policies")
def create_policy(
    payload: PolicyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    policy = Policy(**payload.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    db.add(AuditLog(actor_user_id=current_user.id, entity_type="policy", entity_id=str(policy.id), action="create", details=payload.model_dump()))
    db.commit()
    return {"id": policy.id}


@router.get("/admin/policies")
def list_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rows = db.query(Policy).order_by(Policy.id.asc()).all()
    return [{"id": p.id, "name": p.name, "enforcement": p.enforcement_level, "max_leverage": p.max_leverage} for p in rows]


@router.put("/admin/policies/{policy_id}")
def update_policy(
    policy_id: int,
    payload: PolicyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(404, "policy not found")
    for k, v in payload.model_dump().items():
        setattr(policy, k, v)
    db.commit()
    db.add(AuditLog(actor_user_id=current_user.id, entity_type="policy", entity_id=str(policy.id), action="update", details=payload.model_dump()))
    db.commit()
    return {"ok": True}


@router.delete("/admin/policies/{policy_id}")
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(404, "policy not found")
    db.delete(policy)
    db.add(AuditLog(actor_user_id=current_user.id, entity_type="policy", entity_id=str(policy_id), action="delete", details={}))
    db.commit()
    return {"ok": True}


@router.post("/admin/assign-policy")
def assign_policy(
    user_id: int,
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    up = UserPolicy(user_id=user_id, policy_id=policy_id)
    db.add(up)
    db.add(AuditLog(actor_user_id=current_user.id, target_user_id=user_id, entity_type="user_policy", entity_id=f"{user_id}:{policy_id}", action="assign", details={}))
    db.commit()
    return {"ok": True}


@router.get("/admin/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(200).all()
    return [{"id": l.id, "entity": l.entity_type, "action": l.action, "details": l.details, "created_at": l.created_at} for l in logs]

from app.connector.kraken import KrakenFuturesClient


def _get_latest_credential(db: Session, user_id: int, environment: str):
    cred = db.query(ApiCredential).filter(ApiCredential.user_id == user_id, ApiCredential.environment == environment).order_by(desc(ApiCredential.created_at)).first()
    if not cred:
        raise HTTPException(400, "missing API credentials")
    return cred


@router.get("/kraken/{user_id}/positions")
async def get_positions(
    user_id: int,
    environment: Literal["demo", "prod"] = "demo",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _authorize_user(user_id, current_user)
    cred = _get_latest_credential(db, user_id, environment)
    client = KrakenFuturesClient(cred.api_key, decrypt_secret(cred.api_secret_encrypted), environment)
    return await client.get_positions()


@router.post("/kraken/{user_id}/order")
async def send_order(
    user_id: int,
    order: KrakenOrderIn,
    environment: Literal["demo", "prod"] = "demo",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _authorize_user(user_id, current_user)
    order_data = order.model_dump()
    decision, reasons, _ = evaluate_guard(
        db,
        {
            "user_id": user_id,
            "action": "open_position",
            "symbol": order.symbol,
            "requested_leverage": order.leverage,
            "risk_at_stop_pct": order.risk_at_stop_pct,
            "is_add": order.is_add,
            "is_stop_widening": order.is_stop_widening,
        },
    )
    if decision == "block":
        db.add(Event(user_id=user_id, event_type="order", action="blocked_order", symbol=order.symbol, payload=order_data, guard_result="block", reason="; ".join(reasons)))
        db.commit()
        raise HTTPException(403, {"decision": decision, "reasons": reasons})

    cred = _get_latest_credential(db, user_id, environment)
    client = KrakenFuturesClient(cred.api_key, decrypt_secret(cred.api_secret_encrypted), environment)
    response = await client.send_order(order.kraken_payload())
    db.add(Event(user_id=user_id, event_type="order", action="open_position", symbol=order.symbol, payload=order_data, guard_result="allow", reason=""))
    db.commit()
    return response
