from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import FoodLog, User, ScanLog
from openai_service import scan_food_image
from schemas import FoodLogResponse, FoodScanRequest, FoodScanResponse, FoodItem, FoodLogUpdate, ManualLogRequest

router = APIRouter()


@router.post("/scan", response_model=FoodScanResponse)
async def scan_food(
    request: FoodScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to scan for this user",
        )
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not (request.image_base64 and request.image_base64.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image data is required",
        )
    # Enforce per-user daily scan limit (50 scans/day)
    today = date.today()
    scan_log = (
        db.query(ScanLog)
        .filter(ScanLog.user_id == request.user_id, ScanLog.scan_date == today)
        .first()
    )
    if scan_log:
        if scan_log.scan_count >= 50:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily scan limit reached (50 scans/day). Try again tomorrow.",
            )
        scan_log.scan_count += 1
    else:
        scan_log = ScanLog(user_id=request.user_id, scan_date=today, scan_count=1)
        db.add(scan_log)
    db.commit()
    scan_result = await scan_food_image(request.image_base64)
    items = scan_result.get("items") or []
    if not items:
        return FoodScanResponse(
            items=[],
            total_calories=0.0,
            total_protein=0.0,
            total_carbs=0.0,
            total_fat=0.0,
            calorie_range_min=0.0,
            calorie_range_max=0.0,
            confidence=0.0,
            questions_for_user=[],
        )
    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    log_ids: list[int] = []
    for item in items:
        calories = float(item.get("calories") or 0)
        protein_g = float(item.get("protein_g") or 0)
        carbs_g = float(item.get("carbs_g") or 0)
        fat_g = float(item.get("fat_g") or 0)
        total_calories += calories
        total_protein += protein_g
        total_carbs += carbs_g
        total_fat += fat_g
        log_entry = FoodLog(
            user_id=request.user_id,
            food_name=item.get("food_name", "Unknown"),
            quantity_g=float(item.get("quantity_g") or 0),
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            meal_type=request.meal_type,
            scan_time=datetime.utcnow(),
        )
        db.add(log_entry)
        db.flush()
        log_ids.append(log_entry.id)
    db.commit()
    item_schemas: list[FoodItem] = []
    calorie_range_min = float(scan_result.get("calorie_range_min") or 0.0)
    calorie_range_max = float(scan_result.get("calorie_range_max") or 0.0)
    confidence = float(scan_result.get("confidence") or 0.0)
    questions_for_user = scan_result.get("questions_for_user") or []

    # Attach the same AI metadata to each item schema; per-item fields can be
    # refined later if needed.
    for raw_item, log_id in zip(items, log_ids):
        item_schemas.append(
            FoodItem(
                id=log_id,
                food_name=raw_item.get("food_name", "Unknown"),
                quantity_g=float(raw_item.get("quantity_g") or 0),
                calories=float(raw_item.get("calories") or 0),
                protein_g=float(raw_item.get("protein_g") or 0),
                carbs_g=float(raw_item.get("carbs_g") or 0),
                fat_g=float(raw_item.get("fat_g") or 0),
            )
        )

    # Persist AI metadata per logged row so the UI can show confidence later
    if confidence or calorie_range_min or calorie_range_max:
        for log_id in log_ids:
            db.query(FoodLog).filter(FoodLog.id == log_id).update(
                {
                    "ai_confidence": confidence or 0.0,
                    "calorie_range_min": calorie_range_min or 0.0,
                    "calorie_range_max": calorie_range_max or 0.0,
                }
            )
        db.commit()
    return FoodScanResponse(
        items=item_schemas,
        total_calories=total_calories,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        calorie_range_min=calorie_range_min or total_calories,
        calorie_range_max=calorie_range_max or total_calories,
        confidence=confidence or 0.0,
        questions_for_user=questions_for_user,
    )


@router.get("/log/today/{user_id}")
async def get_today_log(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this log",
        )
    today = date.today()
    logs = (
        db.query(FoodLog)
        .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == today)
        .order_by(FoodLog.scan_time)
        .all()
    )
    breakfast = []
    lunch = []
    dinner = []
    snack = []
    totals_cal = 0.0
    totals_protein = 0.0
    totals_carbs = 0.0
    totals_fat = 0.0
    for log in logs:
        resp = FoodLogResponse.model_validate(log)
        if log.meal_type == "breakfast":
            breakfast.append(resp)
        elif log.meal_type == "lunch":
            lunch.append(resp)
        elif log.meal_type == "dinner":
            dinner.append(resp)
        else:
            snack.append(resp)
        totals_cal += log.calories or 0
        totals_protein += log.protein_g or 0
        totals_carbs += log.carbs_g or 0
        totals_fat += log.fat_g or 0
    return {
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
        "snack": snack,
        "totals": {
            "calories": totals_cal,
            "protein_g": totals_protein,
            "carbs_g": totals_carbs,
            "fat_g": totals_fat,
            "item_count": len(logs),
        },
    }


@router.post("/log/manual")
async def manual_log(
    request: ManualLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    log = FoodLog(
        user_id=current_user.id,
        food_name=request.food_name,
        calories=request.calories,
        protein_g=request.protein_g,
        carbs_g=request.carbs_g,
        fat_g=request.fat_g,
        quantity_g=request.quantity_g,
        meal_type=request.meal_type,
        scan_time=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"status": "ok", "log_id": log.id}


@router.get("/log/date/{user_id}/{log_date}")
async def get_log_by_date(
    user_id: int,
    log_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this log",
        )
    try:
        target_date = date.fromisoformat(log_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )
    logs = (
        db.query(FoodLog)
        .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == target_date)
        .order_by(FoodLog.scan_time)
        .all()
    )
    breakfast: list[FoodLogResponse] = []
    lunch: list[FoodLogResponse] = []
    dinner: list[FoodLogResponse] = []
    snack: list[FoodLogResponse] = []
    totals_cal = 0.0
    totals_protein = 0.0
    totals_carbs = 0.0
    totals_fat = 0.0
    for log in logs:
        resp = FoodLogResponse.model_validate(log)
        if log.meal_type == "breakfast":
            breakfast.append(resp)
        elif log.meal_type == "lunch":
            lunch.append(resp)
        elif log.meal_type == "dinner":
            dinner.append(resp)
        else:
            snack.append(resp)
        totals_cal += log.calories or 0
        totals_protein += log.protein_g or 0
        totals_carbs += log.carbs_g or 0
        totals_fat += log.fat_g or 0
    return {
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
        "snack": snack,
        "totals": {
            "calories": totals_cal,
            "protein_g": totals_protein,
            "carbs_g": totals_carbs,
            "fat_g": totals_fat,
            "item_count": len(logs),
        },
    }


@router.delete("/log/{log_id}")
async def delete_log_entry(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log_entry = db.query(FoodLog).filter(FoodLog.id == log_id).first()
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found",
        )
    if log_entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this entry",
        )
    db.delete(log_entry)
    db.commit()
    return {"deleted": True, "log_id": log_id}


@router.patch("/log/{log_id}", response_model=FoodLogResponse)
async def update_log_entry(
    log_id: int,
    body: FoodLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log_entry = db.query(FoodLog).filter(FoodLog.id == log_id).first()
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found",
        )
    if log_entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this entry",
        )
    if body.quantity_g is not None:
        log_entry.quantity_g = body.quantity_g
    if body.calories is not None:
        log_entry.calories = body.calories
    if body.protein_g is not None:
        log_entry.protein_g = body.protein_g
    if body.carbs_g is not None:
        log_entry.carbs_g = body.carbs_g
    if body.fat_g is not None:
        log_entry.fat_g = body.fat_g
    db.commit()
    db.refresh(log_entry)
    return FoodLogResponse.model_validate(log_entry)


@router.get("/log/history/{user_id}")
async def get_log_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this history",
        )
    result = []
    today = date.today()
    for i in range(7):
        d = today - timedelta(days=i)
        row = (
            db.query(
                func.coalesce(func.sum(FoodLog.calories), 0).label("total_calories"),
                func.count(FoodLog.id).label("items_count"),
            )
            .filter(FoodLog.user_id == user_id, func.date(FoodLog.scan_time) == d)
        ).first()
        total_cal = float(row.total_calories) if row else 0.0
        count = int(row.items_count) if row else 0
        result.append({
            "date": d.isoformat(),
            "total_calories": total_cal,
            "items_count": count,
        })
    return result
