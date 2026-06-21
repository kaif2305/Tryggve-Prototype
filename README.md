# AI Safety Reporting Prototype

A minimal FastAPI backend that turns short worker incident narratives (optionally with a photo) into structured occupational-safety reports with root-cause analysis, grounded in a small demo regulation corpus.

**This is a prototype**, not production-ready software. Architectural shortcuts are marked with comments in the code.

## Prerequisites

- Python 3.11+
- A [Gemini API key](https://aistudio.google.com/apikey)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
# Edit .env and set GEMINI_API_KEY=your_key_here  (get one at https://aistudio.google.com/apikey)

# 4. Run the API
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive Swagger UI.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/report` | Submit incident (`text` form field, optional `image` file) |
| `GET` | `/reports` | List all reports (newest first) |
| `GET` | `/reports/{id}` | Fetch one report |

### Example: submit a text-only report

```bash
curl -X POST http://127.0.0.1:8000/report -F "text=Worker slipped on icy steps near the loading bay this morning."
```

## Architecture (prototype)

1. **Layer 1 — Extraction**: Gemini flash model structures the raw narrative into title, description, and hazard category (multimodal if a photo is attached).
2. **RAG retrieval**: Query embedding finds the top-3 similar demo regulation snippets in an in-process Chroma store.
3. **Layer 4 — Root cause**: Second Gemini call produces 5-Whys, MTO classification, and a Hierarchy-of-Controls recommendation grounded in retrieved snippets.
4. **Persistence**: SQLite via SQLAlchemy (swap `DATABASE_URL` for Postgres later).

## Run backend + frontend together

Open two terminals from the project root:

```powershell
# Terminal 1 — API (port 8000)
cd "D:\AI Projects\PR\backend"
..\.venv\Scripts\activate
uvicorn main:app --reload

# Terminal 2 — Next.js dashboard (port 3000)
cd "D:\AI Projects\PR\frontend"
npm run dev
```

Open http://localhost:3000 for the dashboard. The frontend posts to `http://localhost:8000/api/v1/report`.

Optional: set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` if the API runs elsewhere.

## Image annotation (v1 API)

`POST /api/v1/report` returns a `ReportResponse` with `report.hazards_detected` (normalized 0–1000 boxes) and `annotated_image_base64` (JPEG with red boxes drawn via Pillow).

## Troubleshooting

**`gemini_configured: false`** — your key is missing or not being read. Ensure `.env` has `GEMINI_API_KEY=your_key` with **no space after `=`**, then restart uvicorn. If you previously exported `GEMINI_API_KEY` in your shell, close that terminal or run `Remove-Item Env:GEMINI_API_KEY` (PowerShell) before starting the server.

**Startup error: `API key not valid`** — the key in `.env` is present but rejected by Google. Create a new key at https://aistudio.google.com/apikey and replace the value in `.env`, then restart.

## Out of scope

Authentication, multi-tenancy, voice/ASR, production observability, semantic caching, container orchestration, and official regulation corpora.

## Render (cloud)

See [RENDER.md](RENDER.md) for Blueprint deployment to Render free tier.
