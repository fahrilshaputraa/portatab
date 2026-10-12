# PortaTap — Deployment

Practical runbook for putting PortaTap on a server. It assumes the approved stack
(PostgreSQL + Django behind a WSGI server) and no optional infrastructure: the MVP
needs no Redis, Celery, WebSocket server or object storage.

Read this together with `docs/PRD.md` §27 (open decisions that must be settled
before real traffic) and `AGENTS.md` §15.

## 1. What must exist before the first deploy

| Item | Where it comes from |
| --- | --- |
| PostgreSQL database + role | Provisioned by your host |
| `DJANGO_SECRET_KEY` | Generated once, stored in the secret manager |
| `DJANGO_ALLOWED_HOSTS` | The real hostnames |
| Midtrans server/client keys | The provider dashboard |
| HTTPS termination | Load balancer or Nginx |
| SMTP credentials | `EMAIL_URL` (invitations and notifications) |

Production settings live in `config/settings/prod.py`. They **fail fast** on a
missing secret key or an empty `ALLOWED_HOSTS`, so a misconfigured deploy stops
instead of silently serving with development defaults.

## 2. Environment variables

```ini
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<50+ random characters>
DJANGO_ALLOWED_HOSTS=portatap.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://portatap.example.com
DATABASE_URL=postgres://user:password@host:5432/portatap
EMAIL_URL=smtp://user:password@smtp.example.com:587
DEFAULT_FROM_EMAIL=PortaTap <no-reply@portatap.example.com>

MIDTRANS_SERVER_KEY=<server key>
MIDTRANS_CLIENT_KEY=<client key>
MIDTRANS_IS_PRODUCTION=True

# Business policy — review before enabling real traffic
REFUND_CASHIER_MAX_AMOUNT=100000
SUBSCRIPTION_TRIAL_DAYS=14
PAYMENT_EXPIRY_MINUTES=15
STOCK_RESERVATION_TTL_MINUTES=30
ORDER_WARNING_SECONDS=180
ORDER_LATE_SECONDS=300
```

Never commit the real `.env`. `SECRET_KEY` and the Midtrans server key are
server-only; the client key may be exposed to the browser.

## 3. Build and release

```bash
uv sync --frozen                     # exact dependency set from uv.lock
npm ci --include=dev                 # Tailwind CLI (skip if npm omits dev deps)
npm run build:css                    # writes static/css/app.css
uv run python manage.py migrate      # schema changes
uv run python manage.py collectstatic --noinput   # hashed static manifest
```

`static/css/app.css` is a **build artifact** and is gitignored, so the deploy must
run `npm run build:css` before `collectstatic`. WhiteNoise serves the hashed
manifest; failing to build the CSS leaves the site unstyled.

Run the service with a production WSGI server — never `runserver`:

```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile -
```

Put Nginx (or the host's load balancer) in front for TLS. Forward
`X-Forwarded-Proto`; `prod.py` already trusts it via `SECURE_PROXY_SSL_HEADER`.

## 4. Scheduled jobs

Two commands must run on a schedule. They are plain management commands, so cron
(or any scheduler) is enough — no Celery required for the MVP.

```cron
# Every minute: 3-minute cashier warning, 5-minute late flag
* * * * * cd /srv/portatap && uv run python manage.py evaluate_orders >> /var/log/portatap/scheduler.log 2>&1

# Every 10 minutes: reconcile digital payments whose webhook never arrived
*/10 * * * * cd /srv/portatap && uv run python manage.py reconcile_payments >> /var/log/portatap/scheduler.log 2>&1
```

Both are idempotent: re-running them never produces duplicate warnings,
duplicate stock effects or downgraded payments.

Nightly, verify a backup actually restores:

```cron
30 2 * * * pg_dump --format=custom --file=/backups/portatap-$(date +\%F).dump "$DATABASE_URL"
```

## 5. Backups and recovery

1. **Back up** with `pg_dump --format=custom` on a schedule, plus uploaded media
   if object storage is not used.
2. **Store** backups off the application server.
3. **Restore drill** into a scratch database at least monthly:
   `pg_restore --clean --if-exists --dbname="$SCRATCH_URL" backup.dump`, then run
   `manage.py migrate` and check the admin loads.
4. Payment and inventory reconciliation after a restore: run
   `manage.py reconcile_payments`, then compare `payments` against the provider
   dashboard before accepting orders again.
5. Define an RPO/RTO target. PRD §27 lists this as an open decision; do not go to
   production without one.

## 6. Monitoring

Logging is structured to stdout (`LOGGING` in `base.py`), so the host's log
collector is the place to look. Watch at least:

- Application errors (`django.request`, level WARNING and above).
- `/manage/console/health/` for stuck payments, unprocessed webhooks, refunds
  needing follow-up, past-due subscriptions and completed-but-unpaid orders.
- Scheduler exit status — a silently failing `evaluate_orders` means late orders
  are never flagged.
- Database disk, connections and slow queries.

Health endpoint: the console requires a platform-admin login, so wire an
authenticated uptime check rather than exposing it publicly.

## 7. Release checklist

- [ ] `uv run python manage.py check --deploy` is clean.
- [ ] `uv run pytest` passes.
- [ ] `npm run build:css` ran and `collectstatic` succeeded.
- [ ] `migrate` applied with no pending migrations (`makemigrations --check`).
- [ ] `DEBUG` is off and `ALLOWED_HOSTS` lists only real hostnames.
- [ ] A platform-admin account exists (`manage.py grant_platform_admin <email>`).
- [ ] Scheduled jobs are installed and have run at least once.
- [ ] A backup has been taken and restore-tested.
- [ ] Provider webhook URL points at `/webhooks/midtrans/` and a real sandbox
      notification was verified end to end.

## 8. Known gaps before unrestricted production

These are honest limitations of the current code, not oversights to discover later:

- **Rate limiting is not implemented.** `docs/AGENTS.md` §15 and
  `docs/API-CONVENTIONS.md` §15 call for it on login, public checkout and
  promotion redemption. Put a limiter at the proxy in the meantime.
- **No load or performance testing** has been run; the pagination, indexes and
  `select_for_update` paths exist but are unmeasured.
- **No error-tracking service** (Sentry or similar) is wired; logs are the only
  signal today.
- **Refund approval thresholds, stock-reservation expiry and subscription grace
  behaviour** are configurable but still need a product decision (PRD §27).
- **Payment provider coverage** is Midtrans only; a second provider needs its own
  adapter behind `apps/payments/providers/`.
