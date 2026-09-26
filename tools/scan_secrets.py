from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {".git", ".venv", ".venv-audit", "__pycache__", ".pytest_cache", "instance", "storage"}
TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".html", ".jinja", ".jinja2", ".css", ".json", ".toml",
    ".yaml", ".yml", ".ini", ".cfg", ".conf", ".txt", ".md", ".env", ".example",
}

PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|DSA|PRIVATE) KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9_]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("Bearer token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("quoted secret-like assignment", re.compile(
        r"(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token|client[_-]?secret|password)"
        r"\s*(?:=|:)\s*['\"][^'\"]{16,}['\"]"
    )),
    ("unquoted secret-like environment assignment", re.compile(
        r"(?im)^(?:api[_-]?key|secret[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*=\s*(?!CHANGE_ME(?:_|$))[^\s#]{16,}$"
    )),
]


def tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, check=True,
            capture_output=True, text=False,
        )
        names = [Path(x.decode("utf-8")) for x in result.stdout.split(b"\0") if x]
        return [ROOT / name for name in names]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [
            p for p in ROOT.rglob("*")
            if p.is_file() and not any(part in EXCLUDE_DIRS for part in p.parts)
        ]


hits: list[tuple[str, str]] = []
for path in tracked_files():
    if not path.is_file() or any(part in EXCLUDE_DIRS for part in path.parts):
        continue
    if path.name in {".env", ".env.local", ".env.production"}:
        hits.append((str(path.relative_to(ROOT)), "environment file must not be tracked"))
        continue
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "requirements.txt"}:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for label, pattern in PATTERNS:
        if pattern.search(text):
            hits.append((str(path.relative_to(ROOT)), label))

# Front-end must never contain server-only secrets or credential fields.
for root in (ROOT / "app" / "templates", ROOT / "app" / "static"):
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for needle in ("SECRET_KEY", "DATABASE_URL", "password_hash", "DATABASE_PASSWORD"):
            if needle in text:
                hits.append((str(path.relative_to(ROOT)), f"frontend contains {needle}"))

if hits:
    print("Potential secret exposure found:")
    for path, label in sorted(set(hits)):
        print(f" - {path}: {label}")
    raise SystemExit(1)

print("Secret scan passed: no obvious credentials, tokens, private keys, or server-only secrets found.")
