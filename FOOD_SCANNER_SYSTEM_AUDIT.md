## SECTION 1: COMPLETE USER EXPERIENCE FLOW

### 1.1 App open

- **Screen**: `screen-landing`.
- **Implementation**:
  - `onReady()` in `frontend/index.html` is called on `DOMContentLoaded` or immediately if DOM already loaded.
  - `onReady`:
    - Calls `bindDOM()` to wire login/register buttons, password eyes, and password strength meter.
    - Calls `showScreen('landing')`.
  - `showScreen('landing')`:
    - Adds `.active` class to `#screen-landing`.
    - Hides bottom nav (`#bottom-nav`).
    - Sets `currentScreen = 'landing'`.
  - Global `window.onerror` renders a fallback error page if any unhandled JS exception occurs, helping debug startup issues.
- **Data shown**:
  - Branding, hero text, benefit pills, primary CTA (“Get Started”) and secondary (“Already have an account?”).
- **User actions**:
  - Tap primary CTA → `showScreen('register')`.
  - Tap secondary CTA → `showScreen('login')`.
- **Backend calls**:
  - None.
- **State management**:
  - Globals are initialized (`authToken`, `currentUser`, `logViewDate`, etc.).
- **Loading/error handling**:
  - Not needed; static content.
- **UX friction**:
  - Low; copy is clear and visual design is strong.

### 1.2 Onboarding (register flow)

- **Screens**:
  - `screen-register` → `screen-voice` (optional) → `screen-setup` → `screen-dashboard`.
- **Data shown**:
  - Name, email, password fields.
  - Inline password strength indicator.
  - “Continue” button and subtle hints.
- **Key functions**:
  - `bindDOM()`:
    - Wires `#reg-continue-btn` click → `validateRegisterStep()`.
  - `validateRegisterStep()`:
    - Reads `#reg-name`, `#reg-email`, `#reg-password`.
    - Validates non‑empty name/email, password length ≥ 6.
    - Writes `registerData = { name, email, password }`.
    - On invalid inputs:
      - Shows inline error in `#reg-error`.
      - Displays warning toast.
    - On success:
      - Calls `showVoiceChoice()` to choose voice vs manual setup.
  - `showVoiceChoice()`:
    - Dynamically creates a modal (`#voice-choice-modal`) using DOM APIs.
    - Provides:
      - Button: “Answer with voice” → `startVoiceOnboarding()`.
      - Button: “Fill form instead” → `showScreen('setup')`.
- **Backend calls**:
  - Not yet; the first network call happens after voice or setup stage.
- **State management**:
  - `registerData` holds identity and credential fields across screens.
- **Loading/error handling**:
  - Inline errors and toasts for validation.
  - Errors inside `showVoiceChoice` are caught and surfaced.
- **UX friction**:
  - Minimal; user is actively guided with validation feedback.

### 1.3 Onboarding (login flow)

- **Screen**: `screen-login`.
- **Data shown**:
  - Email, password inputs.
  - “Login” button.
  - Inline error section `#login-error`.
  - Post‑failure hint `#login-hint` for new users.
- **Key functions**:
  - `bindDOM()` attaches `#login-btn` click → `handleLogin()`.
  - `handleLogin()`:
    - Validates presence of email/password.
    - On missing values:
      - Shows inline “Please fill in both fields.”
    - On submit:
      - Disables button and shows spinner + “Signing in...” text.
      - Calls `apiCall('/auth/login', 'POST', { email, password })`.
    - On success:
      - Sets `authToken`, `currentUser`.
      - Shows success toast.
      - Calls `showScreen('dashboard')`.
    - On failure:
      - Shows error message inline.
      - Displays `#login-hint` after any failure.
      - Restores button state.
- **Backend call**:
  - `/auth/login` (`auth.login`).
- **State management**:
  - `currentUser` is populated with `UserResponse`.
  - `authToken` used by subsequent `apiCall` calls.
- **Loading/error handling**:
  - Clear button loading state and auto‑dismiss toasts.
- **UX friction**:
  - Low; errors are explained and the hint provides a path to registration.

### 1.4 Voice input screen (optional)

- **Screen**: `screen-voice`.
- **Data shown**:
  - Title, step indicator, progress dots (5).
  - Current question text.
  - Mic button with listening animation.
  - Transcript card.
  - “So far” summary.
  - Input area:
    - Numeric input for age, weight, height.
    - Choice buttons for gender and goal.
  - Recovery section after failure.
- **Key functions and state**:
  - `VOICE_QUESTIONS`: strictly ordered as:
    - Age → Weight → Height → Gender → Goal.
  - `voiceIndex`, `voiceAnswers`, `recognition` (speech recognition instance).
  - `startVoiceOnboarding()`:
    - Resets state and navigates to `screen-voice`.
    - Calls `showVoiceQuestion()`.
  - `showVoiceQuestion()`:
    - Renders current question and appropriate input/choice controls.
    - Progress dots updated from `voiceIndex`.
  - `toggleListening()`, `startListening()`, `stopListening()`:
    - Manage `recognition` lifecycle.
    - Always abort previous recognition before starting new; include delay to avoid `InvalidStateError`.
  - `processVoiceAnswer(raw)`:
    - Normalizes string or numeric input.
    - Extracts numeric values for number questions and enforces range checks.
    - Maps natural language gender and goal phrases to canonical values.
    - On invalid input, shows toast and repeats question.
    - On valid input, saves in `voiceAnswers`, updates summary, advances `voiceIndex`, and either calls `submitVoiceProfile` or shows next question.
  - `submitVoiceProfile()`:
    - Shows fullscreen loading overlay.
    - Sends combined `registerData` + `voiceAnswers` to `/auth/register`.
    - On success:
      - Updates `authToken`/`currentUser`.
      - Hides loading.
      - Navigates to `dashboard`.
    - On failure:
      - Hides loading.
      - Toasts error.
      - Shows `#voice-recovery` with “Try Again” and “Fill Form Instead” options.
- **Backend calls**:
  - `/auth/register` (same as manual setup).
- **State management**:
  - `voiceAnswers` persists across attempts and can be used to prefill setup.
- **Loading/error handling**:
  - Loading overlay with specific text (“Creating your profile...”).
  - Clear fallback path to form setup.
- **UX friction**:
  - Well managed; users are not trapped in voice flow and can always switch to manual form while keeping captured answers.

### 1.5 Health profile setup and personalization

- **Screen**: `screen-setup`.
- **Data shown**:
  - Pre‑filled name, age (possibly from voice).
  - Gender buttons; weight and height sliders with large numeric badges.
  - Goal cards with strong visual differentiation for selection.
  - Calorie preview card, only shown after enough data is available.
- **Key functions**:
  - `initSetupScreen()`, `toggleNameEdit()`, `selectGender`, `selectGoal`, `updateCaloriePreview`, `submitSetupForm` (details in project audit).
- **Backend calls**:
  - `/auth/register`.
- **State management**:
  - Extends `registerData` with physical profile and goal; consolidated into a single request.
- **Loading/error handling**:
  - “Create My Plan →” button obtains spinner and disabled state during request.
  - Errors produce toasts; no inline messages here, but the state is simple enough.
- **UX friction**:
  - Visual enhancements (sliders, badges, goal cards) make the process feel interactive.
  - Only name input duplication vs register could be confusing; mitigated by read‑only with “Change” affordance.

### 1.6 Food image upload and scan

- **Screen**: `screen-scan`.
- **Data shown**:
  - Fullscreen camera preview or fallback error/help text.
  - Meal type pills (Breakfast/Lunch/Dinner/Snack).
  - Capture button at bottom and “Upload photo instead” option.
  - After scan: bottom sheet with:
    - Per‑item list and macros.
    - Calorie total or range.
    - Clarification and confidence section.
    - Accept button.
- **Key functions**:
  - `initCamera()`, `stopCamera()`, `flipCamera()`, `captureFood()`, `handleFileUpload()`, `sendToScan()`, `showScanResults()`, `acceptScanResults()`, `closeScanResults()` (detailed in project audit).
- **Backend calls**:
  - `/food/scan` via `sendToScan`.
- **State management**:
  - `selectedMealType`, `lastScanResult`, `currentUser`.
- **Loading/error handling**:
  - Visible overlay `#scan-loading` during scan.
  - Toasts for:
    - Camera not ready.
    - No food detected.
    - API errors or rate limits.
- **UX friction**:
  - Low: camera requirement is clearly explained in HTTP contexts.
  - However, there is no partial editing of AI estimates; quantity is fixed at AI output.

### 1.7 Result page (dashboard) and recommendation section

- **Screens**:
  - `screen-dashboard` (main hub).
  - `screen-recommend` (tips).
- **Dashboard**:
  - Data shown:
    - Greeting with name and date.
    - Streak days.
    - Calorie ring (consumed vs goal).
    - BMI and category.
    - Macro progress bars (protein, carbs, fat).
    - Water intake tracker.
    - Quick actions (Scan Food, Get Tips, View Log).
    - Recent meals list.
  - Backend calls:
    - `loadDashboard()` concurrently calls:
      - `/users/stats/{id}`.
      - `/food/log/today/{id}`.
  - State management:
    - `waterGlasses` is kept locally.
    - No caching beyond current run; each `loadDashboard` recomputes from backend.
  - Loading/errors:
    - Skeleton placeholders when loading.
    - Card with error message and “Try again” button on failure.
- **Recommendations**:
  - Data shown:
    - JSON fields from AI response: greeting, next_meal suggestions, foods_to_avoid_today, health_tip, water_reminder, goal_progress.
  - Backend calls:
    - `/users/recommendations/{id}` via `loadRecommendations()`.
  - State:
    - Does not persist recommendations; each load is fresh or uses previously stored `Recommendation.content` from DB (if backend returns that shape).
  - Loading/errors:
    - Initial “Analyzing your nutrition...” text.
    - Error message and Retry button on failure.

### 1.8 History page (log and progress)

- **Screens**:
  - `screen-log`.
  - `screen-progress`.
- **Log (history)**:
  - Data shown:
    - Card per meal (today only):
      - Items, macros, and per‑meal total.
    - Today’s total bar with progress vs daily goal.
    - Back/forward date selectors:
      - Only today is fully supported (older dates show high‑level “no data” message).
  - Backend calls:
    - `loadFoodLog()` calls `/food/log/today/{id}`.
    - No additional data for previous days; uses `todayLogData` for current day only.
  - State:
    - `logViewDate`, `todayLogData`.
  - Loading/errors:
    - Skeletons on load.
    - Clear error message on failure.
    - Deletion: `deleteLogEntry(logId)` calls `DELETE /food/log/{log_id}`, reloads log, and shows toast.
- **Progress**:
  - Data shown:
    - Weekly calories bar chart.
    - Macro distribution doughnut chart for today.
  - Backend calls:
    - `drawProgressCharts()`:
      - `apiCall('/users/stats/{id}')`.
      - Followed by `apiCall('/food/log/today/{id}')` for macros.
  - State:
    - `weeklyChartInstance`, `macroChartInstance` to allow chart destruction and recreation.
  - Loading/errors:
    - If no data for 7 days, shows “Log meals to see progress” and CTA to view log.

### 1.9 Profile page and re‑scan/edit flow

- **Screen**: `screen-settings`.
- **Data shown**:
  - Profile card (name, email).
  - BMI summary.
  - Edit form for weight and goal.
  - Reminder toggles and PDF export.
- **Backend calls**:
  - `refreshSettingsProfile()` renders from `currentUser` only (no API call).
  - `saveProfileChanges()`:
    - Calls `PUT /users/{id}` with weight and goal.
    - On success, updates `currentUser` and refreshes UI.
  - `exportPDF()`:
    - Calls `/food/log/today/{id}` then builds PDF client‑side via jsPDF.
- **Re‑scan/edit flows**:
  - From dashboard and log screens, CTAs push user back to `screen-scan` to rescan meals.
  - Edit of historical macros is limited to deletion + recapture; there is no manual adjustment UI yet.

### 1.10 UX gaps and confusion points

Observed gaps:

- Date navigation in log implies full historical browsing, but backend provides only today’s detailed log; past days show generic fallback text.
- AI estimates are not manually adjustable; some users will want to correct obviously over/under estimated portions.
- Confidence and questions are surfaced only on scan result sheet; they are not persisted or referenced later (e.g., on log or recommendations screens).
- Recommendations page assumes `rec` may be either a plain JSON object or an object with `.content` string; if backend behavior changes, parsing may break silently.

---

## SECTION 2: RECOMMENDATION SYSTEM LOGIC ANALYSIS

### 2.1 Recommendation generation type

- Implementation is fully **AI‑generated**, not rule‑based:
  - `user_routes.get_user_recommendations` always delegates to `openai_service.get_recommendations`.
  - There is no post‑processing beyond storing the raw JSON and returning it.

### 2.2 Dependency on user profile

- Inputs include:
  - Age, gender, weight, height.
  - BMI (recomputed).
  - Goal (lose weight/gain muscle/maintain).
  - Daily calorie goal.
  - Today’s consumed and remaining calories.
  - Food list string summarizing current day.
- The system prompt instructs the model to tie reasoning back to the profile and what the user ate today.
- Logic for BMI and daily goal is reused from the same conceptual formulas as in other parts of backend.

### 2.3 Calorie deficit and macro logic

- The backend does not explicitly implement calorie deficit or macro logic in recommendations; it only:
  - Provides daily goal and remaining margin.
  - Leaves the decision of how large the next meal should be to the model.
- Macros are not computed or passed; the model infers them from food names implicitly.
- Prompt expects:
  - `next_meal.total_calories` to be consistent with meal calories but does not enforce alignment with remaining daily goal.

### 2.4 Health goal incorporation

- Health goal is passed in string form (e.g., `lose_weight`, `gain_muscle`, `maintain`).
- Prompt encourages goal‑driven recommendations, but no explicit instructions such as “ensure next meal ≤ remaining calories” or “increase protein for gain_muscle.”
- This results in medium personalization; model is likely to adapt qualitatively but constraints are not algorithmically enforced.

### 2.5 Conflicts and logical contradictions

- Because there is no deterministic checking of AI’s suggested meal vs remaining calories, contradictions can occur:
  - Example: recommending a 900 kcal meal when remaining is 200 kcal.
- No server‑side guard rails to detect or correct:
  - Excessive total_energy vs remaining.
  - Unreasonably large portion sizes.

### 2.6 Personalization depth and repetition

- Personalization:
  - Based on profile + today’s log; not on longer‑term history.
  - No user preference tracking (e.g., vegetarian, allergies).
  - No explicit training or learning from user feedback/corrections.
- Repetition:
  - Without any memory beyond each call, suggestions may repeat across days/sessions.
  - Past `Recommendation` entries are stored but not used to modulate future outputs.

---

## SECTION 3: BACKEND PROMPT ENGINEERING REVIEW

### 3.1 Prompts for scanning

- Clear separation of `SYSTEM_PROMPT_SCAN` and `USER_MESSAGE_SCAN`.
- Strengths:
  - Repeated emphasis on valid JSON only.
  - Explicit schema with keys and subfields.
  - Direct instructions for no‑food scenarios.
  - Use of USDA standards recommended.
- Risks:
  - No explicit handling of multiple food contexts like “two plates” vs “one plate”.
  - No volume/scale context (e.g., coin or hand reference).

### 3.2 Prompts for recommendations

- `SYSTEM_PROMPT_RECOMMEND`:
  - Good emphasis on Indian dietary preferences and JSON‑only output.
- `_build_recommend_user_prompt`:
  - Presents structured but plain text.
  - Enumerates fields user side and lists today’s food in bullet‑like lines.
  - Defines JSON keys for `greeting`, `next_meal`, `foods_to_avoid_today`, `health_tip`, `water_reminder`, `goal_progress`.
- Improvements:
  - Could explicitly instruct the model to:
    - Respect `remaining` calories as a hard upper bound for `next_meal.total_calories`.
    - Balance macros by goal (high protein for muscle gain, reduced simple carbs for weight loss).
    - Include short rationales that mention BMI and remaining calories explicitly.

### 3.3 JSON schema enforcement

- No use of OpenAI function calling or JSON schema tools; the system relies solely on prompt wording.
- Parsing robustness:
  - Strips fences and handles both object and array returns.
  - Falls back to safe defaults when structure is wrong.
- There is no strong typed schema enforcement; mismatched types become zeros/empty lists.

### 3.4 Temperature, retries, and fallbacks

- Temperature and max_tokens are appropriate per use case.
- Retry logic is absent; single attempt per call.
- Fallbacks:
  - Scans: raise HTTP exceptions, forcing frontend to show error and allow manual retry.
  - Recommendations: fallback to `DEFAULT_RECOMMENDATIONS`, in effect masking upstream issues but preserving UX continuity.

### 3.5 Hallucination and injection risk

- Hallucination:
  - Inherent risk due to free text generation of macros and calories; mitigated by approximate nature of problem.
  - Confidence scores and ranges somewhat mitigate user trust issues.
- Prompt injection:
  - Inputs from user foods list and profile could hypothetically contain adversarial strings, but:
    - They are not coming from arbitrary user text (only from structured `FoodLog` and numeric fields).
    - The risk is low in this context.

---

## SECTION 4: DATA FLOW & STATE MANAGEMENT

### 4.1 UI → backend → OpenAI → DB → UI flow

- **Scan path**:
  1. UI collects base64 image and `meal_type`, `user_id`.
  2. `apiCall('/food/scan', 'POST', body)` sends JSON with JWT in header.
  3. Backend validates request, enforces auth and daily scan limits, and calls OpenAI.
  4. AI returns structured JSON; backend parses, aggregates macros, and writes `FoodLog` records.
  5. Backend returns `FoodScanResponse`.
  6. UI:
     - Shows bottom sheet with per‑item details, totals, range, confidence, and questions.
     - On accept, reloads dashboard, which queries current day stats and logs.

- **Recommendations path**:
  1. UI calls `apiCall('/users/recommendations/{id}', 'POST')`.
  2. Backend loads user, computes BMI, pulls today’s `FoodLog`, and builds `today_foods`.
  3. Backend builds prompt and calls GPT‑4o.
  4. Parses JSON and stores it in `Recommendation`.
  5. Returns JSON to UI, which renders cards.

### 4.2 State persistence and caching

- `currentUser` and `authToken` are in‑memory; no persistent auth across refresh.
- `todayLogData` caches a single day’s log for log screen.
- There is no explicit caching of scan results or recommendations beyond DB storage and current JS variables.

### 4.3 Race conditions and async handling

- `apiCall` is async and used consistently via `await`.
- Chart rendering ensures previous instances are destroyed before re‑instantiation.
- Camera handling is robust against:
  - Backgrounding the app (`visibilitychange`).
  - User navigating away from scan screen.
- Potential race:
  - Rapid multi‑tap on scan or recommendation actions could trigger overlapping calls; UI does some guarding (loading overlays and disabled buttons) but not exhaustive.

### 4.4 Error propagation and data mismatch

- Errors from backend propagate via normalized messages surfaced in `apiCall`, then shown as toasts or inline text.
- Mismatches between backend shape and frontend expectations have been largely harmonized:
  - Food scan now returns range and confidence fields used by UI.
  - Recommendations handle both plain JSON and persisted JSON string.

---

## SECTION 5: PERSONALIZATION ENGINE REVIEW

### 5.1 Current personalization behavior

- Personalization inputs:
  - Profile: age, gender, weight, height, BMI, goal, daily calorie goal.
  - Current day: foods eaten, per‑item calories, meal types.
  - Aggregates: consumed vs remaining calories.
- Effects:
  - AI is primed to adapt suggestions to goal and profile.
  - UI surfaces BMI category and calorie targets but does not directly couple them to AI suggestions beyond input data.

### 5.2 Missing personalization features

- No support for:
  - Dietary preferences (vegetarian/vegan, religious constraints).
  - Allergies or intolerances.
  - Food dislikes/likes.
  - Long‑term learning from repeated patterns or feedback (e.g., “this was too high calorie”).

### 5.3 TDEE and tracking

- TDEE and daily goal logic are robust and correctly implemented on both frontend and backend.
- Daily calorie tracking is done accurately via `FoodLog` sums and `StatsResponse`.
- There is no explicit long‑term target tracking (e.g., weekly/Monthly weight targets).

### 5.4 Proposed improved personalization architecture

To deepen personalization:

- Extend `User` model with:
  - `diet_type` (`veg`, `non_veg`, `vegan`, `jain`, etc.).
  - `allergies` (freeform text or structured tags).
  - `preferences` (liked/disliked cuisines or foods).
- Modify:
  - `user_routes.get_user_recommendations` to pass new fields into `user_data`.
  - `SYSTEM_PROMPT_RECOMMEND` and user prompt to instruct model to respect these constraints.
- Add feedback capture:
  - UI button(s) on recommendation cards (e.g., “Helpful” / “Not helpful”).
  - Persist simple counters in DB to feed into future prompts (e.g., “user dislikes fried foods”).

---

## SECTION 6: EDGE CASE LOGIC

### 6.1 Multiple foods and mixed dishes

- Prompt instructs AI to “identify every food item visible on the plate or in the bowl,” so multi‑food cases are expected.
- Mixed dishes (e.g., biryani) rely on model’s training; the app does not further decompose or reclassify them.

### 6.2 Non‑food images

- AI is instructed to return empty items and zeros when no food is visible.
- Frontend checks `result.items` length; if zero, it:
  - Shows warning toast.
  - Does not log any food.
  - Keeps the user on scan screen.

### 6.3 Low confidence and empty results

- Confidence:
  - Displayed as a percentage; clarifying text explains this is an approximate estimate.
- Clarification questions:
  - Shown as a bulleted list whenever AI returns any.
  - They are not yet used to refine the result; no follow‑up call is made.
- Empty results:
  - `scan_food_image` fallback ensures result structure is always present even when AI content is empty, preventing runtime errors.

### 6.4 Large images and upload edge cases

- Addressed with downscaling and Pydantic max_length; see project audit.
- No explicit check for unusual aspect ratios, but these typically only affect AI’s quality, not system stability.

### 6.5 Duplicate scans

- There is no deduplication of scans beyond rate limiting.
- Users can repeat scanning the same plate; each scan creates new `FoodLog` entries.

---

## SECTION 7: PRODUCTION STABILITY SCORE

Scores from 0–10, specific to the food scanner experience.

- **Architecture clarity**: **8/10**
  - Clear separation: scanning, logging, dashboard, recommendations, settings.
  - Data and control flows are easy to trace and reason about.
- **AI reliability**: **7/10**
  - Structured prompts, range/confidence outputs, and robust JSON parsing.
  - Lack of automatic retries and manual correction reduces this score.
- **Recommendation logic**: **6/10**
  - Fully AI‑driven with solid input context, but:
    - No post‑hoc constraint enforcement.
    - No multi‑day personalization or explicit macro balancing.
- **Personalization depth**: **5/10**
  - Uses core physical profile and goal, but misses preferences/allergies and adaptive learning.
- **UX clarity**: **8/10**
  - Scanner UX is strong: clear HTTP/HTTPS messaging, error copy, and guidance.
  - Onboarding flows are well organized and visually polished.
- **Error resilience**: **8/10**
  - Well‑handled AI errors, network failures, and camera issues.
  - Graceful fallbacks (manual setup, manual retry, no‑food handling).
- **Scalability**: **6/10**
  - Enough for demo/limited usage.
  - Requires DB and infrastructure upgrades for large‑scale deployment.
- **Monetization readiness**: **4/10**
  - App has clear user value loops (scan → log → recommendations), but:
    - No explicit subscriptions/tiers/quotas beyond scan rate limit.
    - No billing or plan concept implemented yet.

---

## SECTION 8: ADVANCED IMPROVEMENT ROADMAP

### 8.1 Critical fixes

- **Introduce structured JSON validation**:
  - Wrap AI outputs in Pydantic models (e.g., `FoodScanAIOutput`, `RecommendationOutput`) before mapping to domain types; reject malformed content early.
- **Limit abusive recommendation calls**:
  - Implement per‑user per‑day cap for `/users/recommendations/{id}` similar to `ScanLog`.

### 8.2 AI accuracy improvements

- **Clarification loop implementation**:
  - Add UI to capture answers to `questions_for_user` (e.g., radio buttons for oil quantity, homemade vs restaurant).
  - Add `/food/scan/refine` endpoint that:
    - Accepts original `scan_id`, clarifications, and prior AI output.
    - Calls GPT‑4o again with context “update your estimate given these answers,” adjusting totals accordingly.
- **Portion scaling and comparison**:
  - Introduce heuristics for checking whether AI’s `quantity_g` is plausible (e.g., bounding typical portion sizes) and mark estimates as “very approximate” when out of typical range.

### 8.3 Recommendation intelligence upgrades

- **Macro‑aware next meal planning**:
  - Compute macros from today’s log server‑side and pass summary to AI (`protein_today`, `target_protein`, etc.).
  - Update prompt to instruct the model to:
    - Compensate for imbalances (e.g., “low protein so far; add high‑protein foods”).
- **Hard calorie budget**:
  - Encode:
    - `remaining` as a firm upper bound on `next_meal.total_calories`.
  - Validate AI output; if it violates the budget by more than, say, 20%, either:
    - Ask AI to regenerate with stricter constraints.
    - Clamp suggestions to fit within remaining calories.

### 8.4 UX friction reduction

- **Better feedback on corrections**:
  - Allow users to:
    - Edit the name and macros of individual log entries.
    - Mark scans as “inaccurate” and optionally rescan.
  - Use this input to refine future suggestions (e.g., not recommending the same dish if user often marks it as misestimated).
- **Improve history UX**:
  - Implement full historical log retrieval at per‑day granularity.
  - Enhance date picker to show days with logs distinctly.

### 8.5 Personalization engine upgrade

- Extend profile:
  - Add preferences and restrictions fields and integrate them in both:
    - Recommendations.
    - Scan clarification (e.g., “is this dish vegetarian?”).
- Long‑term trends:
  - Use `StatsResponse.last_7_days` over longer horizons (e.g., 30 days) to compute adherence patterns (on‑track vs off‑track days).
  - Feed patterns into recommendations (e.g., “weekends are heavier; suggest lighter breakfast on Monday”).

### 8.6 Revenue optimization ideas

- **Freemium model**:
  - Free tier:
    - Limited daily scans and basic recommendations.
  - Pro tier:
    - Unlimited scans.
    - Advanced recommendation intelligence and macro‑aware planning.
    - Historical analytics and PDF exports (already implemented) bundled as premium.
- **Partner integrations**:
  - Consider recommending partner products (e.g., healthy snacks) in a separate, clearly labeled section, not mixed with core health tips.

### 8.7 Scaling strategy

- **Backend**:
  - Move to Postgres and async DB engine.
  - Introduce message queue for asynchronous tasks (e.g., generating long‑running reports).
- **OpenAI cost management**:
  - Track per‑user, per‑day token usage.
  - Consider caching repeated queries (e.g., similar logs for same user) and reusing recommendations within a day.
- **Observability and monitoring**:
  - Integrate with metrics/log aggregation tools.
  - Set alerts on:
    - Elevated AI error rates.
    - Latency spikes on `/food/scan` or `/users/recommendations`.

This `FOOD_SCANNER_SYSTEM_AUDIT.md` captures the current end‑to‑end behavior, strengths, and targeted improvements for the NutriScan AI food scanning experience, based solely on the actual implementation.

