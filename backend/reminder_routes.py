from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import PushSubscription, ReminderSchedule, User


router = APIRouter()


class ReminderScheduleIn(BaseModel):
    type: Literal["breakfast", "lunch", "dinner", "water", "goal_alert"]
    enabled: bool = True
    scheduled_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class ReminderScheduleOut(BaseModel):
    id: int
    type: str
    enabled: bool
    scheduled_time: str | None


class PushSubscriptionIn(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


@router.get("/reminders/{user_id}", response_model=list[ReminderScheduleOut])
def list_reminders(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view reminders",
        )
    rows = (
        db.query(ReminderSchedule)
        .filter(ReminderSchedule.user_id == user_id)
        .order_by(ReminderSchedule.type)
        .all()
    )
    return [
        ReminderScheduleOut(
            id=row.id,
            type=row.type,
            enabled=row.enabled,
            scheduled_time=row.scheduled_time,
        )
        for row in rows
    ]


@router.post("/reminders", response_model=ReminderScheduleOut)
def upsert_reminder(
    body: ReminderScheduleIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(ReminderSchedule)
        .filter(
            ReminderSchedule.user_id == current_user.id,
            ReminderSchedule.type == body.type,
        )
        .first()
    )
    now = datetime.utcnow()
    if row is None:
        row = ReminderSchedule(
            user_id=current_user.id,
            type=body.type,
            enabled=body.enabled,
            scheduled_time=body.scheduled_time,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    else:
        row.enabled = body.enabled
        row.scheduled_time = body.scheduled_time
        row.updated_at = now
    db.commit()
    db.refresh(row)
    return ReminderScheduleOut(
        id=row.id,
        type=row.type,
        enabled=row.enabled,
        scheduled_time=row.scheduled_time,
    )


@router.post("/push/subscribe")
def subscribe_push(
    body: PushSubscriptionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == body.endpoint).first()
    if sub is None:
        sub = PushSubscription(
            user_id=current_user.id,
            endpoint=body.endpoint,
            p256dh=body.p256dh,
            auth=body.auth,
        )
        db.add(sub)
    else:
        sub.user_id = current_user.id
        sub.p256dh = body.p256dh
        sub.auth = body.auth
    db.commit()
    return {"status": "subscribed"}


@router.delete("/push/subscribe")
def unsubscribe_push(
    body: PushSubscriptionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.endpoint == body.endpoint,
            PushSubscription.user_id == current_user.id,
        )
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    db.delete(sub)
    db.commit()
    return {"status": "unsubscribed"}

