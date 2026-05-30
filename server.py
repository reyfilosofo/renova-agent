from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "localhost"
PORT = 8000


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    root = Path(__file__).resolve().parent
    handler = partial(NoCacheHandler, directory=str(root))
    server = ThreadingHTTPServer((HOST, PORT), handler)

    print(f"Serving SERESARTE V-OS from {root}")
    print(f"Open http://{HOST}:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
