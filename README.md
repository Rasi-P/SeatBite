# SeatBite

**Food delivered to your seat.** SeatBite is a cinema food ordering platform with a mobile customer experience, live kitchen and delivery operations, and a venue admin console.

## What works

- Secure seat QR resolution with seat-specific customer sessions.
- Venue-filtered food catalog with real photography, offers, server-priced cart, tax, and immutable snapshots.
- Simulated UPI/card/cash payment that confirms a real backend order.
- Role-validated `CONFIRMED -> PREPARING -> READY -> OUT_FOR_DELIVERY -> DELIVERED` workflow.
- Customer tracking polling, staff Kanban, delivery seat map, admin analytics, catalog management, seats, and QR downloads.
- PostgreSQL/Redis Docker environment, audit history, and backend tests.

## Quick start

Prerequisites: Docker Desktop with Docker Compose.

```bash
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173). The backend is at [http://localhost:8000](http://localhost:8000), and the browsable Django admin is at [http://localhost:8000/admin](http://localhost:8000/admin).

The backend container applies migrations on startup. It does not seed demo data automatically.

## Initial setup

After the stack is running, create your first admin user:

```bash
docker compose exec backend python manage.py createsuperuser
```

Then sign in at `/admin` or `/login` and load your real data:

1. Create your venue.
2. Create screens and seats.
3. Generate seat QR codes.
4. Add categories, products, and offers.
5. Create staff users and assign roles.

Customer ordering starts when guests scan one of the generated seat QR codes.

## Local development without Docker

The Django settings use SQLite when `DATABASE_URL` is absent, which is useful only for local tests. PostgreSQL remains the default composed environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

## Verification

```bash
cd backend && python manage.py test
cd frontend && npm run build
```

Architecture and security decisions are documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The endpoint map is in [`docs/API.md`](docs/API.md).
Production deployment instructions for Vercel + Render are in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
