\
import os
os.environ["SECRET_KEY"] = "test-secret-key-" + "x" * 40
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["RATELIMIT_STORAGE_URI"] = "memory://"

from app import create_app
from app.security.ssrf import SSRFBlocked, validate_url


def test_ssrf_blocks_private():
    for url in ("http://127.0.0.1/", "http://169.254.169.254/", "http://192.168.1.1/"):
        try:
            validate_url(url)
            assert False, url
        except SSRFBlocked:
            pass


def test_public_url_shape():
    assert validate_url("https://example.com/").startswith("https://example.com")


def test_app_health():
    app = create_app()
    client = app.test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_unauthenticated_history_redirects():
    app = create_app()
    client = app.test_client()
    r = client.get("/history/", follow_redirects=False)
    assert r.status_code in (302, 303)


def _get_csrf(client, path):
    page = client.get(path)
    html = page.get_data(as_text=True)
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    return html[start:end]


def test_register_confirm_password_mismatch_rejected():
    app = create_app()
    client = app.test_client()
    token = _get_csrf(client, "/auth/register")
    r = client.post("/auth/register", data={
        "csrf_token": token,
        "email": "mismatch@example.com",
        "password": "GoodPassw0rd!123",
        "confirm_password": "DifferentPassw0rd!123",
    })
    assert r.status_code == 400

    from sqlalchemy import select
    import app.extensions as extensions
    from app.models import User
    db = extensions.SessionLocal()
    try:
        assert db.scalar(select(User).where(User.email == "mismatch@example.com")) is None
    finally:
        db.close()


def test_register_confirm_password_match_succeeds():
    app = create_app()
    client = app.test_client()
    token = _get_csrf(client, "/auth/register")
    r = client.post("/auth/register", data={
        "csrf_token": token,
        "email": "match@example.com",
        "password": "GoodPassw0rd!123",
        "confirm_password": "GoodPassw0rd!123",
    }, follow_redirects=False)
    assert r.status_code in (302, 303)

    from sqlalchemy import select
    import app.extensions as extensions
    from app.models import User
    db = extensions.SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == "match@example.com"))
        assert user is not None
        # Password must be hashed, never stored in plaintext.
        assert user.password_hash != "GoodPassw0rd!123"
        assert user.check_password("GoodPassw0rd!123")
    finally:
        db.close()


def test_register_missing_confirm_password_rejected():
    app = create_app()
    client = app.test_client()
    token = _get_csrf(client, "/auth/register")
    r = client.post("/auth/register", data={
        "csrf_token": token,
        "email": "noconfirm@example.com",
        "password": "GoodPassw0rd!123",
    })
    assert r.status_code == 400


def test_config_not_exposed_to_templates():
    app = create_app()
    client = app.test_client()
    token = _get_csrf(client, "/auth/register")
    html = client.get("/auth/register").get_data(as_text=True)
    assert "SECRET_KEY" not in html
    assert "DATABASE_URL" not in html
