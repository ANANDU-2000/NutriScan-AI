# Render Setup — NutriScan AI Backend

## Database (Created)

| Item | Value |
|------|-------|
| Name | nutriscan-db |
| Region | Singapore |
| Status | Available |
| Expires | April 3, 2026 (Free tier) |

### URLs

- **Internal** (for Render backend): Render Dashboard → nutriscan-db → Connect → Internal Database URL
- **External** (for local dev): Same page → External Database URL

---

## Next Step: Create Web Service

1. Render Dashboard → **New** → **Web Service**
2. Connect **NutriScan-AI** repo
3. **Root Directory**: `backend`
4. **Build**: `pip install -r requirements.txt`
5. **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. **Instance**: Free

### Environment Variables (add in Render)

| Key | Value |
|-----|-------|
| `DATABASE_URL` | **Internal** Database URL from dashboard |
| `OPENAI_API_KEY` | Your OpenAI key |
| `SECRET_KEY` | Random string (e.g. `openssl rand -hex 32`) |
| `ALLOWED_ORIGINS` | `https://nutriscanaiapp.netlify.app` |
| `ALGORITHM` | `HS256` |
| `DEBUG` | `False` |

---

## Deployed

| Service | URL |
|---------|-----|
| Backend (Render) | https://nutriscan-ai-tfv4.onrender.com |
| Frontend (Netlify) | https://nutriscanaiapp.netlify.app |
| Database | nutriscan-db (Render PostgreSQL) |

Push to GitHub → Netlify auto-deploys. Test at https://nutriscanaiapp.netlify.app
