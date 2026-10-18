from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=12, max_length=256)


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    action: str
    symbol: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class GuardEvaluateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    model_config = ConfigDict(extra="forbid")

    environment: Literal["demo", "prod"]
    api_key: str
    api_secret: str


class KrakenOrderIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    orderType: Literal["mkt", "lmt", "stp"]
    symbol: str = "PI_XBTUSD"
    size: float = Field(gt=0)
    limitPrice: Optional[float] = Field(default=None, gt=0)
    stopPrice: Optional[float] = Field(default=None, gt=0)
    reduceOnly: bool = False
    cliOrdId: Optional[str] = Field(default=None, max_length=100)
    leverage: float = Field(gt=0)
    risk_at_stop_pct: float = Field(gt=0)
    is_add: bool = False
    is_stop_widening: bool = False

    @model_validator(mode="after")
    def require_price_for_conditional_orders(self):
        if self.orderType == "lmt" and self.limitPrice is None:
            raise ValueError("limitPrice is required for limit orders")
        if self.orderType == "stp" and self.stopPrice is None:
            raise ValueError("stopPrice is required for stop orders")
        return self

    def kraken_payload(self) -> Dict[str, Any]:
        allowed = {"orderType", "symbol", "size", "limitPrice", "stopPrice", "reduceOnly", "cliOrdId"}
        return {key: value for key, value in self.model_dump().items() if key in allowed and value is not None}
