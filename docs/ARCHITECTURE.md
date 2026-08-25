# SeatBite Phase-1 Architecture

## Runtime topology

```text
React / Refine / Ant Design
          |
          | REST + JWT or X-Session-Token
          v
      Django REST API
       /           \
PostgreSQL        Redis
source of truth   Celery-ready broker
```

The browser never supplies authoritative totals, order state, seat ownership, or payment amounts. Django owns all state transitions and calculations. Redis and Celery are configured as extension points; polling is intentionally used for Phase 1.

## Domain boundaries

| Domain | Responsibility |
| --- | --- |
| `accounts` | Staff identity, venue roles, audit log |
| `venues` | Venue, screen, seat, secure QR lifecycle |
| `catalog` | Categories, products, venue offers |
| `orders` | Customer sessions, cart snapshots, orders, state events |
| `payments` | Provider-ready payment records and simulated approval |
| `delivery` | Runner assignment and live seat-map projection |
| `analytics` | Query-backed Phase-1 operational aggregates |

## Trust boundaries

- A QR contains a 256-bit URL-safe token, never a database ID.
- Resolving a QR produces an expiring customer session. Customer cart, checkout, payment, and tracking calls require its `X-Session-Token`.
- Staff APIs require JWT. Querysets are scoped to the user's venue unless the role is `SUPER_ADMIN`.
- Product prices are read from the database and copied into cart and order items. Historical orders do not change with the catalog.
- Order status changes use the transition table in `apps.orders.services`, plus role-specific target restrictions.
- Every transition, payment, delivery assignment, QR rotation, and catalog change produces an audit record.

## Order lifecycle

```text
PENDING -> CONFIRMED -> PREPARING -> READY -> OUT_FOR_DELIVERY -> DELIVERED
    |
    +-> CANCELLED
```

`PENDING -> CONFIRMED` is owned by successful payment. Kitchen staff may set `PREPARING` and `READY`; delivery staff may set `OUT_FOR_DELIVERY` and `DELIVERED`. Managers and super admins can operate the full valid lifecycle but cannot skip states.

## Extension points

- Replace `payments/simulate` with a provider adapter and verified webhook handler.
- Add Celery tasks for session expiry, notifications, and periodic analytics aggregation.
- Replace customer/staff polling with Django Channels or a managed event service.
- Move product images to object storage while preserving the URL-backed API contract.
- Add venue-specific taxes and inventory as separate pricing/inventory services rather than expanding the order model.
