# Phase-1 API Surface

Base URL: `http://localhost:8000/api/v1`

## Customer endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/sessions/resolve/` | Resolve a seat QR and create an expiring session |
| `GET` | `/sessions/current/` | Return the seat for `X-Session-Token` |
| `GET` | `/categories/?venue=CMX-CAL` | Public active categories |
| `GET` | `/products/?venue=CMX-CAL` | Public available products |
| `GET` | `/cart/current/` | Get the session's active cart |
| `POST` | `/cart/items/` | Set quantity for a product |
| `DELETE` | `/cart/items/{item_id}/` | Remove a cart line |
| `POST` | `/cart/checkout/` | Create an immutable pending order snapshot |
| `POST` | `/payments/simulate/` | Approve the server-calculated amount |
| `GET` | `/orders/{public_id}/track/` | Track a session-owned order |

## Staff and admin endpoints

JWT is obtained from `POST /auth/token/` and sent as `Authorization: Bearer <token>`.

| Endpoint | Capability |
| --- | --- |
| `/orders/board/` | Active kitchen/delivery board |
| `/orders/{id}/transition/` | Validated role-aware status transition |
| `/delivery/seat-map/?screen={id}` | Live order status by physical seat |
| `/delivery/` | Runner assignments |
| `/analytics/overview/` | Revenue, order, hourly, and product summaries |
| `/venues/`, `/screens/`, `/seats/` | Venue structure management |
| `/qr/{seat_id}/image/` | Download an individual PNG QR |
| `/qr/print-sheet/?screen={id}` | Download printable screen QR sheet PDF |
| `/categories/`, `/products/`, `/offers/` | Catalog management |
| `/staff/`, `/audit-logs/` | Staff and audit management |

