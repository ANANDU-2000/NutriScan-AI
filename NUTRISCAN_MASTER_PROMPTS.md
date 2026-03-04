# 🥗 NUTRISCAN AI — MASTER CURSOR PROMPTS
### Real-Time Food Scanning & Nutrition Advisory App
### Ameya. K. Anil | NCE22AM006 | Nehru College of Engineering | B.Tech CSE AI & ML
### Supervisor: Dr. Sajitha. A. S

---

## ⚡ HOW TO USE THIS FILE — READ FIRST

1. Open Cursor Pro → File → Open Folder → select `nutriscan-ai/`
2. Cursor will automatically read `.cursorrules` (the rules file) — this means it knows the full project
3. Press `Ctrl+L` to open Cursor Chat
4. Copy each **PROMPT block** below in exact order — STEP 1 first, then STEP 2, etc.
5. **Wait for Cursor to finish writing ALL files** before copying the next prompt
6. If Cursor writes incomplete code, type: `You left the function incomplete. Finish it fully.`
7. If there is an error running the app, paste the exact error text and type: `Fix this exact error.`
8. **Never skip a step** — every step depends on the one before it

---

## 📁 CREATE THIS FOLDER STRUCTURE FIRST (Do This Manually)

```
nutriscan-ai/               ← your project root folder
├── .cursorrules            ← already created, put it here
├── backend/                ← create this folder
└── frontend/               ← create this folder
```

Then open `nutriscan-ai/` in Cursor.

---

## 🔑 CREATE YOUR .env FILE (Do This Before Any Prompt)

Create a file at `backend/.env` and paste exactly this:

```env
OPENAI_API_KEY=sk-proj-PASTE_YOUR_REAL_KEY_HERE
SECRET_KEY=nutriscan_jwt_secret_2026_change_this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./nutriscan.db
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
DEBUG=True
```

**Get your OpenAI key:**
→ Go to https://platform.openai.com/api-keys
→ Click "Create new secret key" → copy the key starting with `sk-proj-`
→ Paste it in the .env above replacing `sk-proj-PASTE_YOUR_REAL_KEY_HERE`
→ Go to https://platform.openai.com/account/limits → set Monthly Budget = $5 (safety limit)

---

## ✅ TASK CHECKLIST — TICK AS YOU COMPLETE EACH STEP

```
BACKEND
[ ] STEP 1  — database.py + models.py + schemas.py + requirements.txt
[ ] STEP 2  — main.py (FastAPI app, CORS, startup)
[ ] STEP 3  — auth.py (register, login, JWT, password hash)
[ ] STEP 4  — openai_service.py (food scan + recommendations)
[ ] STEP 5  — food_routes.py (scan endpoint + food log CRUD)
[ ] STEP 6  — user_routes.py (stats + recommendations + profile update)
[ ] STEP 7  — Wire everything in main.py + run backend, test /health

FRONTEND
[ ] STEP 8  — index.html skeleton (CSS system + JS helpers + screen shells + bottom nav)
[ ] STEP 9  — Landing + Login + Register + Voice Onboarding + Profile Setup screens
[ ] STEP 10 — Dashboard screen (calorie ring + BMI + macros + water)
[ ] STEP 11 — Scanner screen (live camera + capture + results sheet)
[ ] STEP 12 — Food Log + Recommendations screens
[ ] STEP 13 — Progress charts + Reminders + PDF export + Settings + final polish

DONE
[ ] STEP 14 — Full test on desktop browser
[ ] STEP 15 — Mobile browser test
```

---
---
---

# ════════════════════════════════════
# BACKEND — STEPS 1 TO 7
# ════════════════════════════════════

---

## STEP 1 — DATABASE, MODELS, SCHEMAS

> Copy everything between the triple dashes and paste into Cursor Chat

---
I am building NutriScan AI. My .cursorrules file already has the full project context.

Create these 3 files in backend/ exactly as specified:

**backend/database.py**
- Import create_engine, sessionmaker, declarative_base from sqlalchemy
- DATABASE_URL = "sqlite:///./nutriscan.db"
- engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
- SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
- Base = declarative_base()
- def get_db(): yields SessionLocal(), always closes in finally block

**backend/models.py**
Import Base from database. Create 3 SQLAlchemy models:

Model User (tablename: users):
  id: Integer, primary key, index
  name: String(100), nullable=False
  email: String(200), unique=True, index=True, nullable=False
  password_hash: String(256), nullable=False
  age: Integer
  weight_kg: Float
  height_cm: Float
  gender: String(10)
  goal: String(20)  [lose_weight / gain_muscle / maintain]
  daily_calorie_goal: Integer
  created_at: DateTime, default=datetime.utcnow
  is_active: Boolean, default=True
  food_logs: relationship("FoodLog", back_populates="user")
  recommendations: relationship("Recommendation", back_populates="user")

Model FoodLog (tablename: food_logs):
  id: Integer, primary key, index
  user_id: Integer, ForeignKey("users.id"), index=True, nullable=False
  food_name: String(200), nullable=False
  quantity_g: Float
  calories: Float
  protein_g: Float
  carbs_g: Float
  fat_g: Float
  meal_type: String(20)
  scan_time: DateTime, default=datetime.utcnow
  user: relationship("User", back_populates="food_logs")

Model Recommendation (tablename: recommendations):
  id: Integer, primary key
  user_id: Integer, ForeignKey("users.id"), nullable=False
  content: Text  [stores JSON string]
  created_at: DateTime, default=datetime.utcnow
  user: relationship("User", back_populates="recommendations")

**backend/schemas.py**
Create Pydantic v2 models (from pydantic import BaseModel, EmailStr):

UserCreate: name(str), email(EmailStr), password(str min 6 chars), age(int), weight_kg(float), height_cm(float), gender(str), goal(str)
UserLogin: email(EmailStr), password(str)
UserResponse: id, name, email, age, weight_kg, height_cm, gender, goal, daily_calorie_goal, created_at — Config model_config = ConfigDict(from_attributes=True)
UserUpdate: name(optional str), age(optional int), weight_kg(optional float), height_cm(optional float), goal(optional str)
Token: access_token(str), token_type(str) = "bearer"
TokenWithUser: access_token, token_type, user(UserResponse)
FoodScanRequest: image_base64(str), meal_type(str default "lunch"), user_id(int)
FoodItem: food_name(str), quantity_g(float), calories(float), protein_g(float), carbs_g(float), fat_g(float)
FoodScanResponse: items(list[FoodItem]), total_calories(float), total_protein(float), total_carbs(float), total_fat(float)
FoodLogResponse: id, food_name, quantity_g, calories, protein_g, carbs_g, fat_g, meal_type, scan_time — from_attributes=True
StatsResponse: bmi(float), bmi_category(str), daily_goal(int), consumed_today(float), remaining_today(float), streak_days(int), last_7_days(list[dict])

**backend/requirements.txt**
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
python-dotenv==1.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
openai==1.51.0
pydantic==2.9.2
pydantic[email]==2.9.2
python-multipart==0.0.12
aiofiles==24.1.0
email-validator==2.2.0

Create all 4 files now. Make sure all imports are correct and cross-file references work.
---

---

## STEP 2 — MAIN.PY (FASTAPI APP)

> Copy and paste into Cursor Chat

---
Create backend/main.py:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("✅ NutriScan AI backend started")
    print(f"✅ OpenAI key loaded: {'YES' if os.getenv('OPENAI_API_KEY') else 'NO — CHECK .env'}")
    yield
    # Shutdown
    print("NutriScan AI shutting down")

app = FastAPI(
    title="NutriScan AI",
    version="1.0.0",
    description="Real-time food scanning and nutrition advisory API",
    lifespan=lifespan
)

# CORS — allow frontend on port 3000
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — import after app is defined to avoid circular imports
from auth import router as auth_router
from food_routes import router as food_router
from user_routes import router as user_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(food_router, prefix="/food", tags=["Food"])
app.include_router(user_router, prefix="/users", tags=["Users"])

@app.get("/")
async def root():
    return {"status": "NutriScan AI running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "database": "connected",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "MISSING — add to .env"
    }
```

Create this exactly. Do not change the import order or router prefix names.
---

---

## STEP 3 — AUTH.PY (REGISTER + LOGIN + JWT)

> Copy and paste into Cursor Chat

---
Create backend/auth.py with complete authentication. Follow these rules exactly:
- Read SECRET_KEY and ALGORITHM from os.getenv() — never hardcode
- Use passlib CryptContext with bcrypt scheme
- Use python-jose for JWT encode/decode
- Raise HTTPException with correct status codes for every error

Include these functions:

**def calculate_daily_calories(age, weight_kg, height_cm, gender, goal) -> int:**
  Harris-Benedict formula:
    male:   88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    female: 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    other: average of male and female
  Multiply by 1.375 (lightly active TDEE multiplier)
  Adjust: lose_weight → -500, gain_muscle → +300, maintain → no change
  Return max(1200, int(result))

**def get_password_hash(password: str) -> str**
**def verify_password(plain: str, hashed: str) -> bool**
**def create_access_token(data: dict) -> str:**
  Encode with SECRET_KEY, ALGORITHM, add expiry from ACCESS_TOKEN_EXPIRE_MINUTES env var

**def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)) -> User:**
  Decode JWT, get user_id from sub field, fetch User from DB
  Raise HTTP 401 "Could not validate credentials" if anything fails
  Raise HTTP 401 "Session expired, please login again" if token expired

**APIRouter with these endpoints:**

POST /auth/register (body: UserCreate):
  1. Check email exists → 400 "Email already registered"
  2. Hash password
  3. Calculate daily_calorie_goal
  4. Create and save User
  5. Create JWT token with sub=str(user.id)
  6. Return TokenWithUser schema

POST /auth/login (body: UserLogin):
  1. Find user by email → 401 "Invalid email or password"
  2. Verify password → 401 "Invalid email or password" (same message for security)
  3. Create JWT token
  4. Return TokenWithUser schema

GET /auth/me (requires token):
  Return current user as UserResponse
---

---

## STEP 4 — OPENAI_SERVICE.PY (ALL AI CALLS)

> Copy and paste into Cursor Chat

---
Create backend/openai_service.py. This file contains ALL OpenAI API interactions.
Rules: always use AsyncOpenAI, always strip markdown fences, always validate JSON type.

**async def scan_food_image(image_base64: str) -> list[dict]:**

Use this exact system prompt (do not change it):
```
You are an expert nutritionist and food analyst.
When shown a food image, identify every food item visible on the plate or in the bowl.
You MUST return ONLY valid JSON — no explanation, no markdown, no code fences.
Use USDA standard nutrition values for estimates.
Be realistic: most home-cooked meals are 150-450g total.
```

Use this exact user message (do not change it):
```
Analyze this food image. Return a JSON array where each element has exactly these keys:
food_name (string — be specific, e.g. "steamed white rice" not "rice"),
quantity_g (number — realistic weight in grams),
calories (number — total for that quantity),
protein_g (number),
carbs_g (number),
fat_g (number)

If no food is visible, return an empty array: []
Return ONLY the JSON array. No other text.
```

API call settings:
  model="gpt-4o"
  temperature=0.3
  max_tokens=1000
  image passed as image_url type with url="data:image/jpeg;base64,{image_base64}" detail="high"

After getting response:
  raw = response.choices[0].message.content.strip()
  Strip leading/trailing ``` and ```json using regex
  Parse JSON — if it fails, try to extract array with regex r'\[.*\]' using re.DOTALL
  If still fails, return []
  Validate result is a list — if not, return []
  Return the list

**async def get_recommendations(user_data: dict, today_foods: list[dict]) -> dict:**

user_data keys: name, age, gender, weight_kg, height_cm, goal, daily_calorie_goal, bmi

Build the prompt dynamically:
  consumed = sum of calories from today_foods
  remaining = daily_calorie_goal - consumed
  food_list = formatted string of each food: "- {meal_type}: {food_name} ({quantity_g}g, {calories} kcal)"
  if today_foods is empty: food_list = "Nothing logged yet today"

System prompt:
```
You are a certified nutritionist AI.
Give practical, realistic food recommendations suitable for Indian dietary preferences.
You MUST return ONLY valid JSON — no explanation, no markdown, no code fences.
```

User prompt (build dynamically with f-string):
```
User Profile:
Name: {name}, Age: {age}, Gender: {gender}
Weight: {weight_kg}kg, Height: {height_cm}cm, BMI: {bmi:.1f}
Goal: {goal}, Daily Calorie Target: {daily_calorie_goal} kcal

Today's Food:
{food_list}
Consumed: {consumed:.0f} kcal | Remaining: {remaining:.0f} kcal

Return a JSON object with exactly these keys:
greeting (string — encouraging, mention their name),
next_meal (object with: meal_type string, suggestions list of objects each having food string, portion string, calories int, reason string, total_calories int),
foods_to_avoid_today (list of strings),
health_tip (string — practical tip for their goal),
water_reminder (string),
goal_progress (string — e.g. "65% of daily goal reached — great pace!")
```

API call: model="gpt-4o", temperature=0.7, max_tokens=800
Strip fences, parse JSON, validate it's a dict
If parse fails, return a safe default dict with greeting="Here are your recommendations" and empty/default values for all keys

Both functions must be wrapped in try/except:
  On openai.APIError → raise HTTPException(503, "AI service temporarily unavailable")
  On json.JSONDecodeError → raise HTTPException(422, "Could not parse AI response")
  On any other exception → raise HTTPException(500, f"Unexpected error: {str(e)}")
---

---

## STEP 5 — FOOD_ROUTES.PY (SCAN + LOG ENDPOINTS)

> Copy and paste into Cursor Chat

---
Create backend/food_routes.py with an APIRouter.
All endpoints require authentication via get_current_user dependency from auth.py.

**POST /scan (maps to /food/scan in main.py):**
  Body: FoodScanRequest
  Steps:
    1. Verify user exists (fetch by request.user_id) → 404 if not found
    2. Verify token user matches request.user_id → 403 if mismatch
    3. Validate image_base64 is not empty → 400 "Image data is required"
    4. Call: items = await scan_food_image(request.image_base64)
    5. If items is empty list: return FoodScanResponse with empty items, all totals = 0.0
    6. For each item in items:
       - Create FoodLog(user_id=request.user_id, food_name=item["food_name"],
         quantity_g=item.get("quantity_g",0), calories=item.get("calories",0),
         protein_g=item.get("protein_g",0), carbs_g=item.get("carbs_g",0),
         fat_g=item.get("fat_g",0), meal_type=request.meal_type,
         scan_time=datetime.utcnow())
       - db.add(log_entry)
    7. db.commit()
    8. Calculate totals from all items
    9. Return FoodScanResponse

**GET /log/today/{user_id} (maps to /food/log/today/{user_id}):**
  Get all FoodLog records where user_id matches AND
  date(scan_time) == date.today() — use: func.date(FoodLog.scan_time) == date.today()
  Group by meal_type into a dict
  Calculate totals
  Return:
  {
    "breakfast": [FoodLogResponse, ...],
    "lunch": [...],
    "dinner": [...],
    "snack": [...],
    "totals": {
      "calories": float,
      "protein_g": float,
      "carbs_g": float,
      "fat_g": float,
      "item_count": int
    }
  }

**DELETE /log/{log_id} (maps to /food/log/{log_id}):**
  Fetch FoodLog by log_id → 404 if not found
  Verify log.user_id == current_user.id → 403 "Not authorized to delete this entry"
  db.delete(log_entry), db.commit()
  Return: {"deleted": True, "log_id": log_id}

**GET /log/history/{user_id} (maps to /food/log/history/{user_id}):**
  Get last 7 days of food logs for user
  For each of the past 7 days (today, yesterday, ...):
    Sum calories for that day
  Return: [{"date": "2026-03-02", "total_calories": 1820.5, "items_count": 8}, ...]
  Always return exactly 7 items even if 0 calories for some days
---

---

## STEP 6 — USER_ROUTES.PY (STATS + RECOMMENDATIONS + PROFILE)

> Copy and paste into Cursor Chat

---
Create backend/user_routes.py with an APIRouter.
All endpoints require authentication.

**GET /stats/{user_id} (maps to /users/stats/{user_id}):**
  Fetch user → 404 if not found
  Verify current_user.id == user_id → 403 if mismatch

  Calculate BMI:
    bmi = user.weight_kg / ((user.height_cm / 100) ** 2)
    bmi_category:
      bmi < 18.5  → "Underweight"
      bmi < 25    → "Normal"
      bmi < 30    → "Overweight"
      else        → "Obese"

  Get today's consumed calories:
    Query FoodLog where user_id=user_id and date(scan_time)=today
    Sum calories

  Calculate streak:
    For each of last 30 days starting from yesterday going backward:
      If there is at least 1 food log for that day: streak += 1
      Else: break
    If today has food logged: streak += 1

  Get last_7_days:
    Call same logic as /food/log/history/{user_id}

  Return StatsResponse

**POST /recommendations/{user_id} (maps to /users/recommendations/{user_id}):**
  Fetch user → 404 if not found
  Get today's food log (list of dicts with food_name, calories, quantity_g, meal_type)
  Calculate BMI
  Build user_data dict with: name, age, gender, weight_kg, height_cm, goal, daily_calorie_goal, bmi
  Call: result = await get_recommendations(user_data, today_foods)
  Save to Recommendation table: content=json.dumps(result)
  Return result dict directly (not wrapped)

**PUT /{user_id} (maps to /users/{user_id}):**
  Body: UserUpdate (all optional fields)
  Fetch user → 404 if not found
  Verify current_user.id == user_id → 403 if mismatch
  Update only fields that are not None in the request body
  If weight_kg, age, height_cm, or goal changed: recalculate daily_calorie_goal
  db.commit(), db.refresh(user)
  Return UserResponse
---

---

## STEP 7 — TEST THE BACKEND

> Copy and paste into Cursor Chat

---
The backend code is written. Now do the following:

1. Check every file for missing imports. Common issues:
   - date, datetime from datetime module
   - func from sqlalchemy
   - json module
   - All schemas imported in route files
   - All models imported where needed

2. Check main.py imports auth, food_routes, user_routes correctly

3. Create a simple backend/test_startup.py that:
   - Imports the FastAPI app from main
   - Prints "All imports OK"
   Run it: python test_startup.py
   Fix any import errors found

4. Show me the final main.py with all routers wired up

5. Show me the command to run the backend:
   cd nutriscan-ai/backend
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload

After running, open http://localhost:8000/health — it must return:
{"status":"ok","database":"connected","openai":"configured"}

Open http://localhost:8000/docs — all endpoints must appear.
If anything is wrong, fix it now before frontend starts.
---

---
---
---

# ════════════════════════════════════
# FRONTEND — STEPS 8 TO 13
# ════════════════════════════════════

---

## STEP 8 — HTML SKELETON + CSS SYSTEM + JS HELPERS

> Copy and paste into Cursor Chat

---
Create frontend/index.html — a complete single-file PWA.
This file will contain ALL CSS and ALL JavaScript. No separate files.

**HEAD section must include:**
```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#1A6B3C">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>NutriScan AI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
```

**CSS :root variables** (exact values from .cursorrules — copy all of them)

**Global CSS:**
```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; }
.screen { display: none; flex-direction: column; min-height: 100vh; padding-bottom: 75px; animation: none; }
.screen.active { display: flex; animation: slideIn 0.3s var(--transition); }
@keyframes slideIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
.card { background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px; }
.btn { height: 50px; border: none; border-radius: 25px; font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 600; cursor: pointer; transition: all var(--transition); width: 100%; }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: white; }
.btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-primary:active { transform: scale(0.98); }
.btn-outline { background: transparent; border: 2px solid var(--primary); color: var(--primary); }
.btn-danger { background: var(--error); color: white; }
input[type="text"], input[type="email"], input[type="password"], input[type="number"] {
  width: 100%; height: 50px; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 0 16px; font-family: 'Inter', sans-serif; font-size: 15px; outline: none;
  transition: border-color var(--transition); background: var(--surface); color: var(--text); }
input:focus { border-color: var(--primary); }
.badge { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-green { background: #E8F5E9; color: var(--primary); }
.badge-blue { background: #E3F2FD; color: #1565C0; }
.badge-orange { background: #FFF3E0; color: #E65100; }
.badge-red { background: #FFEBEE; color: #C62828; }
.divider { height: 1px; background: var(--border); margin: 16px 0; }
```

**Skeleton loading animation:**
```css
.skeleton { background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: var(--radius-sm); }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
```

**BODY contains:**
1. Loading overlay div (id="loading-overlay"): full screen, z-index 9999, green gradient background, spinner SVG, message text, hidden by default
2. Toast container div (id="toast-container"): fixed bottom-right, z-index 9998
3. All screen divs (class="screen" id="screen-NAME") — just empty divs for now:
   screen-landing, screen-login, screen-register, screen-voice, screen-setup,
   screen-dashboard, screen-scan, screen-log, screen-recommend, screen-settings
4. Bottom nav (id="bottom-nav"): fixed bottom, 65px height, white, shadow-lg

**Bottom nav exact HTML:**
```html
<nav id="bottom-nav" style="display:none; position:fixed; bottom:0; left:0; width:100%; height:65px; background:white; box-shadow:0 -2px 20px rgba(0,0,0,0.08); z-index:100;">
  <div style="display:flex; align-items:center; justify-content:space-around; height:100%; padding: 0 8px; max-width:500px; margin:0 auto;">
    <button class="nav-btn" onclick="navTo('dashboard')" data-screen="dashboard">
      [house SVG icon 24px] <span>Home</span>
    </button>
    <button class="nav-btn" onclick="navTo('log')" data-screen="log">
      [list SVG icon 24px] <span>Log</span>
    </button>
    <button id="scan-nav-btn" onclick="navTo('scan')" style="width:56px; height:56px; border-radius:50%; background:linear-gradient(135deg,var(--primary),var(--accent)); border:none; cursor:pointer; box-shadow:0 4px 15px rgba(26,107,60,0.4); margin-bottom:20px; display:flex; align-items:center; justify-content:center;">
      [camera SVG icon 26px white]
    </button>
    <button class="nav-btn" onclick="navTo('recommend')" data-screen="recommend">
      [sparkle SVG icon 24px] <span>Tips</span>
    </button>
    <button class="nav-btn" onclick="navTo('settings')" data-screen="settings">
      [person SVG icon 24px] <span>Profile</span>
    </button>
  </div>
</nav>
```

**Nav button CSS:**
```css
.nav-btn { background: none; border: none; display: flex; flex-direction: column; align-items: center; gap: 3px; cursor: pointer; padding: 8px 16px; color: var(--text-light); font-size: 11px; font-family: 'Inter', sans-serif; transition: color var(--transition); }
.nav-btn.active { color: var(--primary); }
.nav-btn svg { transition: color var(--transition); }
```

**JAVASCRIPT at bottom of body:**

```javascript
const API_BASE = 'http://localhost:8000';
let authToken = null;
let currentUser = null;

// ── SCREEN MANAGEMENT ──────────────────────────────────────
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const screen = document.getElementById('screen-' + name);
  if (!screen) { console.error('Screen not found:', name); return; }
  screen.classList.add('active');
  const noNav = ['landing','login','register','voice','setup'];
  document.getElementById('bottom-nav').style.display = noNav.includes(name) ? 'none' : 'flex';
  document.querySelectorAll('.nav-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.screen === name);
  });
  if (name === 'scan') { initCamera(); }
  if (name !== 'scan') { stopCamera(); }
  if (name === 'dashboard') { loadDashboard(); }
  if (name === 'log') { loadFoodLog(); }
  if (name === 'recommend' && currentUser) { /* show button, don't auto-load */ }
}

function navTo(name) { showScreen(name); }

// ── API HELPER ──────────────────────────────────────────────
async function apiCall(endpoint, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (authToken) headers['Authorization'] = 'Bearer ' + authToken;
  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);
  try {
    const res = await fetch(API_BASE + endpoint, options);
    const data = await res.json();
    if (res.status === 401) { authToken = null; currentUser = null; showScreen('login'); throw new Error('Session expired. Please login again.'); }
    if (res.status === 503) throw new Error('AI service temporarily unavailable. Try again.');
    if (!res.ok) throw new Error(data.detail || 'Request failed (' + res.status + ')');
    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Cannot connect to server. Make sure backend is running on port 8000.');
    }
    throw err;
  }
}

// ── TOAST NOTIFICATIONS ─────────────────────────────────────
function showToast(message, type = 'success') {
  const colors = { success: '#1A6B3C', error: '#F44336', warning: '#FF9800', info: '#1565C0' };
  const toast = document.createElement('div');
  toast.style.cssText = `position:fixed; bottom:80px; left:50%; transform:translateX(-50%); 
    background:${colors[type] || colors.success}; color:white; padding:12px 20px; 
    border-radius:24px; font-size:14px; font-weight:500; z-index:9997; 
    box-shadow:0 4px 20px rgba(0,0,0,0.2); max-width:90vw; text-align:center;
    animation: slideUp 0.3s ease; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = '0.3s'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// ── LOADING OVERLAY ─────────────────────────────────────────
function showLoading(msg = 'Loading...') {
  document.getElementById('loading-overlay').style.display = 'flex';
  const msgEl = document.getElementById('loading-message');
  if (msgEl) msgEl.textContent = msg;
}
function hideLoading() { document.getElementById('loading-overlay').style.display = 'none'; }

// ── APP INIT ────────────────────────────────────────────────
window.onload = () => {
  showScreen('landing');
};
```

Create the complete file now with all of this. Use real SVG icons for the bottom nav — not emojis. Make it look professional.
---

---

## STEP 9 — LANDING + LOGIN + REGISTER + VOICE + SETUP SCREENS

> Copy and paste into Cursor Chat

---
Fill in the content for these 5 screens in index.html.
Add the HTML inside each existing screen div and the matching JavaScript functions.

**screen-landing:**
Full screen green gradient (linear-gradient 150deg, #145530 0%, #1A6B3C 50%, #2E7D32 100%)
Center everything vertically and horizontally.
Content (white text):
- SVG logo: a circle with a leaf and fork icon (create simple SVG, white lines)
- "NutriScan AI" — 2.8rem, font-weight 800, white, letter-spacing -0.5px
- "Scan your food. Know your nutrition." — 1rem, white opacity 0.85, margin-top 8px
- Spacer (flex: 1)
- White "Get Started →" button (btn class, white background, primary text color, 56px height)
  onclick: showScreen('register')
- "Already have an account?" link (white, opacity 0.8, underline)
  onclick: showScreen('login')
- Bottom: small text "Powered by GPT-4o Vision" (white, opacity 0.5, font-size 12px)
All content in a centered div with max-width 360px, padding 40px 24px.

**screen-login:**
White screen, padding 24px, max-width 420px centered on desktop.
- Back arrow top-left: onclick showScreen('landing')
- "Welcome back 👋" — 1.8rem, bold, margin-top 40px
- "Sign in to your account" — secondary color, margin-bottom 32px
- Email input with label
- Password input with label + eye icon toggle (show/hide)
- "Login" btn-primary button
  onclick: handleLogin()
- "Don't have an account? Register" — link, center, margin-top 16px

async function handleLogin():
  const email = document.getElementById('login-email').value.trim()
  const password = document.getElementById('login-password').value
  if (!email || !password) { showToast('Please fill in all fields', 'warning'); return; }
  const btn = document.getElementById('login-btn')
  btn.disabled = true; btn.textContent = 'Signing in...'
  try {
    const data = await apiCall('/auth/login', 'POST', {email, password})
    authToken = data.access_token
    currentUser = data.user
    showToast('Welcome back, ' + currentUser.name + '! 👋')
    showScreen('dashboard')
  } catch (err) {
    showToast(err.message, 'error')
  } finally {
    btn.disabled = false; btn.textContent = 'Login'
  }

**screen-register:**
White screen, padding 24px.
- Back arrow: onclick showScreen('landing')
- "Create Account" — 1.8rem bold, margin-top 40px
- "Join NutriScan AI today" — secondary
- Name input, Email input, Password input
- Password strength indicator bar:
  Under password input: thin bar (4px height, border-radius 2px)
  0-5 chars: red "Weak", 6-9 chars: orange "Fair", 10+: green "Strong"
  Update on input event
- "Continue →" btn-primary
  onclick: validateRegisterStep()
- "Have an account? Login" link

let registerData = {}
function validateRegisterStep():
  Validate name (not empty), email (valid format), password (min 6 chars)
  If valid: store registerData = {name, email, password}
  Ask user: showVoiceChoice()

function showVoiceChoice():
  Show a small modal or bottom sheet:
  Title: "Set up your profile"
  Two options:
    "🎤 Use Voice (faster)" — btn-primary — onclick: registerData already set, showScreen('voice'); startVoiceOnboarding()
    "📝 Fill Form" — btn-outline — onclick: showScreen('setup')
  Can dismiss with X

**screen-voice:**
Dark green gradient background (same as landing)
Center everything, white text.
- "Let's get to know you" — 1.5rem, bold, white, margin-top 60px
- Subtitle: "Answer by speaking — or type below" — opacity 0.75
- Progress steps: 5 dots, current dot is larger and white, others are white opacity 0.3
- Current question text — 1.3rem, white, bold, center, margin 32px 24px
- Large microphone button (80px circle):
  Idle: white background, primary icon
  Listening: pulsing animation (box-shadow grows), green fill, white icon
  CSS: @keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(76,175,80,0.4) } 50% { box-shadow: 0 0 0 20px rgba(76,175,80,0) } }
- Recognized text display area (white card below mic, shows what was heard)
- Text input fallback (below mic, placeholder matches current question)
- Submit answer button (small, outline white) for text input
- "Skip to form →" link at very bottom

const VOICE_QUESTIONS = [
  { key: 'age', text: 'How old are you?', type: 'number' },
  { key: 'weight_kg', text: 'What is your weight in kilograms?', type: 'number' },
  { key: 'height_cm', text: 'How tall are you in centimeters?', type: 'number' },
  { key: 'gender', text: 'What is your gender? Say male, female, or other.', type: 'gender' },
  { key: 'goal', text: 'Your health goal: lose weight, gain muscle, or stay healthy?', type: 'goal' }
]
let voiceAnswers = {}; let voiceIndex = 0; let recognition = null;

function startVoiceOnboarding():
  voiceIndex = 0; voiceAnswers = {}
  updateVoiceUI()
  speakQuestion()

function speakQuestion():
  const q = VOICE_QUESTIONS[voiceIndex]
  document.getElementById('voice-question-text').textContent = q.text
  updateProgressDots()
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(q.text)
  u.rate = 0.85; u.pitch = 1.1; u.volume = 1
  u.onend = () => setTimeout(startListening, 500)
  window.speechSynthesis.speak(u)

function startListening():
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) { showManualVoiceInput(); return }
  recognition = new SR()
  recognition.lang = 'en-US'; recognition.interimResults = false; recognition.maxAlternatives = 1
  recognition.onstart = () => setMicState('listening')
  recognition.onresult = (e) => processVoiceAnswer(e.results[0][0].transcript)
  recognition.onerror = () => { setMicState('idle'); showManualVoiceInput(); }
  recognition.onend = () => setMicState('idle')
  recognition.start()

function processVoiceAnswer(transcript):
  const q = VOICE_QUESTIONS[voiceIndex]
  let value = transcript.trim().toLowerCase()
  document.getElementById('voice-transcript').textContent = '"' + transcript + '"'
  if (q.type === 'number'):
    const num = parseFloat(transcript.match(/\d+\.?\d*/)?.[0])
    if (isNaN(num)) { showToast('Please say a number', 'warning'); speakQuestion(); return; }
    value = num
  else if (q.type === 'gender'):
    if (value.includes('male') && !value.includes('fe')) value = 'male'
    else if (value.includes('female')) value = 'female'
    else value = 'other'
  else if (q.type === 'goal'):
    if (value.includes('lose')) value = 'lose_weight'
    else if (value.includes('gain') || value.includes('muscle')) value = 'gain_muscle'
    else value = 'maintain'
  voiceAnswers[q.key] = value
  voiceIndex++
  if (voiceIndex >= VOICE_QUESTIONS.length):
    submitVoiceProfile()
  else:
    setTimeout(speakQuestion, 800)

async function submitVoiceProfile():
  showLoading('Creating your profile...')
  try {
    const body = { ...registerData, ...voiceAnswers }
    const data = await apiCall('/auth/register', 'POST', body)
    authToken = data.access_token
    currentUser = data.user
    hideLoading()
    showToast('Profile created! Welcome, ' + currentUser.name + '! 🎉')
    showScreen('dashboard')
  } catch (err) {
    hideLoading()
    showToast(err.message, 'error')
    showScreen('setup')
  }

**screen-setup (form fallback):**
White screen, scrollable.
- Back arrow
- "Your Health Profile" — bold title
- Step progress: "2 of 2"
- Name input (pre-fill from registerData.name if exists)
- Age input (number, min 10 max 100)
- Weight slider: range 30-200, step 0.5 — live label showing value + "kg"
- Height slider: range 100-220, step 1 — live label showing value + "cm"
- Gender: 3 pill-style toggle buttons (Male / Female / Other) — click to select, selected = primary bg white text
- Goal: 3 full-width option cards:
    [🔥 Lose Weight | Calorie deficit, fat loss focus]
    [💪 Gain Muscle | High protein, strength goals]
    [⚖️ Stay Healthy | Balanced, maintain weight]
  Selected card: primary color border + very light primary background
- Live preview box: "Your daily calorie target: ~1,850 kcal" (recalculate on any input change)
- "Create My Plan →" btn-primary (taller, 56px)
  onclick: submitSetupForm()

async function submitSetupForm():
  Gather all values, validate none are empty
  showLoading('Creating your plan...')
  const body = { ...registerData, age: parseInt(age), weight_kg: parseFloat(weight), height_cm: parseFloat(height), gender, goal }
  const data = await apiCall('/auth/register', 'POST', body)
  authToken = data.access_token; currentUser = data.user
  hideLoading()
  showScreen('dashboard')

Create all 5 screens fully now. Make them beautiful and production-quality.
---

---

## STEP 10 — DASHBOARD SCREEN

> Copy and paste into Cursor Chat

---
Fill in screen-dashboard with complete content and all JavaScript.

**HTML Layout:**

```
[Green gradient header: greeting + date + streak badge]
[Calorie ring card]
[BMI card (inline with macro row)]
[3 macro progress bars card]
[Water tracker card]
[Quick action buttons: Scan | AI Tips | View Log]
[Recent food log: last 3 items]
```

**Green gradient header:**
background: linear-gradient(135deg, var(--primary-dark), var(--primary-light))
padding: 24px 20px 32px
Text:
  Greeting (h2, white, bold): "Good morning, {name}!"
  Date (p, white opacity 0.8): e.g. "Monday, March 2, 2026"
  Row of chips: "🔥 X day streak" (white semi-transparent pill) + goal badge

Dynamic greeting logic:
  const h = new Date().getHours()
  if h < 12: "Good morning" 
  else if h < 17: "Good afternoon"
  else if h < 21: "Good evening"
  else: "Good night"

**Calorie ring (SVG):**
```html
<div class="card" style="margin: -20px 16px 0; position:relative; z-index:1;">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <div>
      <p style="color:var(--text-secondary); font-size:13px;">Daily Calories</p>
      <p id="calories-remaining" style="font-size:13px; color:var(--primary); font-weight:600; margin-top:4px;">-- kcal remaining</p>
    </div>
    <svg width="110" height="110" viewBox="0 0 110 110">
      <circle cx="55" cy="55" r="46" fill="none" stroke="#E8F5E9" stroke-width="10"/>
      <circle id="calorie-ring" cx="55" cy="55" r="46" fill="none" stroke="var(--primary)" stroke-width="10"
        stroke-linecap="round" stroke-dasharray="289" stroke-dashoffset="289"
        transform="rotate(-90 55 55)" style="transition: stroke-dashoffset 1s ease;"/>
      <text x="55" y="50" text-anchor="middle" font-size="20" font-weight="700" fill="var(--text)" id="calories-consumed-text">0</text>
      <text x="55" y="65" text-anchor="middle" font-size="10" fill="var(--text-secondary)" id="calories-goal-text">/ 0 kcal</text>
    </svg>
  </div>
</div>
```

**BMI mini card (same row layout):**
Show bmi value large, category badge below.

**Macro bars:**
3 rows, each:
  Label (Protein/Carbs/Fat), consumed/target in grams
  Progress bar: div with background border, inner div width = % of target, color green
  Example: Protein: 45g / 120g → bar is 37.5% wide

Macro targets from user's daily_calorie_goal:
  protein_target = (daily_goal * 0.30) / 4   [grams]
  carbs_target   = (daily_goal * 0.50) / 4   [grams]
  fat_target     = (daily_goal * 0.20) / 9   [grams]

**Water tracker:**
Row of 8 water drop SVGs (💧 style)
glasses_drunk stored in let waterGlasses = 0
Clicking a drop fills it (up to that number)
Show text: "{waterGlasses * 250}ml / 2000ml"
"+250ml" button adds one glass

**Quick actions row:**
3 equal-width cards with icon + label:
  📷 Scan Food → onclick: showScreen('scan')
  ✨ Get AI Tips → onclick: showScreen('recommend')
  📋 View Log → onclick: showScreen('log')
Cards: white, shadow-sm, border-radius var(--radius), hover lifts

**Recent log section:**
Title "Recent Today" + "See all →" link
Show last 3 items from today's log
Each as a small row: circle with letter + food name + calories
Empty state: "No food logged yet" with scan CTA

**async function loadDashboard():**
  if (!currentUser) return
  try {
    showSkeletonDashboard()
    const [stats, log] = await Promise.all([
      apiCall('/users/stats/' + currentUser.id),
      apiCall('/food/log/today/' + currentUser.id)
    ])
    updateCalorieRing(stats.consumed_today, stats.daily_goal)
    updateBMI(stats.bmi, stats.bmi_category)
    updateMacros(log)
    updateStreak(stats.streak_days)
    updateRecentLog(log)
    updateGreeting()
  } catch (err) {
    showToast('Could not load dashboard: ' + err.message, 'error')
  }

**function updateCalorieRing(consumed, goal):**
  const circumference = 2 * Math.PI * 46  // = 289
  const pct = Math.min(consumed / goal, 1)
  const offset = circumference - (pct * circumference)
  document.getElementById('calorie-ring').style.strokeDashoffset = offset
  document.getElementById('calories-consumed-text').textContent = Math.round(consumed)
  document.getElementById('calories-goal-text').textContent = '/ ' + goal + ' kcal'
  document.getElementById('calories-remaining').textContent = Math.round(goal - consumed) + ' kcal remaining'

**function showSkeletonDashboard():**
  Show 3-4 skeleton divs (height 80px each, class="skeleton") while loading

Create the full dashboard screen now. Must look stunning — this is the main screen reviewers will see.
---

---

## STEP 11 — CAMERA SCANNER SCREEN

> Copy and paste into Cursor Chat

---
Fill in screen-scan. This is the CORE FEATURE. Build it perfectly.

**HTML (inside screen-scan div):**
```html
<div id="scan-container" style="position:relative; width:100%; height:100vh; background:black; overflow:hidden;">
  
  <!-- Live camera feed -->
  <video id="camera-feed" autoplay playsinline muted
    style="width:100%; height:100%; object-fit:cover; display:block;"></video>
  <canvas id="capture-canvas" style="display:none;"></canvas>
  
  <!-- Top bar overlay -->
  <div style="position:absolute; top:0; left:0; width:100%; padding:50px 20px 20px; background:linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, transparent 100%); display:flex; align-items:center; gap:16px; z-index:10;">
    <button onclick="showScreen('dashboard')" style="width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,0.2);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;">
      [back arrow SVG white 20px]
    </button>
    <div id="meal-selector" style="display:flex; gap:8px; flex:1; justify-content:center;">
      [4 pill buttons: Breakfast / Lunch / Dinner / Snack]
      [selected pill: white bg, primary text; unselected: white border, white text opacity 0.7]
    </div>
    <button onclick="flipCamera()" style="width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,0.2);border:none;cursor:pointer;">
      [flip camera SVG white]
    </button>
  </div>
  
  <!-- Aim guide overlay -->
  <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-55%); width:280px; height:280px; border:2px dashed rgba(255,255,255,0.5); border-radius:24px; pointer-events:none; z-index:5;">
    <p style="position:absolute; bottom:-32px; left:50%; transform:translateX(-50%); color:white; font-size:13px; white-space:nowrap; opacity:0.8;">Point at your food plate</p>
  </div>
  
  <!-- Bottom bar overlay -->
  <div style="position:absolute; bottom:0; left:0; width:100%; padding:20px 32px 40px; background:linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 100%); display:flex; align-items:center; justify-content:space-between; z-index:10;">
    <!-- Upload photo button -->
    <button onclick="document.getElementById('file-upload').click()" style="width:46px;height:46px;border-radius:50%;background:rgba(255,255,255,0.2);border:2px solid rgba(255,255,255,0.4);cursor:pointer;display:flex;align-items:center;justify-content:center;">
      [gallery/upload SVG white 22px]
    </button>
    <!-- Capture button -->
    <button id="capture-btn" onclick="captureFood()" style="width:72px;height:72px;border-radius:50%;background:white;border:4px solid rgba(255,255,255,0.5);cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,0.3);">
      <div style="width:56px;height:56px;border-radius:50%;background:var(--primary);"></div>
    </button>
    <!-- Flip hint -->
    <div style="width:46px;"></div>
  </div>
  
  <!-- File upload input -->
  <input type="file" id="file-upload" accept="image/*" capture="environment" style="display:none;" onchange="handleFileUpload(event)">
  
  <!-- Scanning loading overlay -->
  <div id="scan-loading" style="display:none; position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); z-index:20; flex-direction:column; align-items:center; justify-content:center;">
    [spinning circle SVG animation, green, 60px]
    <p style="color:white; font-size:18px; font-weight:600; margin-top:24px;">Analyzing your food...</p>
    <p style="color:rgba(255,255,255,0.7); font-size:14px; margin-top:8px;">Identifying items & calculating nutrition</p>
  </div>
  
  <!-- Camera error state -->
  <div id="camera-error" style="display:none; position:absolute; top:0; left:0; width:100%; height:100%; background:#1a1a1a; z-index:15; flex-direction:column; align-items:center; justify-content:center; padding:32px; text-align:center;">
    [camera-off SVG white 64px]
    <p id="camera-error-msg" style="color:white; font-size:16px; margin-top:20px; margin-bottom:24px;"></p>
    <button onclick="document.getElementById('file-upload').click()" class="btn btn-primary" style="max-width:280px;">Upload a Photo Instead</button>
    <button onclick="showScreen('dashboard')" style="color:white; opacity:0.7; margin-top:16px; background:none; border:none; cursor:pointer;">Go Back</button>
  </div>
  
</div>

<!-- Results bottom sheet -->
<div id="scan-results-sheet" style="display:none; position:fixed; bottom:0; left:0; width:100%; max-height:70vh; background:white; border-radius:24px 24px 0 0; box-shadow:0 -4px 30px rgba(0,0,0,0.15); z-index:50; overflow-y:auto; padding:20px;">
  <div style="width:40px; height:4px; background:var(--border); border-radius:2px; margin:0 auto 20px;"></div>
  <h3 style="font-size:18px; font-weight:700; margin-bottom:16px;">Scan Results 🍽️</h3>
  <div id="scan-results-list"></div>
  <div id="scan-totals-bar" style="border-top:1px solid var(--border); margin-top:16px; padding-top:16px; display:flex; justify-content:space-between; align-items:center;">
    <div>
      <span style="font-size:13px; color:var(--text-secondary);">Total</span>
      <div id="scan-total-calories" style="font-size:22px; font-weight:800; color:var(--primary);"></div>
    </div>
    <div style="font-size:12px; color:var(--text-secondary); text-align:right;" id="scan-total-macros"></div>
  </div>
  <div style="display:flex; gap:12px; margin-top:16px;">
    <button onclick="closeScanResults()" class="btn btn-outline" style="flex:1;">↺ Retake</button>
    <button onclick="acceptScanResults()" class="btn btn-primary" style="flex:2;">✓ Added to Log</button>
  </div>
</div>
```

**JavaScript:**

```javascript
let stream = null;
let facingMode = 'environment';
let selectedMealType = 'lunch';
let lastScanResult = null;

async function initCamera() {
  document.getElementById('camera-error').style.display = 'none';
  try {
    if (stream) { stream.getTracks().forEach(t => t.stop()); }
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: facingMode }, width: { ideal: 1920 }, height: { ideal: 1080 } }
    });
    document.getElementById('camera-feed').srcObject = stream;
  } catch (err) {
    const msg = err.name === 'NotAllowedError'
      ? 'Camera blocked. In your browser, tap the camera icon in the address bar and allow access, then come back.'
      : 'Camera not available on this device. You can upload a photo instead.';
    showCameraError(msg);
  }
}

function stopCamera() {
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
}

function showCameraError(msg) {
  const el = document.getElementById('camera-error');
  document.getElementById('camera-error-msg').textContent = msg;
  el.style.display = 'flex';
}

function flipCamera() {
  facingMode = facingMode === 'environment' ? 'user' : 'environment';
  initCamera();
}

async function captureFood() {
  const video = document.getElementById('camera-feed');
  const canvas = document.getElementById('capture-canvas');
  if (!stream || !video.videoWidth) { showToast('Camera not ready', 'warning'); return; }
  
  // Set canvas to video dimensions (compress to max 1024px)
  const maxDim = 1024;
  const scale = Math.min(maxDim / video.videoWidth, maxDim / video.videoHeight, 1);
  canvas.width = video.videoWidth * scale;
  canvas.height = video.videoHeight * scale;
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  
  // White flash
  const flash = document.createElement('div');
  flash.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:white;opacity:0.7;z-index:99;pointer-events:none;transition:opacity 0.15s;';
  document.body.appendChild(flash);
  setTimeout(() => { flash.style.opacity = '0'; setTimeout(() => flash.remove(), 150); }, 50);
  if (navigator.vibrate) navigator.vibrate(40);
  
  const base64 = canvas.toDataURL('image/jpeg', 0.75).replace('data:image/jpeg;base64,', '');
  await sendToScan(base64);
}

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const base64 = e.target.result.replace(/^data:image\/\w+;base64,/, '');
    sendToScan(base64);
  };
  reader.readAsDataURL(file);
  event.target.value = '';
}

async function sendToScan(base64) {
  document.getElementById('scan-loading').style.display = 'flex';
  document.getElementById('scan-results-sheet').style.display = 'none';
  try {
    const result = await apiCall('/food/scan', 'POST', {
      image_base64: base64,
      meal_type: selectedMealType,
      user_id: currentUser.id
    });
    lastScanResult = result;
    document.getElementById('scan-loading').style.display = 'none';
    if (!result.items || result.items.length === 0) {
      showToast('No food detected. Try better lighting or move closer.', 'warning');
      return;
    }
    showScanResults(result);
  } catch (err) {
    document.getElementById('scan-loading').style.display = 'none';
    showToast(err.message, 'error');
  }
}

function showScanResults(result) {
  const list = document.getElementById('scan-results-list');
  list.innerHTML = result.items.map(item => `
    <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid var(--border);">
      <div>
        <div style="font-weight:600; font-size:15px;">${item.food_name}</div>
        <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">~${Math.round(item.quantity_g)}g &nbsp;|&nbsp; P:${item.protein_g.toFixed(1)}g C:${item.carbs_g.toFixed(1)}g F:${item.fat_g.toFixed(1)}g</div>
      </div>
      <div style="font-size:20px; font-weight:800; color:var(--primary); white-space:nowrap;">${Math.round(item.calories)} kcal</div>
    </div>
  `).join('');
  document.getElementById('scan-total-calories').textContent = Math.round(result.total_calories) + ' kcal';
  document.getElementById('scan-total-macros').innerHTML = `P: ${result.total_protein.toFixed(1)}g<br>C: ${result.total_carbs.toFixed(1)}g  F: ${result.total_fat.toFixed(1)}g`;
  document.getElementById('scan-results-sheet').style.display = 'block';
}

function closeScanResults() {
  document.getElementById('scan-results-sheet').style.display = 'none';
}

function acceptScanResults() {
  closeScanResults();
  showToast('✅ Added to your food log!');
  showScreen('dashboard');
}

// Meal type selector
document.querySelectorAll('.meal-pill').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.meal-pill').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    selectedMealType = btn.dataset.meal;
  });
});
```

Build this completely. The scanner must work on mobile Chrome and desktop Chrome.
---

---

## STEP 12 — FOOD LOG + RECOMMENDATIONS

> Copy and paste into Cursor Chat

---
Fill in screen-log and screen-recommend.

**screen-log complete layout:**

Header with date navigation:
  "← Yesterday" button | "Today, March 2" title (centered) | "→" (disabled if today)
  onclick prev/next: change the displayed date and reload

Per-day log grouped by meal:
  For each of [breakfast, lunch, dinner, snack] that has items:
    Section header: emoji + meal name + "— Xkcal" right-aligned
    Each food item row:
      Left circle: 36px, primary bg, white letter (first letter of food name)
      Middle: food name (bold, 14px), meal type + quantity below (secondary, 12px)
      Right: calories (primary, bold) + X delete button (red, small, right of calories)
    
    onclick delete button:
      if confirm is not needed (just do it silently):
      await apiCall('/food/log/' + logId, 'DELETE')
      remove the card with CSS transform + opacity animation (0.3s)
      update totals
      showToast('Removed from log')

Daily totals summary bar (position:sticky; bottom:0):
  White bg, border-top var(--border), padding 12px 20px
  "Total: 1,240 / 2,000 kcal"
  Thin progress bar (full width, green fill for consumed proportion)
  Macro row: P: 85g  C: 145g  F: 42g (small chips)

Empty state:
  Center: 🍽️ emoji large, "Nothing here yet", "Scan your meal →" button → showScreen('scan')

"Export PDF" button top-right (calls exportPDF())

async function loadFoodLog(dateStr = null):
  showSkeletonCards(3)
  const today = dateStr || 'today'  
  // For today use the today endpoint, for other dates filter client-side from history
  const log = await apiCall('/food/log/today/' + currentUser.id)
  renderFoodLog(log)

function renderFoodLog(log):
  Build and insert HTML for each meal group
  Update totals bar
  If all groups empty: show empty state

**screen-recommend complete layout:**

Header: "AI Nutrition Tips ✨"
Subtitle: "Based on your profile and today's meals"

Initial state (before loading):
  Large centered button: "Get My Recommendations 🧠"
  Subtext: "Analyzes your profile + today's meals"
  onclick: loadRecommendations()

Loading state:
  Animated dots or spinner
  Typewriter text cycling through: "Analyzing your nutrition..." → "Checking your macros..." → "Building your meal plan..."

Results state (after API responds):

1. Greeting card (gradient green):
   rec.greeting text, white, centered, italic, padding 20px

2. Next Meal card:
   Title: "Suggested Next Meal" + meal_type badge
   Each suggestion: food name bold, portion gray, calories green right, reason italic small below
   Total: "Meal total: X kcal" at bottom
   Button: "Add All to Log" → add each suggestion as a FoodLog entry with calories only

3. Foods to Avoid card (orange left border):
   Title "⚠️ Skip These Today"
   Tags/chips for each item (orange bg, white text, rounded)

4. Health Tip card (blue-green left border):
   "💡 " + rec.health_tip

5. Water card (light blue):
   "💧 " + rec.water_reminder

6. Progress card:
   rec.goal_progress text
   Thin progress bar showing consumed/daily_goal

"Refresh Tips 🔄" button at bottom → calls loadRecommendations() again

async function loadRecommendations():
  Show loading state
  Start typewriter cycling
  try:
    const rec = await apiCall('/users/recommendations/' + currentUser.id, 'POST')
    Stop typewriter
    const data = typeof rec.content === 'string' ? JSON.parse(rec.content) : rec
    Render all recommendation cards with slide-in animation
  catch err:
    showToast('Could not load tips: ' + err.message, 'error')
    Show retry button

Build both screens completely now.
---

---

## STEP 13 — CHARTS + REMINDERS + PDF + SETTINGS + FINAL POLISH

> Copy and paste into Cursor Chat

---
Add the final features and make the app production-quality.

**1. Add a Progress tab or section in screen-log (toggle between "Log" and "Progress"):**

Weekly calorie chart (Chart.js):
  type: 'bar'
  data from: apiCall('/users/stats/' + currentUser.id) → last_7_days
  config:
    datasets[0]: label 'Calories', backgroundColor: '#4CAF50', borderRadius: 8
    Add a horizontal line dataset for daily goal: type 'line', borderColor: '#FF9800', borderDash: [5,5], pointRadius: 0
    x-axis: day abbreviations (Mon, Tue, etc.)
    y-axis: starting from 0
    No legend. Tooltip shows exact calories.
    responsive: true, maintainAspectRatio: false
  Container height: 200px

Macro pie chart:
  type: 'doughnut'
  Get macro data from today's food log
  backgroundColor: ['#1A6B3C', '#4CAF50', '#FF9800'] for Protein/Carbs/Fat
  cutout: '65%'
  Center label plugin: show "Macros" in center
  Below chart: 3 legend items showing grams

Always destroy existing chart instance before re-creating:
  if (weeklyChartInstance) { weeklyChartInstance.destroy(); weeklyChartInstance = null; }

**2. Reminders section (inside screen-settings):**

```html
<div class="card" style="margin:16px;">
  <h3 style="font-size:16px; font-weight:700; margin-bottom:16px;">🔔 Meal Reminders</h3>
  [4 rows:]
  [toggle switch] 🌅 Breakfast [time input default 08:00]
  [toggle switch] ☀️ Lunch [time input default 13:00]  
  [toggle switch] 🌙 Dinner [time input default 19:00]
  [toggle switch] 💧 Water (every 2 hrs) [checkbox]
  <button onclick="saveReminders()" class="btn btn-primary" style="margin-top:16px;">Save Reminders</button>
</div>
```

Toggle switch CSS:
```css
.toggle { position:relative; width:44px; height:24px; }
.toggle input { opacity:0; width:0; height:0; }
.toggle-slider { position:absolute; cursor:pointer; top:0;left:0;right:0;bottom:0; background:#ccc; border-radius:24px; transition:.3s; }
.toggle-slider:before { position:absolute; content:""; height:18px; width:18px; left:3px; bottom:3px; background:white; border-radius:50%; transition:.3s; }
input:checked + .toggle-slider { background: var(--primary); }
input:checked + .toggle-slider:before { transform:translateX(20px); }
```

async function saveReminders():
  if (Notification.permission === 'default'):
    const perm = await Notification.requestPermission()
    if (perm !== 'granted'):
      showToast('Enable notifications in browser settings to use reminders', 'warning')
      return
  if (Notification.permission === 'denied'):
    showToast('Notifications blocked. Allow them in browser settings.', 'warning'); return
  Schedule each enabled reminder:
    const [hours, mins] = timeString.split(':').map(Number)
    const now = new Date(); const target = new Date()
    target.setHours(hours, mins, 0, 0)
    if (target <= now) target.setDate(target.getDate() + 1)
    const ms = target - now
    setTimeout(() => new Notification('NutriScan AI 🥗', { body: reminderMessage, icon: '' }), ms)
  showToast('Reminders saved! ✅')

**3. PDF Export function:**
async function exportPDF():
  const { jsPDF } = window.jspdf
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  
  // Header bar
  doc.setFillColor(26, 107, 60); doc.rect(0, 0, 210, 28, 'F')
  doc.setTextColor(255,255,255); doc.setFontSize(18); doc.setFont('helvetica','bold')
  doc.text('NutriScan AI — Food Log Report', 14, 18)
  
  // User info
  doc.setTextColor(50,50,50); doc.setFont('helvetica','normal'); doc.setFontSize(11)
  doc.text('Name: ' + currentUser.name, 14, 38)
  doc.text('Date: ' + new Date().toLocaleDateString('en-IN', {weekday:'long',year:'numeric',month:'long',day:'numeric'}), 14, 46)
  doc.text('Daily Goal: ' + currentUser.daily_calorie_goal + ' kcal', 14, 54)
  doc.text('BMI: ' + (currentUser.weight_kg / Math.pow(currentUser.height_cm/100, 2)).toFixed(1), 110, 54)
  
  // Table header
  let y = 68
  doc.setFillColor(240,247,242); doc.rect(10, y-6, 190, 9, 'F')
  doc.setFont('helvetica','bold'); doc.setFontSize(10)
  doc.text('Food Item', 12, y); doc.text('Qty', 92, y); doc.text('kcal', 118, y); doc.text('Protein', 140, y); doc.text('Meal', 170, y)
  y += 2; doc.setDrawColor(200,220,200); doc.line(10, y, 200, y)
  
  // Rows
  const log = await apiCall('/food/log/today/' + currentUser.id)
  const allItems = [...(log.breakfast||[]), ...(log.lunch||[]), ...(log.dinner||[]), ...(log.snack||[])]
  doc.setFont('helvetica','normal')
  allItems.forEach((item, i) => {
    y += 8
    if (i % 2 === 0) { doc.setFillColor(248,253,249); doc.rect(10, y-5, 190, 7, 'F'); }
    doc.setTextColor(30,30,30)
    doc.text(item.food_name.substring(0,30), 12, y)
    doc.text(Math.round(item.quantity_g)+'g', 92, y)
    doc.text(Math.round(item.calories)+'', 118, y)
    doc.text(item.protein_g.toFixed(1)+'g', 140, y)
    doc.text(item.meal_type, 170, y)
    if (y > 270) { doc.addPage(); y = 20; }
  })
  
  // Totals
  y += 12
  doc.setFillColor(26,107,60); doc.rect(10, y-6, 190, 9, 'F')
  doc.setTextColor(255,255,255); doc.setFont('helvetica','bold')
  doc.text('TOTAL', 12, y)
  doc.text(Math.round(log.totals?.calories||0)+' kcal', 118, y)
  doc.text((log.totals?.protein_g||0).toFixed(1)+'g', 140, y)
  
  doc.save('nutriscan-' + new Date().toISOString().split('T')[0] + '.pdf')
  showToast('PDF downloaded! 📄')

**4. screen-settings layout:**
- Header: "Profile ⚙️"
- Profile card:
    Avatar circle (60px, primary bg, white initials 2 letters)
    Name (bold), email (secondary), goal badge
    "Edit" button → toggle inline edit form
- Edit form (hidden):
    Weight input, Goal selector, "Save Changes" → PUT /users/{id} → update currentUser → showToast
- Stats row: BMI value + category, "Member since {date}", Goal label
- Reminders section (as above)
- "Export PDF" button
- Danger: "Logout" button (red outline) → authToken=null; currentUser=null; showScreen('landing')

**5. Final Polish — check ALL of these:**

a) Pull-to-refresh on dashboard:
   touchstart: record startY
   touchmove: if deltaY > 80 and at top of page: show "↓ Release to refresh" indicator
   touchend: if pulled enough: call loadDashboard(); hide indicator

b) Active nav highlighting:
   Inside showScreen(), after switching:
   document.querySelectorAll('[data-screen]').forEach(b => b.classList.toggle('active', b.dataset.screen === name))

c) All async functions have try/catch — check every single one

d) Input sanitization: trim all string inputs before API calls

e) On window.onload: showScreen('landing') — nothing else, no auto-login

f) Responsive desktop layout:
   @media (min-width: 768px):
     body max-width: 480px, margin: 0 auto — keeps mobile layout centered on desktop
     Add subtle desktop background gradient behind the 480px center column

g) Smooth scrollbar:
   html { scroll-behavior: smooth; }
   ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-thumb { background: var(--accent-light); border-radius: 2px; }

Do a complete review of index.html after adding all these features.
Make sure there are zero broken onclick handlers, zero undefined functions, zero uncaught promise rejections.
Show me the final line count of index.html.
---

---
---

# ════════════════════════════════════
# TESTING — STEPS 14 & 15
# ════════════════════════════════════

---

## STEP 14 — DESKTOP TEST

> Copy and paste into Cursor Chat after the app runs

---
The app is running. Do a complete audit:

1. Check backend at http://localhost:8000/docs — list all endpoints visible

2. Test register via /docs Swagger UI:
   POST /auth/register with:
   {"name":"Test User","email":"test@nutriscan.com","password":"Test123!","age":22,"weight_kg":68,"height_cm":172,"gender":"male","goal":"lose_weight"}
   Expected: returns access_token

3. Test login:
   POST /auth/login with same email/password
   Expected: returns access_token

4. Test stats (use token from above):
   GET /users/stats/1
   Expected: returns bmi, daily_goal, consumed_today, streak_days, last_7_days

5. In the frontend (http://localhost:3000):
   a. Does landing screen show correctly?
   b. Can you register a new user?
   c. Does voice onboarding start?
   d. Does the dashboard load with calorie ring animating?
   e. Does camera scanner open (allow camera permission)?
   f. Does the bottom nav switch screens correctly?

Fix every issue found. List what you fixed.
---

---

## STEP 15 — MOBILE TEST + FINAL PREP

> Copy and paste into Cursor Chat

---
Prepare for mobile browser demo:

1. Find my local IP:
   On Mac/Linux: ifconfig | grep "inet " | grep -v 127.0.0.1
   On Windows: ipconfig | findstr "IPv4"

2. Change in frontend/index.html:
   const API_BASE = 'http://YOUR_IP_HERE:8000';
   (Replace YOUR_IP_HERE with the IP from step 1)

3. Restart uvicorn with --host 0.0.0.0:
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload

4. Restart frontend server:
   cd frontend && python -m http.server 3000 --bind 0.0.0.0

5. On your phone (same WiFi as computer):
   Open: http://YOUR_IP_HERE:3000

6. Mobile-specific checks:
   □ Does the screen fit without horizontal scroll?
   □ Does the camera open in back-facing mode?
   □ Does voice recognition work? (Chrome mobile only)
   □ Are all buttons large enough to tap (min 44px)?
   □ Does the food scan work on a real plate of food?
   □ Does the PDF download work?
   □ Does the bottom nav feel native?

7. If camera requires HTTPS (some phones):
   Install ngrok: pip install pyngrok
   Run: python -c "from pyngrok import ngrok; t = ngrok.connect(3000); print(t.public_url)"
   Use the https://xxx.ngrok.io URL on your phone

Fix any mobile layout issues. The demo reviewer will use a phone.
---

---
---

# ════════════════════════════════════
# QUICK REFERENCE CARD
# ════════════════════════════════════

## Run the App (Both Terminals Open)

```bash
# Terminal 1 — Backend
cd nutriscan-ai/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# → Open: http://localhost:8000/docs

# Terminal 2 — Frontend  
cd nutriscan-ai/frontend
python -m http.server 3000
# → Open: http://localhost:3000
```

## If Something Breaks — Paste This Into Cursor

```
I got this error. Fix it exactly without changing other code:

[PASTE YOUR ERROR HERE]

File: [which file]
Line: [which line if shown]
```

## API Endpoint Summary

| Method | URL | Auth | Does |
|--------|-----|------|------|
| POST | /auth/register | No | Create account |
| POST | /auth/login | No | Get JWT token |
| GET | /auth/me | Yes | Get current user |
| GET | /health | No | Check server |
| POST | /food/scan | Yes | Scan food image |
| GET | /food/log/today/{id} | Yes | Today's log |
| DELETE | /food/log/{id} | Yes | Delete log entry |
| GET | /food/log/history/{id} | Yes | 7-day history |
| GET | /users/stats/{id} | Yes | BMI + calories |
| POST | /users/recommendations/{id} | Yes | AI tips |
| PUT | /users/{id} | Yes | Update profile |

## OpenAI Cost Control
- Set $5 monthly limit: platform.openai.com → Settings → Limits
- Each food scan ≈ $0.006 (less than 1 cent)
- Each recommendation ≈ $0.003
- 100 scans total ≈ $0.60

---

*NutriScan AI | Ameya. K. Anil | NCE22AM006 | March 2026 | Nehru College of Engineering*
