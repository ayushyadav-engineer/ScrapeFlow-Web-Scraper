from __future__ import annotations

from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import declarative_base, sessionmaker

login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

Base = declarative_base()
_engine = None
SessionLocal = None


def init_db(database_url: str):
    global _engine, SessionLocal

    if database_url.startswith("sqlite:///"):
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "future": True,
        }
        if database_url in {"sqlite:///:memory:", "sqlite://"}:
            engine_kwargs["poolclass"] = StaticPool
        _engine = create_engine(database_url, **engine_kwargs)
    elif database_url.startswith(("mysql+pymysql://", "mysql://")):
        # utf8mb4 is required for full Unicode support (emoji, etc.) in MySQL 8.4.
        # Setting it here guarantees correct behavior even if the DATABASE_URL
        # does not include ?charset=utf8mb4 explicitly.
        _engine = create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args={"charset": "utf8mb4"},
        )
    else:
        _engine = create_engine(database_url, future=True, pool_pre_ping=True)

    SessionLocal = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    # Import models before create_all(). SQLAlchemy only creates tables that
    # have already been registered in Base.metadata. The previous startup
    # order initialized the engine before importing models, leaving a fresh
    # SQLite database with no tables (for example, no ``users`` table).
    from . import models  # noqa: F401
    Base.metadata.create_all(_engine)


def get_engine():
    return _engine
