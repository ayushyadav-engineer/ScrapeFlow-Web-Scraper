from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictInt, StrictStr, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )


class RegisterInput(StrictModel):
    email: EmailStr
    password: StrictStr = Field(min_length=12, max_length=128)
    confirm_password: StrictStr = Field(min_length=12, max_length=128)

    @field_validator("password", "confirm_password")
    @classmethod
    def password_strength(cls, value: str):
        if any(ord(ch) < 32 for ch in value):
            raise ValueError("Password contains invalid control characters")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain a number")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("Password must contain a symbol")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        # Server-side is authoritative: confirm_password must never be trusted
        # from the client without re-checking it matches password here.
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password must match")
        return self


class LoginInput(StrictModel):
    email: EmailStr
    password: StrictStr = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def password_characters(cls, value: str):
        if any(ord(ch) < 32 for ch in value):
            raise ValueError("Password contains invalid control characters")
        return value


class ScrapeInput(StrictModel):
    url: StrictStr = Field(min_length=8, max_length=2048)
    pages: StrictInt = Field(ge=1)

    @field_validator("url")
    @classmethod
    def url_chars(cls, value: str):
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise ValueError("Invalid URL characters")
        return value


class ExportFormat(StrictModel):
    fmt: Literal["csv", "excel"]


class ProductSearchInput(StrictModel):
    q: StrictStr = Field(default="", max_length=100)
    page: StrictInt = Field(default=1, ge=1, le=1000)

    @field_validator("q")
    @classmethod
    def query_characters(cls, value: str):
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise ValueError("Invalid query characters")
        return value
