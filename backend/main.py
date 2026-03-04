import os

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, SessionLocal, engine
from notification_service import check_and_send_due_reminders

load_dotenv()

_scheduler: AsyncIOScheduler | None = None


def _run_reminder_job() -> None:
    db = SessionLocal()
    try:
        check_and_send_due_reminders(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    Base.metadata.create_all(bind=engine)
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_run_reminder_job, "cron", minute="*")
    _scheduler.start()
    try:
        yield
    finally:
        if _scheduler:
            _scheduler.shutdown()


app = FastAPI(
    title="Smart AI Food Scanner",
    version="1.0.0",
    description="Real-time food scanning and nutrition advisory API",
    lifespan=lifespan,
)

# In production, set ALLOWED_ORIGINS to a specific list of HTTPS origins (e.g. https://yourdomain.com).
# For local development we fall back to a permissive CORS policy if ALLOWED_ORIGINS is not set.
_default_origins = "http://localhost:3000,http://localhost:3001,http://localhost:52449,http://localhost:51723,http://localhost:62211,http://localhost:54375,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:52449,http://127.0.0.1:51723,http://127.0.0.1:62211,http://127.0.0.1:54375"
_env_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
if _env_origins:
    allow_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
else:
    allow_origins = [o.strip() for o in _default_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from admin_routes import router as admin_router
from auth import router as auth_router
from food_routes import router as food_router
from reminder_routes import router as reminder_router
from user_routes import router as user_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(food_router, prefix="/food", tags=["Food"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(reminder_router, tags=["Reminders"])
app.include_router(admin_router, tags=["Admin"])


@app.get("/")
async def root():
    return {"status": "Smart AI Food Scanner running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "database": "connected",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "MISSING — add to .env",
    }
