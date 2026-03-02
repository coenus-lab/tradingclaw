from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    user_id: int
    event_type: str
    action: str
    symbol: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class GuardEvaluateIn(BaseModel):
    user_id: int
    action: str
    symbol: str = "PI_XBTUSD"
    requested_leverage: Optional[float] = None
    risk_at_stop_pct: Optional[float] = None
    is_add: bool = False
    is_stop_widening: bool = False


class GuardEvaluateOut(BaseModel):
    decision: str
    reasons: List[str]
    allowed_actions: List[str]


class ScoreOut(BaseModel):
    score: int
    sub_scores: Dict[str, int]
    last_updated: datetime


class PolicyIn(BaseModel):
    name: str
    enforcement_level: str = "guard"
    max_risk_at_stop_pct: float = 1.0
    max_leverage: float = 3.0
    max_adds: int = 1
    add_cooldown_seconds: int = 600
    max_trades_per_day: int = 10
    max_consecutive_losses: int = 3
    strict_stop_widening_block: bool = True
    allowlist_symbols: List[str] = ["PI_XBTUSD"]
    config: Dict[str, Any] = Field(default_factory=dict)


class CredentialIn(BaseModel):
    user_id: int
    environment: str
    api_key: str
    api_secret: str
