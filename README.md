# Behavioral Risk OS (Kraken Futures BTCUSD MVP)

MVP trading platform with Training/Mastery UX, Guard mode enforcement, StabilityScore v1, and admin policy controls.

## Architecture
- **Frontend:** Next.js + TypeScript + Tailwind + Zustand + React Query
- **Backend:** FastAPI + PostgreSQL + Redis
- **Execution model:** Orders go through backend proxy to Kraken Futures REST v3
- **Auth:** email/password JWT (MVP)
- **Security:** API secrets encrypted at rest (Fernet)

## Repository Tree
- `frontend/` UI (dashboard, order ticket, admin panel)
- `backend/app/api` API contracts and endpoints
- `backend/app/connector` Kraken Futures REST connector
- `backend/app/rules` Guard rules engine + cooldowns
- `backend/app/scoring` StabilityScore v1 service
- `backend/migrations` SQL migrations
- `docker-compose.yml` local stack

## API Contracts
- `POST /v1/events` normalized events
- `GET /v1/users/{id}/score` StabilityScore v1
- `POST /v1/guard/evaluate` evaluate risk escalation action
- Admin:
  - `POST/GET/PUT/DELETE /v1/admin/policies`
  - `POST /v1/admin/assign-policy`
  - `GET /v1/admin/audit-logs`
- Kraken proxy:
  - `GET /v1/kraken/{user_id}/positions`
  - `POST /v1/kraken/{user_id}/order`

## Guard rules implemented (10)
1. Symbol allowlist
2. Max risk-at-stop %
3. Max leverage
4. Strict stop widening block
5. Max adds
6. Add cooldown (default 10 min)
7. Max trades/day
8. Consecutive loss lockout
9. Global cooldown after blocks
10. Rapid side-flip block

## PnL masking behavior
- While position/session is active: hide PnL, ROE, equity delta, return %.
- Reveal only after trade closes or session ends.

## Local Run (Docker)
1. Copy `.env.example` to `.env` and replace every placeholder. Generate a random
   `JWT_SECRET` (at least 32 characters) and a persistent Fernet `ENCRYPTION_KEY`.
2. Start stack:
   ```bash
   docker compose up --build
   ```
3. Frontend: `http://localhost:3000`
4. Backend docs: `http://localhost:8000/docs`

## Demo flow (Kraken demo)
1. Register user: `POST /v1/auth/register`, then log in with `POST /v1/auth/login`.
2. Send the returned token as `Authorization: Bearer <token>` on all other API calls.
3. Save demo key/secret: `POST /v1/credentials` with `environment=demo`.
4. Open `/trade` and place small market order for `PI_XBTUSD`.
5. Attempt blocked action (e.g., set leverage above policy or stop widening flag) and verify 403 + event feed block reason.

Public registration always creates a `trader`. Bootstrap or promote administrators through a
controlled database operation; the public registration endpoint never grants the `admin` role.

## Deploy options
- **Render:** separate services for backend/frontend + managed Postgres + Redis.
- **Fly.io:** one app per service or monorepo with process groups.
- **VPS:** Docker compose on Ubuntu with Nginx reverse proxy + TLS.

## Notes
- Request only Kraken permissions: trading + read (no withdrawals).
- Demo/prod creds are stored separately and selected by environment toggle.
- BTCUSD UI label maps to Kraken symbol `PI_XBTUSD`.
