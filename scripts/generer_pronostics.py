"""Génère les pronostics des prochains matchs (calendrier football-data) en JSON.

Usage : .venv/bin/python scripts/generer_pronostics.py [--calendrier fichier.csv] [--sortie f.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from missa import donnees  # noqa: E402
from missa.pipeline import Moteur  # noqa: E402
from missa.stockage import Stockage  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calendrier", default=donnees.URL_CALENDRIER)
    ap.add_argument("--sortie", default=str(RACINE / "data" / "pronostics.json"))
    ap.add_argument("--maintenant", default=None, help="date/heure de référence (tests)")
    a = ap.parse_args()
    cal = donnees.charger_calendrier(a.calendrier)
    res = Moteur(stockage=Stockage()).predire(cal, a.maintenant)
    Path(a.sortie).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    n = sum(len(c["matchs"]) for c in res["championnats"])
    print(f"{n} matchs prédits -> {a.sortie}")


if __name__ == "__main__":
    main()
