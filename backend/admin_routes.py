from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_admin_user
from database import get_db
from models import FoodLog, Recommendation, ScanLog, User


router = APIRouter()


@router.get("/admin/stats")
def admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    today = date.today()
    user_count = db.query(func.count(User.id)).scalar() or 0
    scans_today = (
        db.query(func.coalesce(func.sum(ScanLog.scan_count), 0))
        .filter(ScanLog.scan_date == today)
        .scalar()
        or 0
    )
    logs_today = (
        db.query(func.count(FoodLog.id))
        .filter(func.date(FoodLog.scan_time) == today)
        .scalar()
        or 0
    )
    return {
        "users": user_count,
        "scans_today": int(scans_today),
        "logs_today": int(logs_today),
    }


@router.get("/admin/users")
def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "created_at": u.created_at,
            "goal": u.goal,
            "daily_calorie_goal": u.daily_calorie_goal,
        }
        for u in users
    ]


@router.get("/admin/users/{user_id}")
def admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    logs = (
        db.query(FoodLog)
        .filter(FoodLog.user_id == user_id)
        .order_by(FoodLog.scan_time.desc())
        .limit(50)
        .all()
    )
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user_id)
        .order_by(Recommendation.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
            "goal": user.goal,
            "daily_calorie_goal": user.daily_calorie_goal,
        },
        "recent_logs": [
            {
                "id": f.id,
                "food_name": f.food_name,
                "calories": f.calories,
                "meal_type": f.meal_type,
                "scan_time": f.scan_time,
            }
            for f in logs
        ],
        "recent_recommendations": [
            {
                "id": r.id,
                "created_at": r.created_at,
                "preview": (r.content or "")[:160],
            }
            for r in recs
        ],
    }


@router.get("/admin/food-logs")
def admin_food_logs(
    user_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    q = db.query(FoodLog).order_by(FoodLog.scan_time.desc())
    if user_id is not None:
        q = q.filter(FoodLog.user_id == user_id)
    logs = q.limit(limit).all()
    return [
        {
            "id": f.id,
            "user_id": f.user_id,
            "food_name": f.food_name,
            "meal_type": f.meal_type,
            "calories": f.calories,
            "scan_time": f.scan_time,
        }
        for f in logs
    ]


@router.get("/admin/scan-logs")
def admin_scan_logs(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    rows = (
        db.query(ScanLog)
        .order_by(ScanLog.scan_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "scan_date": r.scan_date,
            "scan_count": r.scan_count,
        }
        for r in rows
    ]


@router.get("/admin/recommendations")
def admin_recommendations(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    recs = (
        db.query(Recommendation)
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "created_at": r.created_at,
            "preview": (r.content or "")[:160],
        }
        for r in recs
    ]

