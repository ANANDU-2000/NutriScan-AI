# Render Deploy Fix — Root Directory

## Fixed

Backend has been moved to repo root. Structure is now:
```
Nutrition/ (repo root)
├── backend/       ← Backend code (Render uses Root Directory: backend)
└── nutriscan-ai/
    └── frontend/  ← Frontend (Netlify uses nutriscan-ai/frontend)
```

Render with **Root Directory: `backend`** will now work. Push to main to trigger deploy.
