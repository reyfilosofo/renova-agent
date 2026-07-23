from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


HOST = "127.0.0.1"
PORT = 8000

PUBLIC_PATHS = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app.js": "app.js",
    "/calculator.js": "calculator.js",
    "/page-agent-bridge.js": "page-agent-bridge.js",
    "/styles.css": "styles.css",
}

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "script-src 'self' https://cdn.jsdelivr.net",
        "connect-src 'self' https://page-ag-testing-ohftxirgbn.cn-shanghai.fcapp.run",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self' data:",
        "worker-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
        "frame-ancestors 'none'",
    )
)


class SafeStaticHandler(SimpleHTTPRequestHandler):
    """Serve only the V-OS public assets, never the repository working tree."""

    def _host_is_allowed(self) -> bool:
        raw_host = self.headers.get("Host", "")
        try:
            hostname = urlsplit(f"//{raw_host}").hostname
        except ValueError:
            return False
        return bool(hostname and hostname.casefold() in ALLOWED_HOSTS)

    def _public_path(self) -> str | None:
        request_path = unquote(urlsplit(self.path).path)
        return PUBLIC_PATHS.get(request_path)

    def _serve_public(self, *, head_only: bool = False) -> None:
        if not self._host_is_allowed():
            self.send_error(421, "Untrusted Host header")
            return

        public_path = self._public_path()
        if public_path is None:
            self.send_error(404, "Public asset not found")
            return

        original_path = self.path
        self.path = f"/{public_path}"
        try:
            if head_only:
                super().do_HEAD()
            else:
                super().do_GET()
        finally:
            self.path = original_path

    def do_GET(self) -> None:
        self._serve_public()

    def do_HEAD(self) -> None:
        self._serve_public(head_only=True)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def create_server(root: Path, host: str = HOST, port: int = PORT) -> ThreadingHTTPServer:
    handler = partial(SafeStaticHandler, directory=str(root.resolve()))
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    root = Path(__file__).resolve().parent
    server = create_server(root)

    print(f"Serving SERESARTE V-OS public assets from {root}")
    print(f"Open http://{HOST}:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
