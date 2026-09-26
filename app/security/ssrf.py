from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit

_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_PORTS = {80, 443}
_NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")


class SSRFBlocked(ValueError):
    pass


def _is_bad_ip(ip: ipaddress._BaseAddress) -> bool:
    if ip in _NAT64_PREFIX:
        mapped = ipaddress.ip_address(int(ip) & 0xFFFFFFFF)
        return _is_bad_ip(mapped)

    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )


def _resolve_public(host: str, port: int):
    try:
        infos = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except (OSError, UnicodeError) as exc:
        raise SSRFBlocked("Host could not be resolved") from exc

    addresses = {ipaddress.ip_address(item[4][0]) for item in infos}
    if not addresses:
        raise SSRFBlocked("Host could not be resolved")

    for ip in addresses:
        if _is_bad_ip(ip):
            raise SSRFBlocked("Private or reserved network target is not allowed")

    return addresses


def validate_url(raw: str) -> str:
    if not isinstance(raw, str):
        raise SSRFBlocked("Invalid URL")

    raw = raw.strip()
    if len(raw) > 2048:
        raise SSRFBlocked("URL is too long")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in raw):
        raise SSRFBlocked("Invalid URL characters")

    try:
        parsed = urlsplit(raw)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
    except (ValueError, UnicodeError) as exc:
        raise SSRFBlocked("Invalid URL") from exc

    if scheme not in _ALLOWED_SCHEMES:
        raise SSRFBlocked("Only HTTP and HTTPS URLs are allowed")
    if not hostname:
        raise SSRFBlocked("URL host is required")
    if parsed.username or parsed.password:
        raise SSRFBlocked("Credentials in URLs are not allowed")

    if port is None:
        port = 443 if scheme == "https" else 80
    if port not in _ALLOWED_PORTS:
        raise SSRFBlocked("Non-standard ports are not allowed")
    if scheme == "https" and port != 443:
        raise SSRFBlocked("Invalid HTTPS port")
    if scheme == "http" and port != 80:
        raise SSRFBlocked("Invalid HTTP port")

    host = hostname.rstrip(".").lower()
    if not host or host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise SSRFBlocked("Localhost is not allowed")

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise SSRFBlocked("Invalid hostname") from exc

    try:
        ip = ipaddress.ip_address(ascii_host)
        if _is_bad_ip(ip):
            raise SSRFBlocked("Private or reserved network target is not allowed")
    except ValueError:
        _resolve_public(ascii_host, port)

    netloc = ascii_host
    if ":" in ascii_host and not ascii_host.startswith("["):
        netloc = f"[{ascii_host}]"
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"

    # Remove fragments and credentials. Fragments are never sent to servers.
    return urlunsplit((scheme, netloc, parsed.path or "/", parsed.query, ""))
