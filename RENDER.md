# Render Blueprint Deployment

Deploy the Tryggve.ai monorepo to [Render](https://render.com) using the free tier and `render.yaml`.

## Prerequisites

- GitHub repo with this monorepo pushed
- Render account
- Gemini API key

## Deploy steps

1. Push code to GitHub (ensure `render.yaml` is at the repo root).

2. In Render Dashboard → **New** → **Blueprint** → connect your repo.

3. Render reads `render.yaml` and prompts for `sync: false` secrets:
   - `GEMINI_API_KEY` — your Gemini API key
   - `CORS_ORIGINS` — frontend URL after deploy, e.g. `https://tryggve-frontend.onrender.com`
   - `NEXT_PUBLIC_API_BASE_URL` — backend URL, e.g. `https://tryggve-backend.onrender.com`

4. Apply the Blueprint. Render creates:
   - `tryggve-db` (PostgreSQL 15, free)
   - `tryggve-backend` (Python/FastAPI)
   - `tryggve-frontend` (Node/Next.js)

5. **After backend deploys**, copy its URL (`https://tryggve-backend.onrender.com`) and set `NEXT_PUBLIC_API_BASE_URL` on the frontend service, then **Manual Deploy** the frontend (this var is baked at build time).

6. Set `CORS_ORIGINS` on the backend to your frontend URL if not done during Blueprint setup.

## Verify

```bash
curl https://tryggve-backend.onrender.com/health
curl https://tryggve-backend.onrender.com/api/v1/health
```

Open `https://tryggve-frontend.onrender.com` and submit a test report.

## Free tier notes

- Services spin down after inactivity (~50s cold start on first request).
- Chroma regulation embeddings rebuild on each deploy (ephemeral disk).
- Use `uvicorn --workers 1` on Render free tier (configured in `render.yaml`).
- Free Postgres expires after 90 days unless upgraded.

## Monorepo layout

```
backend/     ← FastAPI (rootDir for tryggve-backend)
frontend/    ← Next.js (rootDir for tryggve-frontend)
render.yaml  ← Blueprint at repo root
```

Local dev still uses `backend/` for uvicorn and `frontend/` for Next.js — see root `README.md`.
