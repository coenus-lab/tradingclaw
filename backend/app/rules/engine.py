from datetime import datetime, timezone
from typing import List, Tuple

import redis
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Event, Policy, UserPolicy

rds = redis.from_url(settings.redis_url, decode_responses=True)


def get_user_policy(db: Session, user_id: int) -> Policy:
    up = db.query(UserPolicy).filter(UserPolicy.user_id == user_id).order_by(desc(UserPolicy.assigned_at)).first()
    if up:
        policy = db.query(Policy).filter(Policy.id == up.policy_id).first()
        if policy:
            return policy
    policy = db.query(Policy).order_by(Policy.id.asc()).first()
    return policy


def evaluate_guard(db: Session, payload: dict) -> Tuple[str, List[str], List[str]]:
    user_id = payload["user_id"]
    action = payload["action"]
    policy = get_user_policy(db, user_id)
    reasons: List[str] = []

    if not policy:
        return "block", ["No policy configured"], []

    symbol = payload.get("symbol", "PI_XBTUSD")

    # Rule 1: Symbol allowlist
    if symbol not in policy.allowlist_symbols:
        reasons.append("Symbol not in allowlist")

    # Rule 2: risk at stop cap
    risk_at_stop = payload.get("risk_at_stop_pct")
    if risk_at_stop is not None and risk_at_stop > policy.max_risk_at_stop_pct:
        reasons.append(f"Risk-at-stop exceeds {policy.max_risk_at_stop_pct}%")

    # Rule 3: leverage cap
    req_lev = payload.get("requested_leverage")
    if req_lev is not None and req_lev > policy.max_leverage:
        reasons.append(f"Leverage exceeds {policy.max_leverage}x")

    # Rule 4: strict stop widening block
    if payload.get("is_stop_widening") and policy.strict_stop_widening_block:
        reasons.append("Stop widening is blocked")

    # Rule 5: max adds
    if payload.get("is_add"):
        add_key = f"user:{user_id}:adds:{datetime.now(timezone.utc).date()}"
        adds = int(rds.get(add_key) or 0)
        if adds >= policy.max_adds:
            reasons.append("Max adds reached")
        # Rule 6: add cooldown
        cooldown_key = f"user:{user_id}:add_cooldown"
        if rds.ttl(cooldown_key) > 0:
            reasons.append("Add cooldown active")

    # Rule 7: trades per day
    trades_today_key = f"user:{user_id}:trades:{datetime.now(timezone.utc).date()}"
    if int(rds.get(trades_today_key) or 0) >= policy.max_trades_per_day and action == "open_position":
        reasons.append("Max trades per day reached")

    # Rule 8: consecutive losses
    if int(rds.get(f"user:{user_id}:consec_losses") or 0) >= policy.max_consecutive_losses and action == "open_position":
        reasons.append("Consecutive loss lockout")

    # Rule 9: overtrading cooldown after blocks
    if rds.ttl(f"user:{user_id}:global_cooldown") > 0 and action == "open_position":
        reasons.append("Global cooldown active")

    # Rule 10: anti-flip (rapid opposite orders)
    last_flip = db.query(Event).filter(Event.user_id == user_id, Event.action == "flip_side").order_by(desc(Event.created_at)).first()
    if last_flip and (datetime.utcnow() - last_flip.created_at).seconds < 120 and action == "flip_side":
        reasons.append("Rapid side flip blocked")

    decision = "allow" if not reasons else "block"
    allowed_actions = ["place_market", "place_limit", "place_stop", "cancel_order"] if decision == "allow" else ["cancel_order", "flatten"]
    return decision, reasons, allowed_actions


def update_counters_after_event(event: Event):
    user_id = event.user_id
    today = datetime.now(timezone.utc).date()
    if event.action == "open_position" and event.guard_result == "allow":
        rds.incr(f"user:{user_id}:trades:{today}")
        rds.expire(f"user:{user_id}:trades:{today}", 172800)
    if event.action == "add_position" and event.guard_result == "allow":
        add_key = f"user:{user_id}:adds:{today}"
        rds.incr(add_key)
        rds.expire(add_key, 172800)
        rds.setex(f"user:{user_id}:add_cooldown", 600, "1")
    if event.action == "close_loss":
        rds.incr(f"user:{user_id}:consec_losses")
    if event.action == "close_win":
        rds.set(f"user:{user_id}:consec_losses", 0)
    if event.guard_result == "block":
        rds.setex(f"user:{user_id}:global_cooldown", 120, "1")
