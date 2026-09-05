"""Serveur local optionnel.

La page index.html est autonome : elle calcule en JavaScript et s'ouvre
directement dans un navigateur (double-clic) ou depuis GitHub Pages.
Ce serveur ne sert qu'a la confort local :  python app.py  ->  http://127.0.0.1:8000

Les routes /api/* restent disponibles et utilisent artillery.py, ce qui permet
de recouper le moteur JavaScript avec l'implementation Python de reference.
"""

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import artillery

HOST = "127.0.0.1"
PORT = 8000
STATIC = Path(__file__).parent

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "Artillerie/1.0"

    def log_message(self, fmt, *args):
        pass  # silence

    def _send(self, code, body, content_type):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, payload):
        self._send(code, json.dumps(payload), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"

        target = (STATIC / path.lstrip("/")).resolve()
        if not str(target).startswith(str(STATIC.resolve())) or not target.is_file():
            self._send(404, "404", "text/plain; charset=utf-8")
            return

        self._send(200, target.read_bytes(), CONTENT_TYPES.get(target.suffix, "application/octet-stream"))

    def do_POST(self):
        route = self.path.split("?", 1)[0]
        if route not in ("/api/solve", "/api/adjust", "/api/project"):
            self._json(404, {"error": "route inconnue"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
            gun = (float(data["gun"]["x"]), float(data["gun"]["y"]))
            scale = float(data.get("meters_per_point") or artillery.METERS_PER_POINT)
            if route == "/api/adjust":
                target = (float(data["target"]["x"]), float(data["target"]["y"]))
                raw = data.get("impacts") or [data["impact"]]
                impacts = [(float(i["x"]), float(i["y"])) for i in raw]
            elif route == "/api/project":
                distance_m = float(data["distance_m"])
                azimuth_deg = float(data["azimuth_deg"])
            else:
                targets = data.get("targets") or []
        except (ValueError, KeyError, TypeError) as exc:
            self._json(400, {"error": f"requete invalide : {exc}"})
            return

        if route == "/api/adjust":
            self._json(200, artillery.adjust(gun, target, impacts, scale))
            return

        if route == "/api/project":
            self._json(200, artillery.project(gun, distance_m, azimuth_deg, scale))
            return

        results = []
        for t in targets:
            try:
                pos = (float(t["x"]), float(t["y"]))
            except (ValueError, KeyError, TypeError):
                results.append({"id": t.get("id"), "error": "coordonnees invalides"})
                continue
            solution = artillery.solve(gun, pos, scale)
            solution["id"] = t.get("id")
            solution["label"] = t.get("label")
            results.append(solution)

        self._json(200, {"results": results})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"Artillerie -> {url}   (Ctrl+C pour arreter)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\narret")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
