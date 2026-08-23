# SeatBite

**Food delivered to your seat.** SeatBite is a production-minded Phase-1 cinema food ordering demo with a mobile customer experience, live kitchen/delivery operations, and a venue admin console.

## What works

- Secure seat QR resolution for `CineMax Calicut`, including the scripted `Screen 2 · F12` demo.
- Venue-filtered food catalog with real photography, offers, server-priced cart, tax, and immutable snapshots.
- Simulated UPI/card/cash payment that confirms a real backend order.
- Role-validated `CONFIRMED -> PREPARING -> READY -> OUT_FOR_DELIVERY -> DELIVERED` workflow.
- Customer tracking polling, staff Kanban, delivery seat map, admin analytics, catalog management, seats, and QR downloads.
- PostgreSQL/Redis Docker environment, deterministic seed command, audit history, and backend tests.

## Quick start

Prerequisites: Docker Desktop with Docker Compose.

```bash
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173). The backend is at [http://localhost:8000](http://localhost:8000), and the browsable Django admin is at [http://localhost:8000/admin](http://localhost:8000/admin).

The backend container applies migrations and runs `seed_demo` on startup. The command is idempotent, so restarting does not duplicate the scripted dataset.

## Demo accounts

All staff accounts use password `SeatBite@123`.

| Experience | Username | Email | Route |
| --- | --- | --- | --- |
| Super admin | `admin` | `admin@seatbite.demo` | `/admin` |
| Venue manager | `manager` | `manager@seatbite.demo` | `/admin` |
| Kitchen | `kitchen` | `kitchen@seatbite.demo` | `/staff` |
| Delivery | `delivery` | `delivery@seatbite.demo` | `/staff` |

Customer login is not required. The seeded F12 QR opens:

```text
http://localhost:5173/customer/qr/uJ7cV2nQ9mL4xR8pK6sT3wZ5aB1dF0hG
```

## Demonstration flow

1. Open the customer demo and confirm `Screen 2 · Row F · Seat 12`.
2. Add Caramel Popcorn, Coke, or a Movie Combo, then complete the simulated payment.
3. Open a separate window as `kitchen`; accept the new order and mark it ready.
4. Sign in as `delivery`; start the delivery, use the seat map, and mark it delivered.
5. Watch the customer order page update automatically throughout the workflow.

## Local development without Docker

The Django settings use SQLite when `DATABASE_URL` is absent, which is useful only for local tests. PostgreSQL remains the default composed environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py seed_demo
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
# SeatBite
