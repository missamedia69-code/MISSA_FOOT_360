"""Serveur de l'application web MISSA FOOT 360 (bibliothèque standard uniquement).

    python3 web/serveur.py                     # http://0.0.0.0:8080
    python3 web/serveur.py --port 3000
    MISSA_API=http://127.0.0.1:8000 python3 web/serveur.py

Sert les fichiers statiques de web/ et relaie /api/* vers l'API FastAPI du dépôt
(`uvicorn api.main:app --port 8000`). Sans API, l'application fonctionne
entièrement hors ligne avec web/data/donnees.json.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB = Path(__file__).resolve().parent
API = os.environ.get("MISSA_API", "http://127.0.0.1:8000").rstrip("/")


class Gestionnaire(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        if self.path.startswith("/api/"):
            super().log_message(fmt, *args)

    def _reponse_json(self, code: int, objet: dict) -> None:
        corps = json.dumps(objet, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corps)

    def _proxy(self, methode: str) -> None:
        chemin = self.path[len("/api"):] or "/"
        url = API + chemin
        longueur = int(self.headers.get("Content-Length") or 0)
        corps = self.rfile.read(longueur) if longueur else None
        entetes = {"Accept": "application/json"}
        for h in ("Content-Type", "x-cle-admin"):
            if self.headers.get(h):
                entetes[h] = self.headers[h]
        requete = urllib.request.Request(url, data=corps, headers=entetes, method=methode)
        try:
            with urllib.request.urlopen(requete, timeout=15) as r:
                donnees = r.read()
                type_contenu = r.headers.get("Content-Type", "application/json; charset=utf-8")
                code = r.status
        except urllib.error.HTTPError as e:
            donnees, type_contenu, code = e.read(), "application/json; charset=utf-8", e.code
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            self._reponse_json(502, {"erreur": "API MISSA FOOT 360 indisponible",
                                     "detail": str(e), "api": API})
            return
        self.send_response(code)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(donnees)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(donnees)

    def do_GET(self) -> None:
        if self.path.startswith("/api"):
            self._proxy("GET")
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith("/api"):
            self._proxy("POST")
        else:
            self._reponse_json(405, {"erreur": "Méthode non autorisée"})

    def end_headers(self) -> None:
        # Autorise l'aperçu intégré (aucun en-tête X-Frame-Options / CSP bloquante).
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def main() -> None:
    p = argparse.ArgumentParser(description="Serveur web MISSA FOOT 360")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=int(os.environ.get("MISSA_PORT", 8080)))
    a = p.parse_args()
    if not (WEB / "data" / "donnees.json").exists():
        raise SystemExit("web/data/donnees.json manquant : lancez python3 web/scripts/preparer_donnees.py")
    serveur = ThreadingHTTPServer((a.host, a.port), Gestionnaire)
    print(f"MISSA FOOT 360 → http://{a.host}:{a.port}  (API : {API})", flush=True)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        serveur.server_close()


if __name__ == "__main__":
    main()
