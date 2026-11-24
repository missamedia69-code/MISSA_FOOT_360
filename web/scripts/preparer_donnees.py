"""Prépare le jeu de données de l'application web MISSA FOOT 360.

Priorité :
  1. data/pronostics.json  (pronostics frais produits par scripts/generer_pronostics.py)
  2. android/app/src/main/assets/demo.json  (données de démonstration hors ligne)

Ajoute les tables de calibration et les paramètres du modèle, puis écrit
web/data/donnees.json (JSON compact, sans dépendance externe).

    python3 web/scripts/preparer_donnees.py
"""
from __future__ import annotations

import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "web" / "data" / "donnees.json"


def charger(chemin: Path):
    return json.loads(chemin.read_text(encoding="utf-8")) if chemin.exists() else None


def main() -> None:
    frais = charger(RACINE / "data" / "pronostics.json")
    demo = charger(RACINE / "android" / "app" / "src" / "main" / "assets" / "demo.json")
    source = frais or demo
    if source is None:
        raise SystemExit("Aucune donnée : lancez scripts/generer_pronostics.py")

    d = dict(source)
    d["source_donnees"] = "pronostics" if frais else "demonstration"
    d["calibration"] = charger(RACINE / "data" / "calibration.json") or {}
    d["modele"] = charger(RACINE / "data" / "modele.json") or {}
    d["fiabilite_marches"] = charger(RACINE / "data" / "fiabilite_marches.json") or {}
    # Le pipeline frais ne publie pas les tables de validation : on complète
    # avec celles de la démo (statistiques mesurées, suivi des pronostics).
    if frais and demo:
        for cle in ("stats_moteur", "suivi_pronostics", "suivi_value", "avertissement"):
            d.setdefault(cle, demo.get(cle))

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    matchs = sum(len(c["matchs"]) for c in d["championnats"])
    print(f"{SORTIE.relative_to(RACINE)} : {matchs} matchs, "
          f"{len(d['championnats'])} championnats, source « {d['source_donnees']} », "
          f"{SORTIE.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    main()
