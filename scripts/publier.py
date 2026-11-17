"""Publication automatique (lancée par GitHub Actions toutes les 3 heures).

1. Importe les pronostics d'experts de data/experts/pronostics.csv (s'il existe).
2. Clôture automatiquement les pronostics des matchs joués (cotes de clôture de football-data)
   -> CLV et note de chaque expert.
3. Calcule les pronostics des prochains matchs (calendrier football-data).
4. Écrit publication/pronostics.json, publication/pronostiqueurs.json, publication/etat.json.

Usage : .venv/bin/python scripts/publier.py [--sortie publication] [--calendrier url_ou_fichier]
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from missa import donnees  # noqa: E402
from missa.pipeline import Moteur, identifiant, saisons_precedentes  # noqa: E402
from missa.stockage import Stockage  # noqa: E402

CSV_EXPERTS = RACINE / "data" / "experts" / "pronostics.csv"


def cloturer(stockage: Stockage) -> int:
    """Renseigne la cote juste de clôture des pronostics dont le match est joué."""
    ouverts = [p for p in stockage.pronostics() if p["proba_juste_cloture"] is None]
    champs = {p["match_id"].split("-")[0] for p in ouverts}
    n = 0
    for champ in champs:
        parts = []
        for s in saisons_precedentes(pd.Timestamp.now(), 2):
            try:
                parts.append(donnees.charger_saison(champ, s))
            except Exception:
                pass
        if not parts:
            continue
        h = pd.concat(parts)
        index = {identifiant(champ, r.date, r.domicile, r.exterieur): r for r in h.itertuples()}
        for mid in {p["match_id"] for p in ouverts if p["match_id"].startswith(champ + "-")}:
            r = index.get(mid)
            if r is None:
                continue
            cotes = {}
            if pd.notna(r.clo_H):
                cotes["1x2"] = [r.clo_H, r.clo_D, r.clo_A]
            if pd.notna(r.clo_plus25):
                cotes["ou25"] = [r.clo_plus25, r.clo_moins25]
            if cotes:
                n += stockage.cloturer_match(mid, cotes)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sortie", default=str(RACINE / "publication"))
    ap.add_argument("--calendrier", default=donnees.URL_CALENDRIER)
    a = ap.parse_args()
    sortie = Path(a.sortie)
    sortie.mkdir(parents=True, exist_ok=True)

    stockage = Stockage(Path(tempfile.mkdtemp()) / "experts.db")
    rapport_experts = {"importes": 0, "refuses": []}
    if CSV_EXPERTS.exists():
        rapport_experts = stockage.importer_csv(CSV_EXPERTS)
        rapport_experts["clotures"] = cloturer(stockage)

    calendrier = donnees.charger_calendrier(a.calendrier)
    # on ne publie que les matchs à venir (ou commencés depuis moins de 2 heures)
    limite = pd.Timestamp.now(tz="Europe/London").tz_localize(None) - pd.Timedelta(hours=2)
    calendrier = calendrier[calendrier["coup_envoi"].fillna(calendrier["date"]) >= limite]
    res = Moteur(stockage=stockage).predire(calendrier)
    nb = sum(len(c["matchs"]) for c in res["championnats"])

    (sortie / "pronostics.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    (sortie / "pronostiqueurs.json").write_text(json.dumps(stockage.classement(), ensure_ascii=False),
                                                encoding="utf-8")
    etat = {"genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "matchs": nb, "championnats": [c["code"] for c in res["championnats"] if c["matchs"]],
            "experts": rapport_experts}
    (sortie / "etat.json").write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(etat, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
