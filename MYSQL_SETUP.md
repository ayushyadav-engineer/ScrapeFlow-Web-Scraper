# MySQL 8.4 Setup for SCRAPEFLOW

SCRAPEFLOW uses SQLAlchemy, so it can run against SQLite (default, for local
development) or MySQL 8.4 (recommended for production) with no code changes —
only the `DATABASE_URL` environment variable changes. This guide covers MySQL.

The driver used is **PyMySQL** (pure-Python, no system MySQL client library
required). It is already pinned in `requirements.txt`.

---

## 1. Install / verify MySQL 8.4

**MySQL Command Line Client 8.4**

```bash
mysql --version
# mysql  Ver 8.4.x for Linux on x86_64
```

If it is not installed, follow the official MySQL 8.4 installation guide for
your OS: https://dev.mysql.com/doc/refman/8.4/en/installing.html

**MySQL Workbench 8.0** (optional GUI client)
Download from: https://dev.mysql.com/downloads/workbench/

## 2. Start MySQL

```bash
# Linux (systemd)
sudo systemctl start mysqld
sudo systemctl status mysqld

# macOS (Homebrew)
brew services start mysql
```

## 3. Create the database

Connect as an administrative user:

```bash
mysql -u root -p
```

Then create the database with `utf8mb4` / `utf8mb4_unicode_ci`, which is
required for full Unicode support (emoji, multi-language product titles,
currency symbols, etc.):

```sql
CREATE DATABASE scrapeflow
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

## 4. Create a dedicated application user

**Never use `root` credentials in the application.** Create a least-privilege
user scoped to the `scrapeflow` database only:

```sql
CREATE USER 'scrapeflow_app'@'%' IDENTIFIED BY 'CHANGE_ME_STRONG_PASSWORD';
```

## 5. Grant only required permissions

The application only needs standard DML/DDL on its own database — it does not
need `GRANT OPTION`, `SUPER`, `FILE`, or any administrative privilege:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON scrapeflow.* TO 'scrapeflow_app'@'%';
FLUSH PRIVILEGES;
```

If your application server and MySQL server run on the same host, prefer
`'scrapeflow_app'@'localhost'` (or the specific application host) over `'%'`
to further restrict network exposure.

## 6. Configure `DATABASE_URL`

In your `.env` (never commit this file):

```
DATABASE_URL=mysql+pymysql://scrapeflow_app:CHANGE_ME_STRONG_PASSWORD@127.0.0.1:3306/scrapeflow?charset=utf8mb4
```

For Docker Compose, point `DATABASE_URL` at the `mysql` (or equivalent)
service hostname instead of `127.0.0.1`, and keep the password in the host
environment / a secrets manager — never hardcode it in `docker-compose.yml`.

## 7. Initialize / migrate tables

Tables are created automatically the first time the app starts, using the
existing SQLAlchemy models (`app/models.py`) — no separate migration tool is
required for a fresh database:

```bash
python run.py
# or
flask --app run run
```

SQLAlchemy's `Base.metadata.create_all()` (in `app/extensions.py`) creates any
tables that do not yet exist. It does **not** alter existing tables, so if you
later change a model's columns you will need a migration tool (e.g. Alembic)
or manual `ALTER TABLE` statements — this is unchanged from the existing
architecture and is out of scope for this initial MySQL setup.

## 8. Verify the connection

```bash
mysql -u scrapeflow_app -p -h 127.0.0.1 scrapeflow -e "SHOW TABLES;"
```

Expected tables: `users`, `scrape_jobs`, `products`.

You can also verify from the application itself:

```bash
curl http://127.0.0.1:5000/health
# {"status": "ok"}
```

## 9. Backup procedure

**Logical backup (recommended for most cases):**

```bash
mysqldump -u scrapeflow_app -p \
  --single-transaction \
  --routines --triggers \
  scrapeflow > scrapeflow_backup_$(date +%Y%m%d_%H%M%S).sql
```

**Restore:**

```bash
mysql -u scrapeflow_app -p scrapeflow < scrapeflow_backup_YYYYMMDD_HHMMSS.sql
```

Store backups encrypted, off-host, and test restores periodically. Never
commit backup files (containing password hashes and user data) to source
control — they are covered by `.gitignore`'s `*.sql`/`*.db` rules; verify this
before adding any backup automation.

---

## Migrating existing SQLite data to MySQL

If you already have data in `scrapeflow.db` (SQLite) that you need to keep:

1. **Do not delete the SQLite file.** Back it up first:
   ```bash
   cp scrapeflow.db scrapeflow.db.backup
   ```
2. Export the SQLite data to portable SQL, then adapt it for MySQL (SQLite and
   MySQL have different SQL dialects for `AUTOINCREMENT`, boolean types, and
   quoting — a direct `.dump` will not import cleanly):
   ```bash
   sqlite3 scrapeflow.db .dump > sqlite_dump.sql
   ```
3. For a small dataset, the simplest reliable path is a one-off Python script
   using the existing SQLAlchemy models: open a session against the SQLite
   `DATABASE_URL`, read all `User`, `ScrapeJob`, and `Product` rows, then open
   a second session against the MySQL `DATABASE_URL` (after completing steps
   1–6 above) and insert them. This reuses the existing models and avoids
   hand-translating SQL dialects. Run it once, verify row counts match on both
   sides, then only decommission the SQLite file once MySQL is confirmed
   correct and backed up.
4. Never point the application at MySQL and delete the SQLite file in the same
   step — keep the SQLite file as a fallback until the migration is verified.
