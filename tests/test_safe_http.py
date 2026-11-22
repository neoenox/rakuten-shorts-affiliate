import socket

import pytest

import safe_http


class FakeResponse:
    def __init__(self, status_code, *, headers=None, content=b"", url=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self.url = url
        self.closed = False

    def iter_content(self, chunk_size=65536):
        yield self.content

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, responses, record):
        self.responses = responses
        self.record = record
        self.adapters = {}
        self.trust_env = True

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter

    def get(self, url, **kwargs):
        self.record.append((url, kwargs))
        adapter = self.adapters["https://" if url.startswith("https://") else "http://"]
        pool = adapter.get_connection(url, proxies={})
        assert pool.conn_kw["pinned_ip"] == "8.8.8.8"
        assert pool.host == safe_http.urlsplit(url).hostname
        return self.responses.pop(0)

    def close(self):
        pass


def public_dns(host, port, *args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("8.8.8.8", port))]


def test_rejects_local_hosts_ip_literals_credentials_and_non_default_ports():
    for url in (
        "http://localhost/",
        "https://127.0.0.1/",
        "https://[::1]/",
        "https://user:pass@example.com/",
        "https://example.com:8443/",
        "http://service.local/",
    ):
        with pytest.raises(safe_http.SafeFetchError):
            safe_http.validate_url(url)


def test_resolve_public_ip_rejects_private_addresses(monkeypatch):
    monkeypatch.setattr(
        safe_http.socket,
        "getaddrinfo",
        lambda host, port, *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.2", port))
        ],
    )
    with pytest.raises(safe_http.SafeFetchError, match="non-public"):
        safe_http.resolve_public_ip("evil.example", 443)


def test_redirect_to_private_literal_is_rejected_before_second_request(monkeypatch):
    monkeypatch.setattr(safe_http.socket, "getaddrinfo", public_dns)
    record = []
    sessions = []

    def session_factory():
        session = FakeSession(
            [FakeResponse(302, headers={"Location": "http://127.0.0.1/admin"})],
            record,
        )
        sessions.append(session)
        return session

    monkeypatch.setattr(safe_http.requests, "Session", session_factory)
    with pytest.raises(safe_http.SafeFetchError, match="IP-literal"):
        safe_http.safe_get("https://example.com/start")
    assert len(record) == 1


def test_redirect_destination_dns_is_checked_and_pinned(monkeypatch):
    record = []
    calls = 0

    def dns(host, port, *args, **kwargs):
        if host == "evil.example":
            return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.2", port))]
        return public_dns(host, port)

    monkeypatch.setattr(safe_http.socket, "getaddrinfo", dns)

    def session_factory():
        return FakeSession([FakeResponse(302, headers={"Location": "https://evil.example/"})], record)

    monkeypatch.setattr(safe_http.requests, "Session", session_factory)
    with pytest.raises(safe_http.SafeFetchError, match="non-public"):
        safe_http.safe_get("https://example.com/start")
    assert len(record) == 1


def test_public_redirect_chain_returns_final_response(monkeypatch):
    monkeypatch.setattr(safe_http.socket, "getaddrinfo", public_dns)
    record = []
    responses = [
        FakeResponse(302, headers={"Location": "https://cdn.example/path"}),
        FakeResponse(200, headers={"Content-Type": "text/plain; charset=utf-8"}, content=b"ok"),
    ]

    def session_factory():
        return FakeSession([responses.pop(0)], record)

    monkeypatch.setattr(safe_http.requests, "Session", session_factory)
    result = safe_http.safe_get("https://example.com/start")
    assert result.status_code == 200
    assert result.url == "https://cdn.example/path"
    assert result.text == "ok"
    assert len(record) == 2
    assert all(call[1]["allow_redirects"] is False for call in record)
    assert all(call[1]["proxies"] == {} for call in record)


def test_response_size_limit(monkeypatch):
    monkeypatch.setattr(safe_http.socket, "getaddrinfo", public_dns)
    record = []

    def session_factory():
        return FakeSession(
            [FakeResponse(200, headers={"Content-Length": "11"}, content=b"12345678901")],
            record,
        )

    monkeypatch.setattr(safe_http.requests, "Session", session_factory)
    with pytest.raises(safe_http.SafeFetchError, match="size limit"):
        safe_http.safe_get("https://example.com/", max_bytes=10)
