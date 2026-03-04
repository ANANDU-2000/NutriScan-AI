# NutriScan AI — Deploy to Render + Vercel

Step-by-step guide to deploy backend (Render) and frontend (Vercel) for free.

---

## Before You Start

1. **GitHub repo**: Push your code to `ANANDU-2000/NutriScan-AI` (or your repo)
2. **OpenAI key**: Get from https://platform.openai.com/api-keys
3. **Accounts**: Render.com, Vercel.com (both have free tiers)

---

## Step 1: Create PostgreSQL on Render (Free)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. **New** → **PostgreSQL**
3. Name: `nutriscan-db`
4. Region: **Singapore**
5. Plan: **Free**
6. **Create Database**
7. Copy the **Internal Database URL** (starts with `postgres://`)

---

## Step 2: Deploy Backend to Render

1. **New** → **Web Service**
2. Connect **GitHub** → select `NutriScan-AI` repo
3. Configure:

| Field | Value |
|-------|-------|
| **Name** | NutriScan-AI |
| **Region** | Singapore |
| **Branch** | main |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance** | Free |

4. **Environment Variables** (Add each):

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | Your OpenAI key |
| `SECRET_KEY` | Random string (e.g. `openssl rand -hex 32`) |
| `DATABASE_URL` | Paste the PostgreSQL URL from Step 1 |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` (add Vercel URL after Step 4) |

5. **Create Web Service**
6. Wait for deploy. Copy your backend URL: `https://nutriscan-ai-xxxx.onrender.com`

---

## Step 3: Update Frontend API URL

Backend URL: `https://nutriscan-ai-tfv4.onrender.com` (already set in `frontend/index.html`)

---

## Step 4: Deploy Frontend to Vercel

1. Go to [Vercel](https://vercel.com) → **Add New** → **Project**
2. Import `NutriScan-AI` from GitHub
3. Configure:

| Field | Value |
|-------|-------|
| **Root Directory** | `frontend` |
| **Framework Preset** | Other |
| **Build Command** | (leave empty) |
| **Output Directory** | `.` |

4. **Deploy**
5. Copy your Vercel URL: `https://nutriscan-ai-xxxx.vercel.app`

---

## Step 5: Connect Backend and Frontend

1. Go back to **Render** → your NutriScan-AI service → **Environment**
2. Edit `ALLOWED_ORIGINS`:
   - Add your Vercel URL: `https://nutriscan-ai-xxxx.vercel.app`
   - Can add multiple: `https://app1.vercel.app,https://app2.vercel.app`
3. **Save** → Render will auto-redeploy

---

## Step 6: Push to GitHub

```bash
cd C:\Users\anand\Downloads\Nutrition\nutriscan-ai
git add .
git status
git commit -m "Production: Render + Vercel deploy config"
git push origin main
```

---

## Environment Variables Reference

### Backend (Render)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `SECRET_KEY` | Yes | JWT signing secret |
| `DATABASE_URL` | Yes | PostgreSQL URL from Render DB |
| `ALLOWED_ORIGINS` | Yes | Vercel frontend URL(s), comma-separated |
| `ALGORITHM` | No | Default: HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: 1440 |

### Frontend (Vercel)

No env vars needed. API URL is in `index.html` (see Step 3).

---

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
# Create .env from .env.example, use SQLite (no DATABASE_URL)
uvicorn main:app --reload --port 8002

# Frontend: serve index.html (Live Server, or npx serve frontend)
# API_BASE auto-detects localhost
```

---

## Troubleshooting

- **CORS errors**: Add your Vercel URL to `ALLOWED_ORIGINS` on Render
- **502 Bad Gateway**: Free instances spin down after 15 min inactivity; first request may take 30–60s
- **Database connection failed**: Check `DATABASE_URL` format; Render uses `postgres://` (we convert to `postgresql://`)
