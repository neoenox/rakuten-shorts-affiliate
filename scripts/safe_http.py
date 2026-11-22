"""Safe outbound HTTP: resolve public IPs, pin sockets, and validate each redirect."""
from dataclasses import dataclass
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import NewConnectionError


class SafeFetchError(requests.RequestException):
    """Unsafe or rejected outbound request."""


def validate_url(url):
    try:
        parsed = urlsplit(str(url))
        port = parsed.port
    except ValueError as exc:
        raise SafeFetchError("invalid URL") from exc
    if parsed.scheme not in ("http", "https"):
        raise SafeFetchError("only HTTP(S) is allowed")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise SafeFetchError("URL host or credentials are invalid")
    host = parsed.hostname.lower().rstrip(".")
    if not host or host in ("localhost",) or host.endswith((".localhost", ".local", ".internal")):
        raise SafeFetchError("local hostnames are not allowed")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise SafeFetchError("IP-literal URLs are not allowed")
    allowed_port = 443 if parsed.scheme == "https" else 80
    if port not in (None, allowed_port):
        raise SafeFetchError("non-default ports are not allowed")
    return parsed


def resolve_public_ip(host, port):
    try:
        records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SafeFetchError("DNS resolution failed") from exc
    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise SafeFetchError("DNS returned no addresses")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise SafeFetchError("DNS returned an invalid address") from exc
        if not ip.is_global:
            raise SafeFetchError("DNS resolved to a non-public address")
    return addresses[0]


class _PinnedMixin:
    def __init__(self, *args, pinned_ip=None, **kwargs):
        self.pinned_ip = pinned_ip
        super().__init__(*args, **kwargs)

    def _new_conn(self):
        if not self.pinned_ip:
            raise NewConnectionError(self, "missing pinned IP")
        try:
            sock = socket.create_connection(
                (self.pinned_ip, self.port), self.timeout, self.source_address
            )
            for option, value in self.socket_options or ():
                sock.setsockopt(*option, value)
            return sock
        except OSError as exc:
            raise NewConnectionError(self, str(exc)) from exc


class _PinnedHTTPConnection(_PinnedMixin, HTTPConnection):
    pass


class _PinnedHTTPSConnection(_PinnedMixin, HTTPSConnection):
    pass


class _PinnedPoolMixin:
    def __init__(self, host, port, pinned_ip, **kwargs):
        super().__init__(host, port, **kwargs)
        self.conn_kw["pinned_ip"] = pinned_ip


class _PinnedHTTPPool(_PinnedPoolMixin, HTTPConnectionPool):
    ConnectionCls = _PinnedHTTPConnection


class _PinnedHTTPSPool(_PinnedPoolMixin, HTTPSConnectionPool):
    ConnectionCls = _PinnedHTTPSConnection


class _PinnedAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, pinned_ip, **kwargs):
        self.pinned_ip = pinned_ip
        super().__init__(**kwargs)

    def get_connection(self, url, proxies=None):
        if proxies:
            raise SafeFetchError("proxy use is not allowed")
        parsed = urlsplit(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        pool = _PinnedHTTPSPool if parsed.scheme == "https" else _PinnedHTTPPool
        return pool(
            host=parsed.hostname,
            port=port,
            pinned_ip=self.pinned_ip,
            maxsize=1,
            block=True,
        )


@dataclass
class SafeResponse:
    status_code: int
    url: str
    headers: dict
    content: bytes

    @property
    def text(self):
        content_type = self.headers.get("Content-Type", "")
        charset = "utf-8"
        for part in content_type.split(";"):
            if part.strip().lower().startswith("charset="):
                charset = part.split("=", 1)[1].strip().strip('"') or "utf-8"
        try:
            return self.content.decode(charset, errors="replace")
        except LookupError:
            return self.content.decode("utf-8", errors="replace")


_REDIRECTS = {301, 302, 303, 307, 308}


def safe_get(url, *, headers=None, timeout=25, max_redirects=5, max_bytes=5_000_000):
    """Fetch a public URL without proxy/env settings or unvalidated redirects.

    DNS is resolved before each hop and the selected public IP is pinned for
    the TCP connection. HTTPS certificate validation and SNI still use the
    original hostname.
    """
    current = str(url)
    seen = set()
    for hop in range(max_redirects + 1):
        if current in seen:
            raise SafeFetchError("redirect loop")
        seen.add(current)
        parsed = validate_url(current)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        pinned_ip = resolve_public_ip(parsed.hostname, port)
        session = requests.Session()
        session.trust_env = False
        adapter = _PinnedAdapter(pinned_ip)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        response = None
        try:
            response = session.get(
                current,
                headers=headers,
                allow_redirects=False,
                stream=True,
                timeout=timeout,
                proxies={},
            )
            if response.status_code in _REDIRECTS:
                location = response.headers.get("Location")
                if not location:
                    raise SafeFetchError("redirect has no Location")
                next_url = urljoin(current, location)
                response.close()
                session.close()
                if hop >= max_redirects:
                    raise SafeFetchError("too many redirects")
                current = next_url
                continue
            declared = response.headers.get("Content-Length")
            if declared:
                try:
                    if int(declared) > max_bytes:
                        raise SafeFetchError("response exceeds size limit")
                except ValueError as exc:
                    raise SafeFetchError("invalid Content-Length") from exc
            body = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                if len(body) + len(chunk) > max_bytes:
                    raise SafeFetchError("response exceeds size limit")
                body.extend(chunk)
            return SafeResponse(response.status_code, current, dict(response.headers), bytes(body))
        finally:
            if response is not None:
                response.close()
            session.close()
    raise SafeFetchError("too many redirects")
