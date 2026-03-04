import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import calculate_daily_calories, get_current_user
from database import get_db
from models import FoodLog, Recommendation, User, WeightLog
from openai_service import get_recommendations
from pydantic import BaseModel

from schemas import RecommendContext, StatsResponse, UserResponse, UserUpdate


class WeightLogRequest(BaseModel):
    weight_kg: float
    user_id: int

router = APIRouter()


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


@router.get("/stats/{user_id}", response_model=StatsResponse)
async def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.height_cm or user.height_cm <= 0 or not user.weight_kg:
        bmi = 0.0
    else:
        bmi = user.weight_kg / ((user.height_cm / 100) ** 2)
    bmi_category = _bmi_category(bmi)
    today = date.today()
    consumed_row = (
        db.query(func.coalesce(func.sum(FoodLog.calories), 0))
        .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == today)
        .scalar()
    )
    consumed_today = float(consumed_row or 0)
    daily_goal = user.daily_calorie_goal or 2000
    remaining_today = max(0, daily_goal - consumed_today)

    streak_days = 0
    for i in range(1, 31):
        d = today - timedelta(days=i)
        has_log = (
            db.query(FoodLog.id)
            .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == d)
            .first()
        )
        if has_log:
            streak_days += 1
        else:
            break
    has_today = (
        db.query(FoodLog.id)
        .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == today)
        .first()
    )
    if has_today:
        streak_days += 1

    last_7_days = []
    for i in range(7):
        d = today - timedelta(days=i)
        row = (
            db.query(
                func.coalesce(func.sum(FoodLog.calories), 0).label("total_calories"),
                func.coalesce(func.sum(FoodLog.protein_g), 0).label("total_protein"),
                func.coalesce(func.sum(FoodLog.carbs_g), 0).label("total_carbs"),
                func.coalesce(func.sum(FoodLog.fat_g), 0).label("total_fat"),
                func.count(FoodLog.id).label("items_count"),
            )
            .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == d)
        ).first()
        total_cal = float(row.total_calories) if row else 0.0
        total_protein = float(row.total_protein) if row else 0.0
        total_carbs = float(row.total_carbs) if row else 0.0
        total_fat = float(row.total_fat) if row else 0.0
        count = int(row.items_count) if row else 0
        last_7_days.append({
            "date": d.isoformat(),
            "total_calories": total_cal,
            "total_protein": total_protein,
            "total_carbs": total_carbs,
            "total_fat": total_fat,
            "items_count": count,
        })

    return StatsResponse(
        bmi=round(bmi, 1),
        bmi_category=bmi_category,
        daily_goal=daily_goal,
        consumed_today=consumed_today,
        remaining_today=remaining_today,
        streak_days=streak_days,
        last_7_days=last_7_days,
    )


@router.post("/recommendations/{user_id}")
async def get_user_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RecommendContext | None = Body(default=None),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    today = date.today()
    logs = (
        db.query(FoodLog)
        .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == today)
        .all()
    )
    # Simple daily recommendation limit (10 per day)
    today_recs = (
        db.query(func.count(Recommendation.id))
        .filter(
            Recommendation.user_id == user_id,
            func.date(Recommendation.created_at) == today,
        )
        .scalar()
    )
    if today_recs and today_recs >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily recommendation limit reached (10 per day). Try again tomorrow.",
        )
    today_foods = [
        {
            "food_name": log.food_name,
            "calories": log.calories,
            "quantity_g": log.quantity_g,
            "meal_type": log.meal_type,
        }
        for log in logs
    ]
    last_meal_time = None
    if logs:
        latest = max(logs, key=lambda x: x.scan_time or datetime.min)
        if latest.scan_time:
            last_meal_time = latest.scan_time.strftime("%I:%M %p")
    water_glasses = (context.water_glasses if context else 0)
    protein_today = sum((log.protein_g or 0) for log in logs)
    carbs_today = sum((log.carbs_g or 0) for log in logs)
    fat_today = sum((log.fat_g or 0) for log in logs)
    if user.height_cm and user.height_cm > 0 and user.weight_kg:
        bmi = user.weight_kg / ((user.height_cm / 100) ** 2)
    else:
        bmi = 22.0
    daily_goal = user.daily_calorie_goal or 2000
    user_data = {
        "name": user.name,
        "age": user.age or 30,
        "gender": user.gender or "other",
        "weight_kg": user.weight_kg or 70,
        "height_cm": user.height_cm or 170,
        "goal": user.goal or "maintain",
        "daily_calorie_goal": daily_goal,
        "bmi": bmi,
        "macros_today": {
            "protein_g": float(protein_today),
            "carbs_g": float(carbs_today),
            "fat_g": float(fat_today),
        },
    }
    result = await get_recommendations(
        user_data, today_foods, water_glasses=water_glasses, last_meal_time=last_meal_time
    )

    # Hard guard: if AI suggests a next meal far above remaining calories, clamp it
    consumed_today = sum((log.calories or 0) for log in logs)
    remaining = daily_goal - consumed_today
    try:
        next_meal = result.get("next_meal") or {}
        total_calories = next_meal.get("total_calories")
        if isinstance(total_calories, (int, float)) and remaining is not None:
            if total_calories > remaining + 50:
                clamped = max(0, int(remaining))
                next_meal["total_calories"] = clamped
                result["next_meal"] = next_meal
    except Exception:
        # If the shape is not as expected, keep the original result
        pass
    rec = Recommendation(user_id=user_id, content=json.dumps(result))
    db.add(rec)
    db.commit()
    return result


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if body.name is not None:
        user.name = body.name
    if body.age is not None:
        user.age = body.age
    if body.weight_kg is not None:
        user.weight_kg = body.weight_kg
    if body.height_cm is not None:
        user.height_cm = body.height_cm
    if body.goal is not None:
        user.goal = body.goal
    if any([
        body.weight_kg is not None,
        body.age is not None,
        body.height_cm is not None,
        body.goal is not None,
    ]):
        age = user.age or 30
        weight_kg = user.weight_kg or 70
        height_cm = user.height_cm or 170
        gender = user.gender or "other"
        goal = user.goal or "maintain"
        user.daily_calorie_goal = calculate_daily_calories(
            age, weight_kg, height_cm, gender, goal
        )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/weight")
async def log_weight(
    req: WeightLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    entry = WeightLog(user_id=current_user.id, weight_kg=req.weight_kg)
    db.add(entry)
    db.commit()
    user = db.query(User).filter(User.id == current_user.id).first()
    if user:
        user.weight_kg = req.weight_kg
        db.commit()
    return {"status": "ok"}


@router.get("/weight/{user_id}")
async def get_weight_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    logs = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id)
        .order_by(WeightLog.logged_at.desc())
        .limit(12)
        .all()
    )
    return [
        {"weight": l.weight_kg, "date": l.logged_at.strftime("%Y-%m-%d")}
        for l in logs
    ]
