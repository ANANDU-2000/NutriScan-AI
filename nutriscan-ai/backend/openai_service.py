import json
import os
import re
from typing import Any, List

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()

SYSTEM_PROMPT_SCAN = """You are an expert nutritionist and food analyst. Your job is to identify food in images.

CRITICAL RULES:
1. Return ONLY valid JSON. No explanation, no markdown, no code fences, no text before or after.
2. If you see ANY food at all — even one piece, one item, partial plate, snack, fruit, drink — you MUST return at least one item. NEVER return empty items[] unless the image is completely blank, pure black, or shows zero food.
3. Single item = return 1 item. One banana, one idli, one slice of bread, one apple — all valid. One piece of any food = return it.
4. Support ALL food types: Indian (Kerala, North Indian, South Indian), Western, snacks, fruits, vegetables, drinks, packaged food, street food, restaurant meals, home-cooked — anything edible.
5. Use USDA nutrition values. Be realistic: most portions 50–500g. No single item > 2000 kcal.
6. Use short food_name values (e.g. "rice (1 cup)", "banana (1 medium)", "parotta (2 pcs)").
7. When unsure or image is blurry, STILL return your best guess with conservative estimates. Prefer returning items over empty.

Common Kerala/South Indian: puttu, idli, dosa, appam, rice, sambar, rasam, avial, fish curry, chicken curry, parotta, kadala curry, payasam, banana chips, coconut chutney."""

USER_MESSAGE_SCAN = """Analyze this food image.

Return a JSON object with exactly these keys:
- items: array of objects, each with: food_name, quantity_g, calories, protein_g, carbs_g, fat_g
- calorie_range_min, calorie_range_max: numbers
- confidence: 0–1
- questions_for_user: array of short strings

RULE: If you see ANY food (even one piece, one item, any type), return at least one item. Empty items[] ONLY when image shows zero food (blank, black, or no food visible).

Return ONLY the JSON object. No other text."""

SYSTEM_PROMPT_RECOMMEND = """You are a certified nutritionist AI specializing in South Indian and Kerala dietary patterns.

You know Kerala cuisine deeply: rice, sambar, rasam, avial, fish curry, chicken curry, puttu, idli, dosa, appam, stew, biryani, payasam, banana chips, coconut dishes, Kerala sadya.

Rules:
1. Return ONLY valid JSON. No markdown. No explanation. No code fences.
2. Suggest realistic foods for Kerala/South Indian households.
3. Prefer: rice meals, dal, vegetables, fish, chicken, eggs.
4. Match suggestions to time of day (breakfast vs lunch vs dinner).
5. If user ate biryani or fried food: suggest lighter next meal.
6. If fat is HIGH: NEVER suggest coconut curry, fried items, ghee.
7. If carbs are HIGH: NEVER suggest rice, bread, roti, starchy food.
8. Always respect remaining calorie budget — next meal must fit within it.
9. Use simple direct language. No generic phrases like "balanced diet"."""


def _get_client() -> AsyncOpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    return AsyncOpenAI(api_key=key)


def _strip_json_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    return raw.strip()


def _extract_json(raw: str) -> dict | list | None:
    """Extract JSON from GPT response even when wrapped in extra text."""
    raw = _strip_json_fences(raw.strip())
    # Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # GPT sometimes returns "I cannot see... Here is the JSON: {...}" — find first { or [
    start_obj = raw.find("{")
    start_arr = raw.find("[")
    if start_obj >= 0 and (start_arr < 0 or start_obj < start_arr):
        # Find matching closing brace
        depth = 0
        for i in range(start_obj, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start_obj : i + 1])
                    except json.JSONDecodeError:
                        break
    if start_arr >= 0:
        depth = 0
        for i in range(start_arr, len(raw)):
            if raw[i] == "[":
                depth += 1
            elif raw[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        arr = json.loads(raw[start_arr : i + 1])
                        return {"items": arr} if isinstance(arr, list) else arr
                    except json.JSONDecodeError:
                        break
    return None


class FoodItemAI(BaseModel):
    food_name: str
    quantity_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class FoodScanAIOutput(BaseModel):
    items: List[FoodItemAI]
    calorie_range_min: float = 0.0
    calorie_range_max: float = 0.0
    confidence: float = 0.0
    questions_for_user: List[str] = []


USER_MESSAGE_SCAN_RETRY = """This image may contain food. List EVERY food item you can see — even one piece, one item, snack, fruit, or drink. If you see anything edible, return at least one item with your best estimate. Return ONLY valid JSON with items, calorie_range_min, calorie_range_max, confidence, questions_for_user."""


async def scan_food_image(image_base64: str) -> dict:
    if not image_base64 or not image_base64.strip():
        return {"items": [], "calorie_range_min": 0.0, "calorie_range_max": 0.0, "confidence": 0.0, "questions_for_user": []}
    try:
        client = _get_client()
        url = f"data:image/jpeg;base64,{image_base64}"
        last_error: Exception | None = None
        response = None
        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    temperature=0.2,
                    max_tokens=1200,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_SCAN},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": USER_MESSAGE_SCAN},
                                {"type": "image_url", "image_url": {"url": url, "detail": "high"}},
                            ],
                        },
                    ],
                )
                break
            except APIError as e:
                last_error = e
                if attempt < 2:
                    continue
                raise
        if response is None and last_error is not None:
            raise last_error
        raw = response.choices[0].message.content
        if not raw:
            return {"items": [], "calorie_range_min": 0.0, "calorie_range_max": 0.0, "confidence": 0.0, "questions_for_user": []}
        data = _extract_json(raw)
        if data is None:
            raise HTTPException(status_code=422, detail="Could not parse AI response from AI model")
        # If first attempt returned empty items, retry once with stronger prompt (image may have food)
        items_first = (data.get("items") if isinstance(data, dict) else []) or []
        if not items_first and isinstance(data, dict):
            try:
                retry_resp = await client.chat.completions.create(
                    model="gpt-4o",
                    temperature=0.3,
                    max_tokens=1200,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_SCAN},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": USER_MESSAGE_SCAN_RETRY},
                                {"type": "image_url", "image_url": {"url": url, "detail": "high"}},
                            ],
                        },
                    ],
                )
                retry_raw = retry_resp.choices[0].message.content
                if retry_raw:
                    retry_data = _extract_json(retry_raw)
                    if retry_data and isinstance(retry_data, dict):
                        retry_items = retry_data.get("items") or []
                        if retry_items:
                            data = retry_data
            except Exception:
                pass
        # Backwards compatibility: if the model returned a bare array, wrap it
        if isinstance(data, list):
            wrapped: dict[str, Any] = {"items": data}
        elif isinstance(data, dict):
            wrapped = data
        else:
            wrapped = {"items": []}
        try:
            parsed = FoodScanAIOutput.model_validate(wrapped)
        except ValidationError:
            raise HTTPException(status_code=422, detail="Could not parse AI response from AI model")

        # Sanity checks: clamp impossible values, filter invalid items
        clean_items: list[dict[str, Any]] = []
        for item in parsed.items:
            food_name = (item.food_name or "").strip() or "Unknown food"
            quantity_g = max(1.0, float(item.quantity_g or 0))
            calories = max(0.0, min(2000.0, float(item.calories or 0)))
            protein_g = max(0.0, min(100.0, float(item.protein_g or 0)))
            carbs_g = max(0.0, float(item.carbs_g or 0))
            fat_g = max(0.0, float(item.fat_g or 0))
            clean_items.append(
                {
                    "food_name": food_name,
                    "quantity_g": quantity_g,
                    "calories": calories,
                    "protein_g": protein_g,
                    "carbs_g": carbs_g,
                    "fat_g": fat_g,
                }
            )

        result = {
            "items": clean_items,
            "calorie_range_min": max(0.0, float(parsed.calorie_range_min)),
            "calorie_range_max": max(0.0, float(parsed.calorie_range_max)),
            "confidence": float(parsed.confidence),
            "questions_for_user": parsed.questions_for_user,
        }
        return result
    except APIError:
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Could not parse AI response from AI model")
    except HTTPException:
        raise
    except Exception:
        # Do not leak low-level library errors to the client
        raise HTTPException(status_code=500, detail="AI scan failed. Please try again.")


def _build_recommend_user_prompt(
    name: str,
    age: int | float,
    gender: str,
    weight_kg: float,
    height_cm: float,
    goal: str,
    daily_calorie_goal: int,
    bmi: float,
    food_list: str,
    consumed: float,
    remaining: float,
    protein_remaining: float,
    protein_today: float,
    protein_target: float,
    current_time: str,
    last_meal_time: str | None,
    water_intake_ml: int,
    time_of_day: str,
    next_meal: str,
    carbs_today: float,
    fat_today: float,
    carbs_target: float,
    fat_target: float,
    warning_text: str,
) -> str:
    return f"""User Profile:
Name: {name}, Age: {age}, Gender: {gender}
Weight: {weight_kg}kg, Height: {height_cm}cm, BMI: {bmi:.1f}
Goal: {goal}, Daily Calorie Target: {daily_calorie_goal} kcal

Current Time: {time_of_day}
Next meal should be: {next_meal}

Today's Food Log:
{food_list}
Consumed: {consumed:.0f} kcal | Remaining: {remaining:.0f} kcal
{warning_text}

IMPORTANT RULES FOR YOUR RESPONSE:
- If fat is HIGH, do NOT suggest fried food, coconut curry, or oily dishes
- If carbs are HIGH, do NOT suggest rice, bread, or starchy food
- If protein is HIGH, do NOT suggest more meat or eggs
- Suggest only what fits the REMAINING {remaining:.0f} kcal
- Suggest realistic Kerala/South Indian foods for {next_meal}
- Keep suggestion portions realistic (not more than {min(max(0, remaining), 600):.0f} kcal for next meal)

Return this EXACT JSON structure:
{{
  "greeting": "short encouraging message mentioning their name and goal (1 sentence)",
  "next_meal": {{
    "meal_type": "{next_meal}",
    "suggestions": [
      {{"food": "name", "portion": "quantity", "calories": number, "reason": "why this fits"}}
    ],
    "total_calories": number
  }},
  "foods_to_avoid_today": ["food1", "food2"],
  "health_tip": "one specific actionable tip for their goal",
  "water_reminder": "water tip",
  "goal_progress": "progress message"
}}"""


DEFAULT_RECOMMENDATIONS = {
    "greeting": "Here are your recommendations",
    "next_meal": {
        "meal_type": "snack",
        "suggestions": [],
        "total_calories": 0,
    },
    "foods_to_avoid_today": [],
    "health_tip": "Stay hydrated and eat balanced meals.",
    "water_reminder": "Remember to drink water throughout the day.",
    "goal_progress": "Keep logging to see your progress.",
}


async def get_recommendations(
    user_data: dict,
    today_foods: list[dict],
    water_glasses: int = 0,
    last_meal_time: str | None = None,
) -> dict:
    try:
        from datetime import datetime

        consumed = sum((f.get("calories") or 0) for f in today_foods)
        daily_goal = user_data.get("daily_calorie_goal") or 2000
        remaining = daily_goal - consumed
        if today_foods:
            food_list = "\n".join(
                f"- {f.get('meal_type', 'meal')}: {f.get('food_name', '')} ({f.get('quantity_g', 0):.0f}g, {f.get('calories', 0):.0f} kcal)"
                for f in today_foods
            )
        else:
            food_list = "Nothing logged yet today"

        macros_today = user_data.get("macros_today") or {}
        protein_today = float(macros_today.get("protein_g") or 0.0)
        carbs_today = float(macros_today.get("carbs_g") or 0.0)
        fat_today = float(macros_today.get("fat_g") or 0.0)
        protein_target = daily_goal * 0.30 / 4.0
        carbs_target = daily_goal * 0.50 / 4.0
        fat_target = daily_goal * 0.20 / 9.0
        protein_remaining = max(0.0, protein_target - protein_today)
        water_ml = water_glasses * 250
        now = datetime.utcnow()
        hour = now.hour
        current_time = now.strftime("%H:%M") + " " + ("AM" if hour < 12 else "PM")
        if hour < 11:
            time_of_day = "morning (breakfast time)"
            next_meal = "breakfast"
        elif hour < 15:
            time_of_day = "afternoon (lunch time)"
            next_meal = "lunch"
        elif hour < 18:
            time_of_day = "late afternoon (snack time)"
            next_meal = "snack"
        elif hour < 21:
            time_of_day = "evening (dinner time)"
            next_meal = "dinner"
        else:
            time_of_day = "night"
            next_meal = "light snack or nothing"
        warnings = []
        if fat_today > fat_target * 1.2:
            warnings.append(f"Fat is HIGH ({fat_today:.0f}g vs {fat_target:.0f}g target)")
        if carbs_today > carbs_target * 1.2:
            warnings.append(f"Carbs are HIGH ({carbs_today:.0f}g vs {carbs_target:.0f}g target)")
        if protein_today > protein_target * 1.2:
            warnings.append(f"Protein is HIGH ({protein_today:.0f}g vs {protein_target:.0f}g target)")
        warning_text = ""
        if warnings:
            warning_text = "\n⚠️ MACRO WARNINGS (DO NOT recommend more of these):\n" + "\n".join(warnings)

        prompt = _build_recommend_user_prompt(
            name=user_data.get("name", "User"),
            age=user_data.get("age", 30),
            gender=user_data.get("gender", "other"),
            weight_kg=user_data.get("weight_kg", 70),
            height_cm=user_data.get("height_cm", 170),
            goal=user_data.get("goal", "maintain"),
            daily_calorie_goal=daily_goal,
            bmi=user_data.get("bmi", 22.0),
            food_list=food_list,
            consumed=consumed,
            remaining=remaining,
            protein_remaining=protein_remaining,
            protein_today=protein_today,
            protein_target=protein_target,
            current_time=current_time,
            last_meal_time=last_meal_time,
            water_intake_ml=water_ml,
            time_of_day=time_of_day,
            next_meal=next_meal,
            carbs_today=carbs_today,
            fat_today=fat_today,
            carbs_target=carbs_target,
            fat_target=fat_target,
            warning_text=warning_text,
        )

        client = _get_client()
        last_error: Exception | None = None
        response = None
        for attempt in range(2):
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    temperature=0.7,
                    max_tokens=800,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_RECOMMEND},
                        {"role": "user", "content": prompt},
                    ],
                )
                break
            except APIError as e:
                last_error = e
                if attempt == 0:
                    continue
                raise
        if response is None and last_error is not None:
            raise last_error
        raw = response.choices[0].message.content
        if not raw:
            return DEFAULT_RECOMMENDATIONS.copy()
        raw = _strip_json_fences(raw.strip())
        data = json.loads(raw)
        if not isinstance(data, dict):
            return DEFAULT_RECOMMENDATIONS.copy()
        return data
    except APIError:
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Could not parse AI response")
    except Exception:
        raise HTTPException(status_code=500, detail="AI recommendations failed. Please try again.")
