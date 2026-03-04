## PHASE 1: PROJECT STRUCTURE ANALYSIS

### 1.1 Folder structure

```1:98:C:\Users\anand\Downloads\Nutrition\nutriscan-ai\.cursorrules
## FOLDER STRUCTURE (Sacred — Never Change)
```

Effective structure (observed from filesystem and code):

- Root:
  - `nutriscan-ai/`
    - `.cursorrules` (project rules and reference documentation)
    - `backend/`
      - `.env` (environment variables – API key, JWT secret, DB URL, CORS origins)
      - `main.py` (FastAPI application entrypoint, CORS, router inclusion, `/` and `/health`)
      - `database.py` (SQLAlchemy engine/session/Base and `get_db` dependency)
      - `models.py` (SQLAlchemy ORM models: `User`, `FoodLog`, `Recommendation`, `ScanLog`)
      - `schemas.py` (Pydantic models for users, auth tokens, food scan, stats, food logs)
      - `auth.py` (JWT auth, password hashing, register/login/me routes, calorie goal calc)
      - `food_routes.py` (scan endpoint and food log/history management)
      - `user_routes.py` (stats, recommendations, profile update)
      - `openai_service.py` (all OpenAI GPT‑4o calls and prompt logic)
      - `requirements.txt` (pinned backend deps, including `httpx==0.27.2`)
      - `.venv/` (local virtual environment with installed packages)
    - `frontend/`
      - `index.html` (entire SPA: HTML, CSS, JS)
      - `manifest.json` (PWA metadata and icons)
      - `sw.js` (service worker with network‑first strategy for HTML)
      - `generate-icons.html` (utility to generate `icon-192.png` / `icon-512.png`)

### 1.2 Technology stack

- **Frontend framework**: Vanilla single‑page app built as:
  - Static HTML structure with multiple screen containers (`div#screen-*`).
  - Central JS state and functions inside one `<script>` block in `index.html`.
  - Manual routing via `showScreen(name)` and `navTo(name)`.
  - Direct DOM manipulation (no React/Vue/etc.).
- **Backend framework**:
  - FastAPI 0.115.0 with async endpoints and dependency injection.
  - SQLAlchemy 2.x ORM.
  - Pydantic v2 for schemas.
- **Database**:
  - SQLite via `DATABASE_URL = "sqlite:///./nutriscan.db"` in `database.py`.
  - Tables are created automatically through `Base.metadata.create_all` in both:
    - `database.py` (module import side‑effect).
    - `main.py` lifespan handler.
- **API routes** (from `.cursorrules` and code; all implemented as described):
  - **AUTH (no token)**:
    - `POST /auth/register` → `auth.register`
    - `POST /auth/login` → `auth.login`
    - `GET  /auth/me` → `auth.get_me`
  - **FOOD (token required)**:
    - `POST   /food/scan` → `food_routes.scan_food`
    - `GET    /food/log/today/{user_id}` → `food_routes.get_today_log`
    - `DELETE /food/log/{log_id}` → `food_routes.delete_log_entry`
    - `GET    /food/log/history/{user_id}` → `food_routes.get_log_history`
  - **USERS (token required)**:
    - `GET  /users/stats/{user_id}` → `user_routes.get_user_stats`
    - `POST /users/recommendations/{user_id}` → `user_routes.get_user_recommendations`
    - `PUT  /users/{user_id}` → `user_routes.update_user`
  - **SYSTEM**:
    - `GET /` → `main.root`
    - `GET /health` → `main.health`

### 1.3 OpenAI usage

- `openai_service.py`:
  - Uses `AsyncOpenAI` client with API key from `OPENAI_API_KEY` environment variable. If missing, raises `HTTPException(503)`.
  - **Food scanning**:
    - Model: `gpt-4o`.
    - Temperature: 0.3.
    - Max tokens: 1000.
    - Messages:
      - System: `SYSTEM_PROMPT_SCAN` (nutritionist role, USDA reference, JSON‑only requirement).
      - User: `USER_MESSAGE_SCAN` with explicit JSON schema description plus image payload:
        - `{"type": "text", "text": USER_MESSAGE_SCAN}`
        - `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<...>", "detail": "high"}}`
    - Response parsing:
      - Reads `response.choices[0].message.content`.
      - Strips markdown fences (``` / ```json) via `_strip_json_fences`.
      - `json.loads` to Python object.
      - Accepts either:
        - List of items (legacy format) → wraps into `{"items": [...]}`.
        - Dict with keys: `items`, `calorie_range_min`, `calorie_range_max`, `confidence`, `questions_for_user`.
      - Normalizes to dict:
        - `"items": list`
        - `"calorie_range_min" | "calorie_range_max" | "confidence"` as floats.
        - `"questions_for_user"` as list of strings.
      - On invalid types, falls back to an empty‑items result.
    - Error handling:
      - `APIError` → `HTTPException(503, "AI service temporarily unavailable")`.
      - `JSONDecodeError` → `HTTPException(422, "Could not parse AI response from AI model")`.
      - Generic `Exception` → `HTTPException(500, "AI scan failed. Please try again.")`.
  - **Recommendations**:
    - Model: `gpt-4o`.
    - Temperature: 0.7.
    - Max tokens: 800.
    - System message: `SYSTEM_PROMPT_RECOMMEND` (nutritionist, JSON‑only).
    - User message: a structured profile string built by `_build_recommend_user_prompt`.
    - Parses JSON similarly (stripping fences, JSON‑loading).
    - Returns `DEFAULT_RECOMMENDATIONS` fallback on structure problems.
    - Error handling:
      - `APIError` → `HTTPException(503)`.
      - `JSONDecodeError` → `HTTPException(422)`.
      - Generic → `HTTPException(500, "AI recommendations failed. Please try again.")`.

### 1.4 Image upload handling

- **Frontend** (`index.html`):
  - Live camera:
    - `initCamera()` uses `navigator.mediaDevices.getUserMedia` with `facingMode` (`environment`/`user`), `width/height` ideals.
    - Video element `#camera-feed` displays stream.
    - HTTPS guard:
      - If `location.protocol !== 'https:'` and hostname not `localhost`/`127.0.0.1`, shows explicit guidance and refuses to open camera.
    - Graceful error copy for:
      - Permission denied (`NotAllowedError`).
      - No device (`NotFoundError`).
      - Generic errors.
  - Capture:
    - `captureFood()`:
      - Shows loading overlay `#scan-loading`.
      - Optionally vibrates (haptic feedback).
      - Draws the current frame to a hidden canvas, scaled to max dimension 1024.
      - Gets JPEG base64 via `canvas.toDataURL('image/jpeg', 0.78)` and strips prefix.
      - Calls `sendToScan(base64)`.
  - File upload:
    - Hidden file input `#file-upload` with `accept="image/*"`.
    - `handleFileUpload(event)`:
      - Reads selected file with `FileReader.readAsDataURL`.
      - Strips data URL prefix to base64.
      - Calls `sendToScan`.
      - Resets input value to allow re‑selecting same file.
  - `sendToScan(base64)`:
    - Uses `apiCall('/food/scan', 'POST', { image_base64, meal_type, user_id })`.
    - Handles loading overlay, empty items, and error toasts with normalized messages.
- **Backend**:
  - `FoodScanRequest.image_base64`:
    - Pydantic `Field(..., min_length=100, max_length=5_000_000)`, ensuring presence and size limit.
  - `food_routes.scan_food`:
    - Explicit non‑empty check:
      - If missing or whitespace only, returns `400 "Image data is required"`.
    - Passes base64 string directly to `scan_food_image` (no server‑side decoding into file).

### 1.5 Auth system

- **Password hashing**:
  - `auth.py`:
    - `CryptContext` configured with `schemes=["sha256_crypt"]`.
    - `get_password_hash` / `verify_password` wrap hashing/verification.
    - Motivated by bcrypt/Python 3.14 compatibility; still secure when configured correctly.
- **JWT tokens**:
  - `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` from `.env` with sane defaults.
  - `create_access_token`:
    - Adds `"exp"` claim with configured expiry (default 1440 minutes = 24h).
  - `get_current_user`:
    - Uses `HTTPBearer` to read `Authorization: Bearer <token>`.
    - Decodes JWT, extracts `"sub"` as user id string, converts to `int`.
    - On any JWT error, returns `401 "Session expired, please login again"`.
    - Verifies user exists and `is_active` before returning.
  - `auth.register` / `auth.login`:
    - Both return `TokenWithUser` (JWT token + serialized user).
    - Login path handles invalid credentials with `401 "Invalid email or password"`.
- **Frontend storage**:
  - `authToken` is kept only in a JS variable; not persisted to `localStorage`/`sessionStorage`.
  - All API calls go through `apiCall`, which conditionally adds `Authorization: Bearer <token>`.
  - On `401`, `apiCall` clears `authToken` and `currentUser` and routes user back to login.

### 1.6 Module connections

- `backend/main.py`:
  - Loads environment, sets up DB via `Base.metadata.create_all`.
  - Configures CORS with `ALLOWED_ORIGINS` or a wide dev default including `localhost:3000` and `127.0.0.1:3000` plus other ports.
  - Imports and mounts routers:
    - `auth.router` at `/auth`.
    - `food_routes.router` at `/food`.
    - `user_routes.router` at `/users`.
- `auth.py`:
  - Depends on:
    - `database.get_db` for DB sessions.
    - `models.User` for DB operations.
    - `schemas.UserCreate`, `UserLogin`, `UserResponse`, `TokenWithUser`.
  - Exposes `calculate_daily_calories` and `get_current_user`, which are used by `user_routes` and `food_routes`.
- `food_routes.py`:
  - Depends on:
    - `auth.get_current_user` as auth guard for all routes.
    - `database.get_db`.
    - `models.User`, `FoodLog`, `ScanLog`.
    - `schemas` for typing of responses (`FoodScanRequest`, `FoodScanResponse`, `FoodItem`, `FoodLogResponse`).
    - `openai_service.scan_food_image`.
  - This is the main integration point between image uploads and AI.
- `user_routes.py`:
  - Depends on:
    - `auth.get_current_user` and `calculate_daily_calories`.
    - `database.get_db`.
    - `models.User`, `FoodLog`, `Recommendation`.
    - `schemas.StatsResponse`, `UserResponse`, `UserUpdate`.
    - `openai_service.get_recommendations`.
- `openai_service.py`:
  - Only called from `food_routes` and `user_routes`; hidden from frontend.
- `frontend/index.html`:
  - Frontend JS uses `API_BASE = 'http://localhost:8000'` and `apiCall` to call backend routes.
  - Maintains `currentUser` object mirroring `UserResponse` from backend, and uses it across:
    - `loadDashboard`, `loadFoodLog`, `loadRecommendations`, `drawProgressCharts`, `refreshSettingsProfile`, `saveProfileChanges`, `exportPDF`.

Overall, module wiring matches the reference structure in `.cursorrules` and is cohesive: each layer has a clear responsibility and depends on the layer directly below (UI → API → services/models → DB/OpenAI).

---

## PHASE 2: USER FLOW ANALYSIS

### 2.1 High‑level journey

The complete high‑level user journey, as implemented, is:

1. **App open**:
   - File: `frontend/index.html`.
   - Function: `onReady()` → `bindDOM()` → `showScreen('landing')`.
   - Data:
     - Initializes global state: `authToken`, `currentUser`, `logViewDate`, etc.
   - Failure points:
     - Global `window.onerror` replaces body with a “Script error” page if any uncaught error occurs, but this now only triggers during genuine runtime failures.
   - Validation:
     - None needed at this stage; only initialization and static UI.

2. **Onboarding (register / login)**:
   - Screens:
     - `screen-landing` → `screen-login` or `screen-register`.
   - **Register (step 1)**:
     - HTML elements: `#reg-name`, `#reg-email`, `#reg-password`, `#reg-continue-btn`, `#reg-error`, password strength meter.
     - Function chain:
       - `bindDOM()` attaches `click` on `reg-continue-btn` to `validateRegisterStep()`.
       - `validateRegisterStep()`:
         - Reads name, email, password.
         - Validates non‑empty name, email, and min password length.
         - Sets `registerData = { name, email, password }`.
         - Calls `showVoiceChoice()` to choose between voice onboarding and manual form.
     - Failure points:
       - Missing fields or short password lead to inline error + warning toast.
       - Any exception inside `showVoiceChoice()` is caught; error message is shown inline and via toast; console logs retained for debugging.
     - Backend not called yet; all validation is front‑end.
   - **Voice vs manual setup decision**:
     - `showVoiceChoice()` dynamically builds a modal with two buttons:
       - “Use Voice Setup” → `startVoiceOnboarding()`.
       - “Fill Form Instead” → `showScreen('setup')`.
     - This ensures the user has a clear fallback if they do not want voice.
   - **Login**:
     - Screen: `screen-login`.
     - Function: `handleLogin()` (wired via `bindDOM` and inline `onclick`).
     - Data:
       - Reads `#login-email` and `#login-password`.
       - Calls `apiCall('/auth/login', 'POST', { email, password })`.
       - On success:
         - Sets `authToken` and `currentUser`.
         - Shows success toast.
         - Navigates to `showScreen('dashboard')`.
       - On failure:
         - Shows inline error `#login-error` and displays `#login-hint` (“New here? ...” semantics).
     - Backend:
       - `auth.login` verifies credentials; uses Pydantic `UserLogin` and `UserResponse`.
       - Failure points:
         - 400/401 returns `Invalid email or password` which surfaces in the UI inline only (no duplicate toast).
         - Network errors:
           - `apiCall` catches `TypeError` from fetch; shows offline banner and rethrows a descriptive error.
     - Validation:
       - Simple non‑empty fields check on frontend.
       - Backend enforces email format and ensures credentials correctness.

3. **Voice input onboarding (optional)**:
   - Screen: `screen-voice`.
   - Data:
     - `VOICE_QUESTIONS` array (in JS) defines 5 questions with keys:
       - `age` (number).
       - `weight_kg` (number).
       - `height_cm` (number).
       - `gender` (select_gender).
       - `goal` (select_goal).
     - `voiceAnswers` object accumulates answers.
   - Functions:
     - `startVoiceOnboarding()` → `reset voice state` → `showScreen('voice')` → `showVoiceQuestion()`.
     - `showVoiceQuestion()`:
       - Renders question text, progress dots, input widgets based on `type`.
       - For `number`, displays numeric input and submit button.
       - For select types, renders selectable buttons/cards; taps call `processVoiceAnswer` immediately.
     - `toggleListening()`, `startListening()`, `stopListening()`:
       - Manage `recognition` object (global).
       - Always abort existing recognition before starting new one, with a delay.
     - `processVoiceAnswer(raw)`:
       - Normalizes speech/text input to numeric values or specific enum values.
       - Validates ranges:
         - Age: 10–120.
         - Weight: 20–300 kg.
         - Height: 50–250 cm.
       - Updates `voiceAnswers[q.key]`, refreshes summary, and advances `voiceIndex`.
     - `updateProgressDots()`, `updateSoFarSummary()`:
       - Keep visual state and summary in sync with `voiceIndex`.
     - `submitVoiceProfile()`:
       - Merges `registerData` and `voiceAnswers`.
       - Calls `apiCall('/auth/register', 'POST', body)`:
         - Body must satisfy `UserCreate` Pydantic constraints:
           - Name length, email format.
           - Password length.
           - Age, weight, height ranges.
           - Gender and goal regex values.
       - On success:
         - Sets `authToken` and `currentUser`.
         - Navigates to `dashboard`.
       - On failure:
         - Shows toast with error.
         - Reveals `#voice-recovery` section with:
           - “Try Again” button → calls `submitVoiceProfile()` again.
           - “Fill Form Instead” → `prefillSetupFromVoice()` → `showScreen('setup')`.
   - Failure points:
     - Browser lacks speech recognition or permissions: voice flow gracefully falls back to typed inputs.
     - Backend rejects registration due to validation errors: error surfaces in toast and the user can switch to the setup form with preserved answers.

4. **Manual health profile setup (fallback/complement to voice)**:
   - Screen: `screen-setup`.
   - Data:
     - Uses `registerData` and `voiceAnswers` to prefill fields.
     - `selectedGender`, `selectedGoal`.
   - Functions:
     - `initSetupScreen()`:
       - Populates name from `registerData.name`.
       - Prefills age, weight, height, gender, goal from `voiceAnswers` if present.
       - Updates slider badges (`#weight-val`, `#height-val`).
       - Calls `updateCaloriePreview()`.
     - `toggleNameEdit()`:
       - Toggles read‑only name display vs editable input.
     - `selectGender(value)` / `selectGoal(value)`:
       - Update selection state and call `updateCaloriePreview()`.
     - `updateCaloriePreview()`:
       - Implements Harris‑Benedict formula client‑side (consistent with `.cursorrules` and `auth.calculate_daily_calories`).
       - Applies activity factor 1.375 and goal adjustments (−500 / +300 / 0).
       - Enforces minimum 1200 kcal.
     - `submitSetupForm()`:
       - Validates:
         - Name present.
         - Age within 10–120.
         - Gender and goal selected.
       - Locks button with spinner and “Creating your plan...” copy.
       - Builds body with:
         - `registerData` fields.
         - Name, age, weight, height, gender, goal from UI.
       - Calls `apiCall('/auth/register', 'POST', body)`.
       - On success: sets `authToken`/`currentUser`, navigates to `dashboard`.
       - On failure: toast error, button restores.
   - Backend:
     - Uses exact same `auth.register` endpoint; Pydantic ensures numeric ranges and enum correctness.

5. **Food image upload / scanning**:
   - Screen: `screen-scan`.
   - Data:
     - `selectedMealType` (default `'lunch'`).
     - `lastScanResult` for the currently displayed bottom sheet.
   - Functions:
     - Navigation:
       - Bottom nav center FAB and various buttons call `showScreen('scan')`.
       - `showScreen('scan')` calls `initCamera()` and hides bottom nav where appropriate.
     - `initCamera()` / `stopCamera()`:
       - Set up and tear down `stream`.
       - On `visibilitychange` or leaving the scan screen, camera is stopped for security/battery.
     - `captureFood()` / `handleFileUpload()` / `sendToScan()` / `showScanResults()`:
       - Already detailed in 1.4.
   - Backend:
     - `food_routes.scan_food`:
       - Checks `current_user.id` vs `request.user_id` (authz).
       - Ensures user exists.
       - Requires non‑empty `image_base64`.
       - Enforces daily scan limit via `ScanLog` (50 scans/day).
       - Calls `scan_food_image(image_base64)` (OpenAI).
       - Persists each item into `FoodLog` with macros and calories.
       - Returns `FoodScanResponse` including:
         - Items list.
         - Aggregated totals.
         - Calorie range and confidence from AI (or defaults).
         - Clarification questions.
   - Failure points:
     - Exceeded scan limit → 429 with clear detail; `sendToScan` surfaces this as toast.
     - Empty items from OpenAI → returns zero totals and no items; UI shows a “No food detected” message.
     - OpenAI or network errors:
       - Handled by `openai_service` and surfaced via error messages; UI displays “Scan failed: ...”.
     - Large/corrupted uploads:
       - Mitigated by `max_length` on `image_base64` and by frontend downscaling to 1024px.

6. **Backend processing and AI call**:
   - Sequence for a successful scan:
     1. `apiCall('/food/scan', 'POST', {...})` from frontend.
     2. FastAPI validates `FoodScanRequest` against Pydantic; rejects invalid lengths/types.
     3. `food_routes.scan_food`:
        - Auth guard ensures JWT validity.
        - Verifies `user_id` belongs to `current_user`.
        - Limits scans via `ScanLog`.
        - Calls `scan_food_image(image_base64)`.
     4. `scan_food_image`:
        - Calls GPT‑4o with system + user prompts and image.
        - Parses JSON into `result` dict with items and metadata.
     5. `scan_food`:
        - Aggregates macros and calories.
        - Creates `FoodLog` entries and persists.
        - Returns `FoodScanResponse`.
     6. Frontend:
        - `sendToScan` stores result in `lastScanResult` → `showScanResults` renders the bottom sheet.
        - On accept, `acceptScanResults()` refreshes dashboard and navigates to it.

7. **Result display and data storage**:
   - **Dashboard**:
     - `loadDashboard()` retrieves:
       - `stats` from `/users/stats/{id}`.
       - Today log from `/food/log/today/{id}`.
     - Renders:
       - Calorie ring with consumed vs goal.
       - BMI value and category (consistent with backend’s `_bmi_category`).
       - Macro progress bars (targets derived from goal calories).
       - Water intake quick action.
       - Quick actions for scan/tips/log.
       - Recent items.
   - **Food log screen**:
     - `loadFoodLog()` fetches today log and stores in `todayLogData`.
     - `renderFoodLog` displays grouped meals, removable items, totals, and macros.
     - `changeLogDate` allows going back in time conceptually, but only today’s data is actually available (backend only provides daily totals via `stats` and 7‑day summary; not per‑day log for arbitrary dates).
   - **History / progress**:
     - `drawProgressCharts()`:
       - Calls `/users/stats/{id}` again.
       - Uses `stats.last_7_days` to build:
         - Bar chart of calories.
         - Doughnut chart of macros using today’s log.
   - **Recommendations**:
     - `loadRecommendations()` calls `/users/recommendations/{id}` and renders:
       - Greeting.
       - Suggested next meal with per‑food macros.
       - Foods to avoid.
       - Health tip, water reminder, progress messages.
     - Accepts responses where backend either returns the bare JSON or a wrapper with `.content` JSON string (covers historical Recommendation rows).

### 2.2 Validation and failure handling summary per step

For each key step, validation and failure behaviors are:

- **Registration**:
  - Frontend:
    - Non‑empty fields and min password length.
    - Clear inline error messages and warning toasts.
  - Backend:
    - Pydantic constraints on name/email/password/age/weight/height/gender/goal.
    - Unique email enforced by DB and explicit query check.
- **Login**:
  - Backend:
    - Clean 401 with generic but accurate message.
  - Frontend:
    - Single inline error; suggestion hint after failed attempt.
- **Voice onboarding**:
  - Robust normalization and range checks.
  - Clear toast messages for invalid/missing numbers.
- **Food scan**:
  - Pydantic length limits on image.
  - `400` for missing image.
  - `403` if mismatched `user_id`.
  - `404` if user missing.
  - `429` for excessive scans.
  - Graceful AI/JSON errors mapped to user‑friendly messages.
- **Recommendations**:
  - Safe fallback `DEFAULT_RECOMMENDATIONS` if JSON invalid.
  - Errors from OpenAI normalized to friendly HTTP error messages.

---

## PHASE 3: AI WORKFLOW ANALYSIS

### 3.1 Image processing path

- **Client‑side**:
  - Downscales captured frame to a maximum dimension of 1024px; compression at JPEG quality 0.78.
  - Uses base64 encoding of JPEG data and sends as JSON.
  - This reduces payload size while preserving enough detail; there is no multi‑angle or scale marker, so portion estimation is purely visual.
- **Server‑side**:
  - Does not decode or inspect the image; treats base64 as opaque and constructs `data:image/jpeg;base64,<...>` URL for OpenAI.
  - No explicit checks on image type; relies on client ensuring JPEG/PNG.

### 3.2 OpenAI models and configuration

- **Scan**:
  - Model: `gpt-4o`.
  - Temperature: 0.3 (as required by `.cursorrules`).
  - Max tokens: 1000 (aligned with cost protection guidance).
  - Prompts instruct:
    - Strict JSON output (no markdown, no explanation).
    - Use USDA standard nutritional values.
    - Return calorie range, confidence, and clarifying questions.
- **Recommendations**:
  - Model: `gpt-4o`.
  - Temperature: 0.7 (allows more varied suggestions).
  - Max tokens: 800.
  - System prompt and user prompt emphasize:
    - Reference to profile (age, BMI, goal).
    - Reference to today’s food.
    - Return JSON with specific keys.

### 3.3 Prompt structure

- **`SYSTEM_PROMPT_SCAN`**:
  - Defines role, instructs to identify visible food items.
  - Emphasizes honest uncertainty statements and approximate but realistic estimates.
- **`USER_MESSAGE_SCAN`**:
  - Fully enumerates expected JSON keys and semantics.
  - Specifies default empty/no‑food object to return when no food is detected.
  - Repeats the JSON‑only constraint.
- **`SYSTEM_PROMPT_RECOMMEND` + `_build_recommend_user_prompt`**:
  - System prompt sets the persona and JSON‑only requirement.
  - User prompt:
    - Encodes user profile fields and a text list of foods eaten.
    - Provides consumed and remaining calories.
    - Specifies exact JSON keys and nested structure for `next_meal`.

Overall, prompts are reasonably structured and explicit about JSON shape. They do not use function calling or JSON schema tools from the OpenAI SDK, but rely on instruction‑following.

### 3.4 Temperature control and randomness

- Scan: Temperature fixed at 0.3, suitable for consistency and relatively stable calorie estimates.
- Recommendations: Temperature 0.7, moderate creativity while likely preserving consistency.
- No runtime controls are exposed to the user; both temperatures are fixed.

### 3.5 Response parsing and safety

- All OpenAI responses:
  - Strip potential triple‑backtick JSON fences.
  - Parse via `json.loads`.
- **Scan**:
  - Accepts both legacy list format and current dict format.
  - Coerces numeric fields into `float`.
  - Validates that `items` is a list; otherwise uses empty list.
  - If parsing fails outright, returns HTTP 422 with explicit “Could not parse AI response from AI model”.
  - On unexpected types, returns a safe empty object.
- **Recommendations**:
  - If parsing or structure fails, returns `DEFAULT_RECOMMENDATIONS` rather than raising; this avoids user‑visible exceptions but may hide upstream issues.

### 3.6 JSON validation and schema enforcement

- There is no explicit JSON schema validation layer beyond:
  - Basic type checks in code.
  - The final Pydantic models consumed in routes (e.g., `FoodScanResponse`, but only at response_model level in route).
- Risks:
  - If GPT returns partial objects, some fields may be undefined; the code handles this via `.get()` and default fallback values.
  - However, more rigorous JSON schema validation (e.g., via `pydantic.TypeAdapter`) could provide stricter guarantees.

### 3.7 Error handling and retry logic

- Error handling:
  - Network/API errors map to 503 with a generic “AI service temporarily unavailable”.
  - Parse errors map to 422 with explicit message.
  - Generic exceptions map to 500 with generic but user‑friendly text.
- Retry logic:
  - **Not implemented** at the OpenAI client layer.
  - Frontend flows allow manual retry:
    - For scans: user can recapture or reupload on failure.
    - For recommendations: “Refresh Tips” button triggers a new call.
    - For voice registration: explicit “Try Again” button.
- Given the typical reliability of OpenAI, this is acceptable but not resilient to transient 5xx network issues; a small automatic retry with backoff would improve robustness.

---

## PHASE 4: NUTRITION LOGIC VALIDATION

### 4.1 Calorie calculation

- **Daily calorie goals (TDEE)**:
  - Backend: `auth.calculate_daily_calories`:
    - Implements Harris‑Benedict BMR formulas with:
      - Male and female variants.
      - “Other” gender as average of the two.
    - Applies activity factor 1.375.
    - Adjusts goal by:
      - −500 kcal for `lose_weight`.
      - +300 kcal for `gain_muscle`.
      - 0 for `maintain`.
    - Enforces minimum 1200 kcal.
  - Frontend: `updateCaloriePreview` in `index.html`:
    - Uses the same formulas and adjustments.
    - Uses `selectedGender` (default `'male'`) and `selectedGoal` (default `'maintain'`).
    - Derives a displayed approximate daily target with `~<kcal>`.
  - Consistency:
    - Logic between frontend and backend aligns with `.cursorrules` specification and each other.
    - Backend re‑computes daily goal whenever relevant profile fields change.

- **Per‑meal calories**:
  - Determined by AI output:
    - Each `FoodItem` includes `calories` and macros; the backend does not adjust these.
  - No internal nutrition database is implemented; AI is the sole source of per‑item energy/macros.

### 4.2 Portion scaling and uncertainty

- Portion scaling:
  - AI is instructed to estimate `quantity_g` and total calories per item.
  - There is no post‑scan manual adjustment UI yet (e.g., slider to scale quantity).
  - However, AI’s `quantity_g` is persisted and shown in the UI, which provides context.
- Uncertainty margin:
  - `calorie_range_min` and `calorie_range_max` from AI are surfaced:
    - `showScanResults`:
      - If min/max differ, displays `<min>–<max> kcal`.
      - Else shows single `total_calories` value.
  - `confidence`:
    - Converted to percentage and displayed as “AI confidence: <pct>% (estimate, not exact)” in the clarification section.
- Assumptions communication:
  - The UI explains that estimates are approximate and dependent on lighting and framing when no questions/confidence are available.
  - Deeper explanation (e.g., “we assumed 600 g total, medium oil”) is not explicitly surfaced; this is an opportunity for future improvement.

### 4.3 Recommendation logic

- Inputs:
  - `user_data` with:
    - Name, age, gender, weight, height, goal.
    - Daily calorie goal.
    - BMI (computed again even though backend already does it for stats).
  - `today_foods` list:
    - Name, calories, quantity, meal type for today’s log entries.
  - Derived:
    - `consumed` (sum of today’s calories).
    - `remaining` (daily goal minus consumed).
    - `food_list` string summarizing today’s intake.
- AI responsibilities:
  - Choose next meal suggestions consistent with:
    - Goal (weight loss, muscle gain, maintain).
    - Remaining calories and BMI.
  - Provide lists of foods to avoid.
  - Provide health and water tips and progress message.
- Logic consistency:
  - All personalization is handled by the AI; backend does not enforce calorie deficit or macronutrient boundaries beyond what prompt suggests.
  - The prompt explicitly mentions tying reasoning back to profile and today’s log, but it does not enforce, e.g., “ensure remaining calories are not exceeded.”
  - Conflict handling:
    - Not explicitly enforced in code; left to AI (e.g., not recommending a 1200 kcal meal when only 200 kcal remain).

---

## PHASE 5: DATA MODEL & DATABASE REVIEW

### 5.1 Tables and schema

```1:65:C:\Users\anand\Downloads\Nutrition\nutriscan-ai\backend\models.py
class User(Base):
```

- **User**:
  - Columns:
    - `id` (PK, indexed).
    - `name`, `email` (unique, indexed), `password_hash`.
    - `age`, `weight_kg`, `height_cm`, `gender`, `goal`.
    - `daily_calorie_goal` (int).
    - `created_at` (`datetime`).
    - `is_active` (bool).
  - Relationships:
    - `.food_logs` → list of `FoodLog`.
    - `.recommendations` → list of `Recommendation`.
- **FoodLog**:
  - Columns:
    - `id` (PK, indexed).
    - `user_id` (FK to User, indexed).
    - `food_name` (string 200).
    - `quantity_g`, `calories`, `protein_g`, `carbs_g`, `fat_g`.
    - `meal_type` (string 20).
    - `scan_time` (`datetime`).
- **Recommendation**:
  - Columns:
    - `id` (PK, indexed).
    - `user_id` (FK to User).
    - `content` (TEXT, typically JSON).
    - `created_at`.
- **ScanLog**:
  - Columns:
    - `id` (PK, indexed).
    - `user_id` (FK, indexed).
    - `scan_date` (`date`, defaults to `date.today`).
    - `scan_count` (int).
  - Unique constraint on `(user_id, scan_date)` for rate limiting.

### 5.2 Food log, user profile, and AI result storage

- Food logs:
  - Each scan persists one `FoodLog` per item with macros and meal type.
  - Daily summaries and history are computed via aggregate queries (no denormalized totals).
- User profile:
  - Stored in `User` with daily goals and physical parameters.
  - Profile updates recompute `daily_calorie_goal` when relevant fields change.
- AI results:
  - Recommendations:
    - Stored in `Recommendation.content` as raw JSON (string).
    - `user_routes.get_user_recommendations` returns the parsed JSON; the frontend also handles receiving already persisted structures.
  - Scan AI metadata (range, confidence, questions) is not stored; only per‑item macros and calories are persisted in `FoodLog`.

### 5.3 Indexing and performance

- Existing indices:
  - PKs and explicit `index=True` on:
    - `User.id`, `User.email`.
    - `FoodLog.id`, `FoodLog.user_id`.
    - `Recommendation.id`.
    - `ScanLog.id`, `ScanLog.user_id`.
  - `ScanLog` also has a unique index on `(user_id, scan_date)`.
- Query patterns:
  - Daily totals and counts use `func.date(FoodLog.scan_time) == date`.
  - History uses loops over dates with two aggregations per day.
- Observations:
  - For SQLite and expected project scale, performance is adequate.
  - For higher traffic or Postgres, consider:
    - Indexes on `(user_id, scan_time)` or expression indexes on `date(scan_time)`.
    - Bulk aggregation queries over ranges rather than per‑day loops.

### 5.4 Migrations and schema evolution

- There is no migration tool (e.g., Alembic) in the repository.
- Tables are created via `Base.metadata.create_all` at:
  - `database.py` import time.
  - `main.py` app lifespan.
- Risks:
  - Schema changes require manual DB migration or dropping/recreating the DB.
  - For SQLite and student project context, this is acceptable but not ideal for production.

### 5.5 Data consistency risks

- Denormalized fields:
  - `daily_calorie_goal` in `User` is derived from age/weight/height/goal/gender.
  - Backend recalculates this on relevant updates, but if changes are made directly in DB, it may go stale.
- Deletion semantics:
  - Deletion of `FoodLog` entries via API does not adjust any cached totals (since totals are always aggregated at query time, this is safe).
  - Recommendations are never cleaned up; this is mostly a storage concern.
- Error tolerance:
  - Recommendations content may be partially invalid JSON for older rows; the frontend defends against this by parsing only if `rec.content` is a string and expecting a dict shape, but there is still risk of parse errors for mismatched historical format.

---

## PHASE 6: EDGE CASES & FAILURE RISKS

### 6.1 Image edge cases

- **Empty image**:
  - Frontend: `sendToScan` ensures it always passes a non‑empty `base64` string when camera/file works.
  - Backend:
    - `FoodScanRequest` `min_length=100` prevents obviously trivial payloads.
    - `scan_food` checks `if not (request.image_base64 and request.image_base64.strip())` → 400.
- **Large image**:
  - Frontend downscales to 1024px, limiting payload size.
  - Backend uses `max_length=5_000_000` for base64 string; if the client bypasses downscaling, this prevents extreme payloads.
- **Corrupted upload**:
  - Corruption will surface at OpenAI level:
    - Likely as `APIError` or possibly leading to invalid JSON output; both are handled with appropriate HTTP exceptions.
- **Non‑food images**:
  - Prompt instructs the model to return an empty items array with zeroes when no food is detected.
  - `food_routes.scan_food` handles this by returning a zeroed `FoodScanResponse`, and the UI shows a warning without logging items.

### 6.2 OpenAI/timeouts/JSON failures

- Timeouts and network issues:
  - Not explicitly configured (default HTTP timeouts from SDK).
  - Any `APIError` maps to `503 "AI service temporarily unavailable"` for both scan and recommendations.
- JSON parsing failure:
  - `JSONDecodeError` → `422` with clear messages for both scan and recommendations.
  - Frontend displays these via toast.

### 6.3 Rate limits and user abuse

- Per‑user scan rate limiting:
  - `ScanLog` with `scan_count` per `user_id`+`scan_date`, hard cap at 50 per day.
  - This protects the OpenAI key from brute‑force abuse on scanning.
- Other endpoints:
  - No explicit rate limiting implemented on recommendations or auth.
  - However, typical project usage patterns make this acceptable initially; for production, more generic rate limiting would be advisable.

### 6.4 Concurrent uploads and race conditions

- Concurrent scans:
  - Each scan increments `ScanLog.scan_count` and persists `FoodLog` items inside a single request transaction.
  - There is a small risk of race conditions under high concurrency on the same user/date due to simplistic `scan_log.scan_count++` with immediate commit; however, typical usage makes this low risk.
- Frontend state:
  - `lastScanResult` is overwritten on each scan; bottom sheet uses the last response only.
  - `apiCall` is stateless; no global concurrent request coordination is required.

---

## PHASE 7: SECURITY REVIEW

### 7.1 API key exposure

- API key is read only in `openai_service._get_client` via `os.getenv("OPENAI_API_KEY")`.
- Key is never sent to frontend; all AI calls are server‑side.
- `.env` is located in backend directory and is not part of the documented API.

### 7.2 Server‑side protection

- CORS:
  - Configured via `ALLOWED_ORIGINS` env var, or a controlled default list of local dev origins.
  - `allow_credentials=True` and `allow_headers=["*"]` are appropriate for this JWT setup.
- Auth enforcement:
  - All food and user endpoints use `get_current_user` dependency.
  - Direct `user_id` path parameters are always checked against `current_user.id` to prevent horizontal privilege escalation.

### 7.3 Input sanitization

- Backend uses Pydantic models to sanitize and validate:
  - Email addresses.
  - String lengths.
  - Numeric ranges for age, weight, height, and image base64 length.
  - Enforced regex for gender and goal values.
- Food names and other text fields are not sanitized beyond length; for SQLite this is sufficient to guard against SQL injection (ORM handles parameterization), but for UI cleanliness one might eventually add further constraints.

### 7.4 Auth security

- JWT:
  - Reasonably configured with exp claims and robust error handling.
  - Uses `HS256` symmetric signing with configurable secret.
- Passwords:
  - `sha256_crypt` from `passlib` is used; this is less preferred than bcrypt/argon2 for production, but it is a hardened password hashing scheme.
- Token storage:
  - Tokens are kept only in memory in the SPA; page refresh logs the user out.
  - This minimizes XSS persistence risk at the cost of convenience.

### 7.5 File upload safety

- No actual file storage; images are not written to disk.
- AI calls operate on data URLs.
- This fully avoids the usual file upload security class of issues (e.g., RCE via image parsing on server).

---

## PHASE 8: PRODUCTION READINESS SCORE

Scores are from 0–10, based purely on current implementation.

- **Architecture**: **8/10**
  - Clear separation of concerns and modules.
  - Reasonable use of FastAPI, Pydantic, SQLAlchemy, and OpenAI SDK.
  - Minor duplication in DB table creation; migrations not present.
- **AI reliability**: **7/10**
  - Good prompt structure and explicit JSON contract.
  - Robust parsing and error mapping.
  - No automatic retry or circuit‑breaker patterns.
- **Error handling**: **8/10**
  - Backed by consistent HTTPException usage and frontend toasts.
  - Offline banner for network failures.
  - Some flows (e.g., recommendations fallback) may hide root causes but keep UX stable.
- **Scalability**: **6/10**
  - SQLite, single process, per‑user rate limiting only on scans.
  - Adequate for demo/single‑user load; would need Postgres, async DB, and generalized rate limits for scale.
- **Security**: **7/10**
  - Decent JWT practices, password hashing, authorization checks, input validation.
  - No CSRF concerns (pure API + SPA).
  - No general WAF / rate limiting on login or recommendations.
- **UX clarity**: **8/10**
  - Flows are strongly guided; errors are inline and toasts are clear.
  - Onboarding, scan feedback, and offline indications are well‑implemented.
- **Data consistency**: **7/10**
  - Most totals are aggregated at query time; limited risk of stale denormalized fields.
  - Lack of migrations and manual DB updates could generate inconsistencies in the future.

---

## PHASE 9: IMPROVEMENT ROADMAP

### 9.1 Immediate fixes (critical)

- **Add minimal retry logic for OpenAI calls**:
  - Wrap `client.chat.completions.create` with a small retry (1–2 attempts) on retriable errors (timeouts, 5xx).
  - Ensure retries are bounded with backoff (e.g., 200–500 ms).
- **Harden rate limiting across endpoints**:
  - Introduce generic rate limiting middleware or external gateway for:
    - `/auth/login` (to mitigate brute force).
    - `/users/recommendations/{id}` (to prevent overuse).

### 9.2 Stability improvements

- **Add structured logging**:
  - Deploy `logging` with per‑endpoint context for scan/recommendation failures.
  - Avoid `print`; log summarized exceptions and trace IDs.
- **Introduce health check probes**:
  - Extend `/health` to include:
    - Database connectivity test.
    - Optional OpenAI connectivity test flag (without making a full model request).

### 9.3 Accuracy improvements

- **Portion adjustment UI**:
  - After scan, allow user to tweak `quantity_g` per item via sliders and automatically recompute macros and totals (without calling AI again).
  - Store user‑corrected values back into `FoodLog`.
- **Clarification loop**:
  - Use `questions_for_user` to ask a lightweight follow‑up and send corrected context to a refinement endpoint (e.g., `/food/scan/refine`).

### 9.4 Performance improvements

- **DB indexing and query optimization**:
  - For production DBs, add composite indexes:
    - `FoodLog(user_id, scan_time)`.
    - `FoodLog(user_id, meal_type, scan_time)` if needed.
  - Combine 7‑day history aggregates into a single grouped query instead of per‑day loops.
- **Static asset optimization**:
  - Minify CSS/JS and consider extracting JS into a separate file to leverage browser caching more effectively.

### 9.5 Monetization upgrades

- Add:
  - Soft paywall around:
    - Daily recommendation count.
    - Advanced analytics (long‑term trends).
  - “Upgrade to Pro” call‑to‑action backed by:
    - Client‑side feature flags and backend entitlements table (e.g., `Subscription` model).

### 9.6 Scaling strategy

- **Backend**:
  - Migrate DB to Postgres.
  - Use async DB driver (e.g., `asyncpg` with SQLAlchemy async engine).
  - Run multiple FastAPI workers behind a reverse proxy (NGINX/Traefik).
- **AI usage**:
  - Cache repeated recommendations for the same day/user.
  - Introduce a `scan_id` field and tie follow‑up recommendations or corrections to that id.
- **Observability**:
  - Add metrics (Prometheus, OpenTelemetry) for:
    - Scan success/failure rates.
    - OpenAI latencies and error codes.
    - Recommendation usage per user/day.

This concludes the `PROJECT_SYSTEM_AUDIT.md` technical and architectural analysis based solely on the current implementation.

