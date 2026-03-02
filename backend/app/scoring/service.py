from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.entities import Event, StabilityScoreSnapshot


def calculate_stability_score(db: Session, user_id: int) -> StabilityScoreSnapshot:
    events = db.query(Event).filter(Event.user_id == user_id).order_by(desc(Event.created_at)).limit(100).all()
    total = len(events) or 1
    blocked = len([e for e in events if e.guard_result == "block"])
    stop_violations = len([e for e in events if "stop" in (e.reason or "").lower()])
    overtrade = len([e for e in events if "trade" in (e.reason or "").lower()])

    discipline = max(0, 100 - int((blocked / total) * 100))
    risk_control = max(0, 100 - stop_violations * 10)
    pacing = max(0, 100 - overtrade * 10)
    consistency = int((discipline + risk_control + pacing) / 3)
    score = int((discipline * 0.4) + (risk_control * 0.35) + (pacing * 0.25))

    snap = StabilityScoreSnapshot(
        user_id=user_id,
        score=score,
        sub_scores={
            "discipline": discipline,
            "risk_control": risk_control,
            "pacing": pacing,
            "consistency": consistency,
        },
        created_at=datetime.utcnow(),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap
