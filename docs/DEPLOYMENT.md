# Deployment Guide

This repository is prepared for a split deployment:

- `frontend/` deploys to Vercel as a Vite SPA.
- `backend/` deploys to Render as a Django web service.
- PostgreSQL runs on Render.
- Redis and Celery stay disabled in production because the current app does not require them.

## Production changes in this repository

- Django now uses production-safe host, CORS, CSRF, HTTPS, and static-file settings driven by environment variables.
- WhiteNoise serves Django static files, including the admin UI, on Render.
- Render build and start scripts run `collectstatic`, apply migrations, and start Gunicorn.
- Production deployment does not run `seed_demo`.
- Seeded demo passwords are no longer written to logs unless explicitly enabled.
- The frontend API base URL is environment-driven and reused consistently.
- Demo login autofill and password hints are disabled unless `VITE_ENABLE_DEMO_LOGIN=true`.
- Vercel SPA routing is configured so deep links resolve to `index.html`.

## Vercel frontend

Create a Vercel project from this repository and set the Root Directory to `frontend`.

Set this environment variable in Vercel:

- `VITE_API_URL=https://<your-render-backend-domain>/api/v1`

Optional:

- `VITE_ENABLE_DEMO_LOGIN=false`

Build settings can stay on Vercel defaults once the Root Directory is `frontend`.

The SPA rewrite lives in `frontend/vercel.json`.

## Render backend

You can deploy either with the `render.yaml` Blueprint in the repo root or by creating the service manually.

### Blueprint path

The included `render.yaml` provisions:

- one Python web service named `seatbite-backend`
- one PostgreSQL database named `seatbite-db`

The web service uses:

- Root Directory: `backend`
- Build Command: `./build.sh`
- Start Command: `./start.sh`
- Health Check Path: `/api/v1/products/`

### Manual Render setup

If you do not use the Blueprint, create:

1. A PostgreSQL database on Render.
2. A Python web service pointing at this repository with Root Directory `backend`.
3. Build Command `./build.sh`
4. Start Command `./start.sh`

### Backend environment variables

Required:

- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `SEATBITE_CUSTOMER_URL`

Recommended:

- `DJANGO_ALLOWED_HOSTS=<your-render-domain>,<any-custom-api-domain>`
- `CORS_ALLOWED_ORIGIN_REGEXES=` only if you intentionally allow preview domains
- `WEB_CONCURRENCY=3`
- `DJANGO_DB_CONN_MAX_AGE=60`
- `SEATBITE_SHOW_SEED_CREDENTIALS=false`

Notes:

- Use Render's internal Postgres connection string for `DATABASE_URL`.
- `RENDER_EXTERNAL_HOSTNAME` is automatically supplied by Render and is added to `ALLOWED_HOSTS` automatically.
- If you add a custom backend domain, also add it to `DJANGO_ALLOWED_HOSTS`.
- If the frontend runs on a custom Vercel domain, add that exact origin to both `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`.

## Database and static files

- Production uses PostgreSQL through `DATABASE_URL`.
- SQLite remains available only as a local fallback when `DEBUG=true`.
- Static files are collected into `backend/staticfiles` during Render builds and served by WhiteNoise.
- No persistent media disk is required for the current app because product images are external URLs and QR/PDF assets are generated in memory.

## Demo data

- Do not run `python manage.py seed_demo` in production.
- Create a real admin user on Render with `python manage.py createsuperuser`.
- Demo credentials are for local/demo environments only.

## Deployment order

1. Deploy the Render backend and database.
2. Set backend env vars, especially frontend origin values.
3. Confirm the backend is healthy at `https://<render-domain>/api/v1/products/`.
4. Deploy the Vercel frontend with `VITE_API_URL` pointing to the Render backend.
5. Verify deep links such as `/login`, `/customer/qr/<token>`, and `/admin`.
