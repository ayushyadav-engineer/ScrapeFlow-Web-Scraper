# ScrapeFlow

A premium Charcoal/Gold Flask scraping SaaS with authentication, secure product extraction, CSV/Excel exports, strict validation, CSRF, configurable rate limiting, exponential login backoff, SSRF protection, security headers, audit/error logging, and user-level data isolation.

## What is included

- Flask 3.1.x + SQLAlchemy 2.x
- Login/register (with server-validated Confirm Password)/logout
- Argon2 password hashing
- SQLite (dev) and MySQL 8.4 (production) via the same SQLAlchemy models — see `MYSQL_SETUP.md`
- CSRF protection for forms and API POSTs
- Configurable Flask-Limiter limits
- Per-IP + per-user limits
- Exponential login backoff (no hard lockout)
- Strict Pydantic request schemas
- SSRF validation for HTTP/HTTPS URLs
- Private/reserved/loopback/link-local/multicast blocking
- NAT64-aware SSRF validation
- Redirect re-validation
- Request/response/page/item scraper limits
- JSON-LD + HTML product extraction
- Price, currency, availability, rating, category, image URL
- User-isolated product and scrape records
- CSV and XLSX exports
- No file-upload feature: therefore no upload-to-webroot/executable-upload attack surface
- Generic user-facing error pages + detailed server logs
- CSP, HSTS in production, XFO, nosniff, Referrer-Policy, Permissions-Policy
- Request IDs
- Responsive glassmorphism UI
- `pip-audit` included for dependency auditing

## Important security note

No software can honestly be called literally "hackproof". This project is designed as a hardened baseline and includes defense-in-depth controls. Production deployment still needs HTTPS, secure infrastructure, secret management, patching, monitoring, and a current dependency scan.

## Setup — Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
Copy-Item .env.example .env
```

Generate a secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put that value into `.env` as `SECRET_KEY=...`.

Install:

```powershell
pip install -r requirements.txt
```

Run tests:

```powershell
pytest -v
```

Run dependency audit:

```powershell
pip-audit -r requirements.txt
```

For the current installed environment:

```powershell
pip-audit
```

Start:

```powershell
python run.py
```

Open:

```text
http://127.0.0.1:5000/auth/register
```

## Production

Set:

```text
FLASK_ENV=production
SECRET_KEY=<strong secret>
DATABASE_URL=<production database URL>
RATELIMIT_STORAGE_URI=redis://redis:6379/0
```

Serve with a production WSGI server and HTTPS. Example:

```powershell
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
```

## API

Authenticated endpoints:

```text
GET  /api/csrf-token
GET  /api/products
POST /api/scrape
GET  /api/scrape/jobs
GET  /api/analytics
GET  /api/export/csv
GET  /api/export/excel
```

For API POST requests, first obtain a CSRF token from `/api/csrf-token` in the same authenticated session and send it as `X-CSRFToken`.

## Security verification checklist

1. `pytest -v`
2. `pip-audit`
3. Confirm `.env` is ignored by Git.
4. Search source for accidental secrets before pushing.
5. Test `/history/` while logged out.
6. Test private URLs such as `http://127.0.0.1/` and `http://169.254.169.254/`.
7. Test invalid page counts and oversized URL strings.
8. Trigger repeated failed logins and observe increasing delay plus 429 limits.
9. Verify one account cannot access another account's records.
10. Test CSV/XLSX exports.

## Security hardening

ScrapeFlow includes configurable endpoint rate limits, authentication backoff, strict request validation, CSRF protection, SSRF protection, request-size limits, backend scraper limits, secure session cookies, security headers, audit logging, generic error handling, secret scanning, dependency auditing, spreadsheet formula-injection protection, and an upload-safety gate for future upload features.

Run the local security checks with:

```bash
python tools/scan_secrets.py
python tools/scan_uploads.py
pytest -v
pip-audit -r requirements.txt --strict
```

## Local database initialization

On startup, SCRAPEFLOW registers its SQLAlchemy models before calling
`Base.metadata.create_all()`. A fresh local SQLite database is therefore
initialized automatically. No manual migration is required for a new local
installation.

## MySQL 8.4 (production database)

For production, point `DATABASE_URL` at MySQL 8.4 instead of SQLite — no code
changes are required, since both use the same SQLAlchemy models:

```
DATABASE_URL=mysql+pymysql://scrapeflow_app:CHANGE_ME@127.0.0.1:3306/scrapeflow?charset=utf8mb4
```

See `MYSQL_SETUP.md` for full instructions: installing MySQL 8.4, creating the
`scrapeflow` database with `utf8mb4`/`utf8mb4_unicode_ci`, creating a
least-privilege application user, initializing tables, verifying the
connection, backups, and migrating existing SQLite data.
