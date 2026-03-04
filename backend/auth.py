import os
from datetime import datetime, timedelta
from time import time

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import TokenWithUser, UserCreate, UserLogin, UserResponse

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "nutriscan_jwt_secret_2026_change_this")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Use sha256_crypt instead of bcrypt to avoid Python 3.14 + bcrypt backend issues
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = HTTPBearer(auto_error=False)

# Very simple in-memory tracker for failed login attempts per email.
# Suitable for a demo; for production, replace with a persistent store.
FAILED_LOGIN_ATTEMPTS: dict[str, list[float]] = {}


def _check_login_rate_limit(email: str) -> None:
    now = time()
    window_seconds = 60.0
    max_attempts = 5
    attempts = FAILED_LOGIN_ATTEMPTS.get(email, [])
    # Keep only attempts within the last window
    attempts = [t for t in attempts if now - t <= window_seconds]
    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a minute and try again.",
        )
    FAILED_LOGIN_ATTEMPTS[email] = attempts


def calculate_daily_calories(
    age: int, weight_kg: float, height_cm: float, gender: str, goal: str
) -> int:
    if age <= 0 or weight_kg <= 0 or height_cm <= 0:
        return 2000
    if gender == "male":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    elif gender == "female":
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    else:
        male_bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        female_bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
        bmr = (male_bmr + female_bmr) / 2
    tdee = bmr * 1.375
    if goal == "lose_weight":
        tdee -= 500
    elif goal == "gain_muscle":
        tdee += 300
    return max(1200, int(tdee))


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user_id = int(user_id_str)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, please login again",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user


router = APIRouter()


@router.post("/register", response_model=TokenWithUser)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    age = user_in.age if user_in.age is not None else 30
    weight_kg = user_in.weight_kg if user_in.weight_kg is not None else 70.0
    height_cm = user_in.height_cm if user_in.height_cm is not None else 170.0
    gender = user_in.gender or "other"
    goal = user_in.goal or "maintain"
    daily_calorie_goal = calculate_daily_calories(age, weight_kg, height_cm, gender, goal)
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        age=age,
        weight_kg=weight_kg,
        height_cm=height_cm,
        gender=gender,
        goal=goal,
        daily_calorie_goal=daily_calorie_goal,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return TokenWithUser(access_token=access_token, token_type="bearer", user=user_response)


@router.post("/login", response_model=TokenWithUser)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    _check_login_rate_limit(credentials.email)
    user = db.query(User).filter(User.email == credentials.email).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        # Record failed attempt for basic brute-force protection
        FAILED_LOGIN_ATTEMPTS.setdefault(credentials.email, []).append(time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return TokenWithUser(access_token=access_token, token_type="bearer", user=user_response)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
