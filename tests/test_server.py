from contextlib import contextmanager
import http.client
from pathlib import Path
import threading

from server import create_server


@contextmanager
def running_server(root: Path):
    server = create_server(root, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(port, path, *, host=None, method="GET"):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    headers = {"Host": host or f"127.0.0.1:{port}"}
    connection.request(method, path, headers=headers)
    response = connection.getresponse()
    body = response.read()
    result = response.status, dict(response.getheaders()), body
    connection.close()
    return result


def public_root(tmp_path):
    for name in ("index.html", "app.js", "calculator.js", "page-agent-bridge.js", "styles.css"):
        (tmp_path / name).write_text(f"public:{name}", encoding="utf-8")
    return tmp_path


def test_server_serves_only_allowlisted_public_assets(tmp_path):
    root = public_root(tmp_path)
    (root / ".env").write_text("SECRET=value", encoding="utf-8")
    (root / "config").mkdir()
    (root / "config" / "system_prompt.txt").write_text("private", encoding="utf-8")

    with running_server(root) as port:
        status, headers, body = request(port, "/")
        assert status == 200
        assert body == b"public:index.html"
        assert headers["Cache-Control"] == "no-store"
        assert "default-src 'self'" in headers["Content-Security-Policy"]
        assert headers["X-Content-Type-Options"] == "nosniff"

        for private_path in ("/.env", "/.git/config", "/config/system_prompt.txt", "/../.env"):
            assert request(port, private_path)[0] == 404


def test_server_rejects_untrusted_host_and_supports_head(tmp_path):
    with running_server(public_root(tmp_path)) as port:
        assert request(port, "/", host="attacker.example")[0] == 421
        status, _, body = request(port, "/app.js?version=1", method="HEAD")
        assert status == 200
        assert body == b""
