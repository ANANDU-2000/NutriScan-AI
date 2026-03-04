from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Iterable

from fastapi import HTTPException
from pywebpush import webpush, WebPushException
from sqlalchemy.orm import Session

from models import Notification, PushSubscription, ReminderSchedule


VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY") or ""
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY") or ""
VAPID_EMAIL = os.getenv("VAPID_EMAIL") or "admin@example.com"


def _get_vapid_claims() -> dict:
    return {"sub": f"mailto:{VAPID_EMAIL}"}


def send_push_notification(
    db: Session,
    user_id: int,
    title: str,
    body: str,
    payload: dict | None = None,
) -> None:
    """Send a Web Push notification to all subscriptions for a user."""
    if not (VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY):
        # Push not configured; fail silently but record notification
        notif = Notification(
            user_id=user_id,
            type="push_disabled",
            title=title,
            body=body,
            payload=json.dumps(payload or {}),
        )
        db.add(notif)
        db.commit()
        return

    subs: Iterable[PushSubscription] = (
        db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    )
    if not subs:
        return

    notif = Notification(
        user_id=user_id,
        type="push",
        title=title,
        body=body,
        payload=json.dumps(payload or {}),
    )
    db.add(notif)
    db.commit()

    data_str = json.dumps(
        {
            "title": title,
            "body": body,
            "payload": payload or {},
        }
    )

    for sub in subs:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=data_str,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=_get_vapid_claims(),
            )
        except WebPushException:
            # Remove invalid subscription and continue
            db.delete(sub)
            db.commit()


def get_due_reminders(db: Session, now: datetime | None = None) -> list[ReminderSchedule]:
    """Return reminder schedules that are due at the current minute."""
    if now is None:
        now = datetime.utcnow()
    current_time = now.strftime("%H:%M")
    return (
        db.query(ReminderSchedule)
        .filter(
            ReminderSchedule.enabled.is_(True),
            ReminderSchedule.scheduled_time == current_time,
        )
        .all()
    )


def check_and_send_due_reminders(db: Session) -> None:
    """Poll for due reminders and send notifications."""
    due = get_due_reminders(db)
    for rem in due:
        meal_label = rem.type.replace("_", " ").title() if rem.type else "Reminder"
        try:
            send_push_notification(
                db,
                user_id=rem.user_id,
                title="NutriScan reminder",
                body=f"Time to check your {meal_label.lower()} in NutriScan.",
                payload={"type": rem.type or "reminder"},
            )
        except HTTPException:
            # Do not break the loop for one failure
            continue

