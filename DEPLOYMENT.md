# Tryggve.ai Production Deployment Guide

This guide covers deploying the FastAPI backend and Next.js frontend using Docker Compose, PostgreSQL, and Nginx as a single hardened production stack.

## Architecture

```
Internet → Nginx (:80)
              ├── /api/*  → backend:8000  (FastAPI + Uvicorn)
              └── /*      → frontend:3000 (Next.js standalone)
                         backend → db:5432 (PostgreSQL)
```

All secrets are injected via `.env.production` — never baked into images.

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- A Gemini API key ([Google AI Studio](https://aistudio.google.com/apikey))
- A domain name (recommended) pointing to your host

## 1. Generate production secrets

Use cryptographically strong values. Examples on Linux/macOS:

```bash
openssl rand -base64 32    # POSTGRES_PASSWORD
openssl rand -hex 32       # alternative
```

On Windows PowerShell:

```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

Create your production env file:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` and set:

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Strong random password (special characters like `@` are supported) |
| `GEMINI_API_KEY` | Valid Gemini API key |
| `CORS_ORIGINS` | Your public site origin, e.g. `https://tryggve.example.com` |
| `NEXT_PUBLIC_API_BASE_URL` | Leave **empty** when using Nginx same-origin routing |

**Security rules:**

- Add `.env.production` to `.gitignore` (already excluded via `.env.*` pattern).
- Rotate `POSTGRES_PASSWORD` and `GEMINI_API_KEY` on a schedule.
- Restrict file permissions: `chmod 600 .env.production`.

## 2. Build and start the stack

From the repository root:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

First startup may take several minutes while the backend embeds demo regulations via Gemini.

Check service health:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

Verify endpoints:

```bash
curl http://localhost/health
curl http://localhost/api/v1/health
```

Open the dashboard at `http://localhost/` (or your domain).

## 3. CORS lockdown verification

Production CORS is controlled by `CORS_ORIGINS` in `.env.production`. The backend **must not** use `*` in production.

### Expected configuration

```env
CORS_ORIGINS=https://tryggve.example.com
ENVIRONMENT=production
```

With Nginx serving both UI and API on the same origin, browsers make same-origin requests and CORS preflight is typically not triggered for dashboard usage. CORS still protects direct API access from other websites.

### Verify CORS is restricted

**1. Preflight from an unauthorized origin should fail:**

```bash
curl -i -X OPTIONS http://localhost/api/v1/report \
  -H "Origin: https://evil.example.com" \
  -H "Access-Control-Request-Method: POST"
```

Look for **no** `Access-Control-Allow-Origin: https://evil.example.com` header.

**2. Authorized origin should succeed (when testing without Nginx same-origin):**

```bash
curl -i -X OPTIONS http://localhost/api/v1/report \
  -H "Origin: https://tryggve.example.com" \
  -H "Access-Control-Request-Method: POST"
```

Replace the origin with your actual `CORS_ORIGINS` value.

**3. Confirm wildcard is not active:**

```bash
docker compose -f docker-compose.prod.yml exec backend printenv CORS_ORIGINS
```

Output must **not** be `*`.

## 4. Security hardening checklist

| Control | Implementation |
|---------|------------------|
| Non-root containers | Backend runs as `appuser`; frontend as `nextjs` |
| Secret management | `.env.production` via Compose `env_file` |
| DB persistence | Named volume `postgres_data` |
| Reverse proxy | Nginx hides internal ports; only :80 exposed |
| Security headers | `X-Frame-Options`, `X-Content-Type-Options`, `server_tokens off` |
| Upload limit | `client_max_body_size 20M` in Nginx |
| Restart policy | `restart: always` on all services |
| Health checks | Postgres, backend, frontend before Nginx starts |

### Recommended additions before public launch

- Terminate TLS at Nginx or a cloud load balancer (Let's Encrypt / ACM).
- Set `CORS_ORIGINS` to your exact HTTPS origin only.
- Run `UVICORN_WORKERS=1` if you need consistent in-process Chroma RAG state across requests (each worker holds its own vector store).
- Add rate limiting at Nginx or a WAF.
- Enable automated Postgres backups from the `postgres_data` volume.

## 5. Operations

**View logs:**

```bash
docker compose -f docker-compose.prod.yml logs -f nginx backend frontend db
```

**Restart after env change:**

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

**Stop stack (data preserved):**

```bash
docker compose -f docker-compose.prod.yml down
```

**Stop and remove volumes (destructive):**

```bash
docker compose -f docker-compose.prod.yml down -v
```

**Database shell:**

```bash
docker compose -f docker-compose.prod.yml exec db psql -U tryggve -d tryggve
```

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Backend unhealthy on first boot | Wait for Gemini embedding init; check `GEMINI_API_KEY` |
| `502 Bad Gateway` from Nginx | Ensure backend/frontend healthchecks pass |
| CORS errors in browser | Set `CORS_ORIGINS` to exact frontend URL with scheme |
| Frontend calls wrong API | Rebuild frontend with empty `NEXT_PUBLIC_API_BASE_URL` |
| Postgres connection refused | Wait for `db` healthcheck; verify `POSTGRES_*` vars |

## File reference

| File | Purpose |
|------|---------|
| `backend/Dockerfile.prod` | Hardened Python 3.11 backend image |
| `frontend/Dockerfile.prod` | Multi-stage Next.js standalone image |
| `docker-compose.prod.yml` | Orchestrates db, backend, frontend, nginx |
| `nginx/nginx.conf` | Reverse proxy and security headers |
| `.env.production.example` | Template for production secrets |
