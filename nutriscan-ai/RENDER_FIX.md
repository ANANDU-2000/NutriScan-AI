# Render Deploy Fix — Root Directory

## Problem
```
Root directory "backend" does not exist
```

Your repo structure is:
```
Nutrition/ (repo root)
└── nutriscan-ai/
    ├── backend/   ← Backend code is here
    └── frontend/
```

## Fix (1 minute)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Open your **NutriScan-AI** (or backend) Web Service
3. Click **Settings** (left sidebar)
4. Find **Root Directory**
5. Change from `backend` to **`nutriscan-ai/backend`**
6. Click **Save Changes**
7. Go to **Manual Deploy** → **Deploy latest commit**

---

After this, builds will succeed and the 500 errors should stop (they were from the failed deploy).
