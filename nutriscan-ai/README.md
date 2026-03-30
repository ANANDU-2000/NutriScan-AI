# Smart AI Food Scanner

Mobile-first nutrition app: scan food with camera, get AI-powered recommendations, track macros and water.

## Quick Start

### 1. Backend (FastAPI)

```bash
cd backend
.venv\Scripts\activate   # or: python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
# Add OPENAI_API_KEY to .env
uvicorn main:app --host 127.0.0.1 --port 8002 --reload
```

### 2. Frontend

```bash
cd frontend
py -3 -m http.server 3001
```

Open http://127.0.0.1:3001

### 3. Django Admin (optional)

```bash
cd django_admin
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8003
```

Open http://127.0.0.1:8003/admin/

## Project Structure

- `frontend/` — Single-page HTML/CSS/JS app (PWA-ready)
- `backend/` — FastAPI REST API, SQLite, OpenAI GPT-4o
- `django_admin/` — Django super admin for users, logs, reminders, food prices

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for details. See [UX_WORKFLOW.md](UX_WORKFLOW.md) for user flow and architecture.

## Production

- Set `DEBUG=False`, use strong `SECRET_KEY`
- Configure `ALLOWED_ORIGINS` for your domain
- Use HTTPS
- See `backend/.env.example`
