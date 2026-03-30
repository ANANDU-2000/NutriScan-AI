from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    age: int = Field(..., ge=10, le=120)
    weight_kg: float = Field(..., ge=20, le=300)
    height_cm: float = Field(..., ge=50, le=250)
    gender: str = Field(..., pattern="^(male|female|other)$")
    goal: str = Field(..., pattern="^(lose_weight|gain_muscle|maintain)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    age: int | None = None
    weight_kg: float | None = None
    height_cm: float | None = None
    gender: str | None = None
    goal: str | None = None
    daily_calorie_goal: int | None = None
    created_at: datetime | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    weight_kg: float | None = None
    height_cm: float | None = None
    goal: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class FoodScanRequest(BaseModel):
    image_base64: str = Field(..., min_length=100, max_length=5_000_000)
    meal_type: str = Field(default="lunch", pattern="^(breakfast|lunch|dinner|snack)$")
    user_id: int = Field(..., ge=1)


class FoodItem(BaseModel):
    id: int | None = None
    food_name: str
    quantity_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class FoodScanResponse(BaseModel):
    items: list[FoodItem]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    calorie_range_min: float | None = None
    calorie_range_max: float | None = None
    confidence: float | None = None
    questions_for_user: list[str] | None = None


class FoodLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    food_name: str
    quantity_g: float | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    meal_type: str | None = None
    scan_time: datetime | None = None
    ai_confidence: float | None = None
    calorie_range_min: float | None = None
    calorie_range_max: float | None = None


class FoodLogUpdate(BaseModel):
    quantity_g: float | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None


class ManualLogRequest(BaseModel):
    user_id: int
    food_name: str
    calories: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    quantity_g: float = 100
    meal_type: str = "lunch"


class StatsResponse(BaseModel):
    bmi: float
    bmi_category: str
    daily_goal: int
    consumed_today: float
    remaining_today: float
    streak_days: int
    last_7_days: list[dict]


class RecommendContext(BaseModel):
    water_glasses: int = Field(default=0, ge=0, le=8)
