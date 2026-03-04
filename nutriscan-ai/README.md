# Smart AI Food Scanner (NutriScan AI)

Mobile-first nutrition app: scan food with camera, get AI-powered recommendations, track macros and water.

## Quick Start

### 1. Backend (FastAPI)

Backend is at repo root: `../backend` (Render uses Root Directory: `backend`).

```bash
cd ../backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Add OPENAI_API_KEY to .env
uvicorn main:app --host 127.0.0.1 --port 8002 --reload
```

Or run `.\START-BACKEND.ps1` from this folder.

### 2. Frontend

```bash
cd frontend
py -3 -m http.server 3001
```

Open http://127.0.0.1:3001

## Project Structure

- `frontend/` — Single-page HTML/CSS/JS app (PWA-ready)
- `../backend/` — FastAPI REST API, SQLite/PostgreSQL, OpenAI GPT-4o (at repo root for Render)

See [NUTRISCAN_TEACHING_GUIDE.md](NUTRISCAN_TEACHING_GUIDE.md) for full system explanation.

## Production

- **Frontend:** Netlify — `nutriscan-ai/frontend`
- **Backend:** Render — Root Directory `backend` (at repo root)
- Set `DEBUG=False`, use strong `SECRET_KEY`
- Configure `ALLOWED_ORIGINS` for your domain
- See [DEPLOY.md](DEPLOY.md), [RENDER_SETUP.md](RENDER_SETUP.md), [DEPLOYMENT_URLS.md](DEPLOYMENT_URLS.md)

## Cleanup Note

If `nutriscan-ai/backend/` exists (old duplicate): stop any running uvicorn, then delete the folder. The canonical backend is at repo root `backend/`.
