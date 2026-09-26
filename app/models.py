from __future__ import annotations

from datetime import datetime, timezone

from argon2 import PasswordHasher
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import Base

_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    jobs: Mapped[list["ScrapeJob"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        self.password_hash = _hasher.hash(password)

    def check_password(self, password: str) -> bool:
        try:
            return _hasher.verify(self.password_hash, password)
        except Exception:
            return False

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    items_scraped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="jobs")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("user_id", "product_url", name="uq_user_product_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="", nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    availability: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    product_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    image_url: Mapped[str] = mapped_column(String(2048), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="products")
