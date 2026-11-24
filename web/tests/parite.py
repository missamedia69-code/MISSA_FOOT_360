"""Vérifie la parité entre le jumeau numérique du navigateur et missa/jumeau.py.

Compare ~400 probabilités (toutes les options du catalogue sur plusieurs matchs,
des combinés officiels, des modulations et un ticket multi-matchs).

    .venv/bin/pip install numpy scipy
    .venv/bin/python web/tests/parite.py

Écart attendu : < 1e-9 (les deux moteurs lisent la même matrice arrondie).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
import numpy as np  # noqa: E402
from missa.jumeau import JumeauMatch, proba_combine  # noqa: E402

DONNEES = RACINE / "web" / "data" / "donnees.json"
HARNAIS = RACINE / "web" / "tests" / "jumeau_node.mjs"


def jumeau(m: dict) -> JumeauMatch:
    j = m["jumeau"]
    return JumeauMatch(np.array(j["matrice"]), tuple(j["part_1mt"]),
                       tuple(j["corners"]), tuple(j["cartons"]))


def main() -> None:
    d = json.loads(DONNEES.read_text(encoding="utf-8"))
    matchs = {m["id"]: m for c in d["championnats"] for m in c["matchs"]}
    ids = list(matchs)[:2]
    cas, refs = [], []

    def ajouter(c: dict, ref: float):
        cas.append(c)
        refs.append(float(ref))

    # 1. les 193 options du catalogue, sur 2 matchs
    for mid in ids:
        J = jumeau(matchs[mid])
        for groupe in d["catalogue"]:
            for o in groupe["options"]:
                ajouter({"type": "simple", "matchId": mid, "code": o["code"]}, J.proba(o["code"]))

    # 2. modulations (absence d'un attaquant, arbitre sévère…)
    modulations = [
        {"attaque_dom": 0.85, "attaque_ext": 1.1, "corners_dom": 1.2,
         "corners_ext": 0.9, "cartons": 1.4},
        {"attaque_dom": 1.35, "attaque_ext": 0.7, "cartons": 0.6},
    ]
    for k, mod in enumerate(modulations):
        J = jumeau(matchs[ids[k]]).moduler(**mod)
        for code in ("1X2:1", "OU:2.5:plus", "BTTS:oui", "DC:1N & OU:2.5:plus",
                     "1X2@MT1:N", "MTFT:1/N", "CORNERS_OU:9.5:plus",
                     "CARTONS_OU:3.5:plus", "TG:6+", "MARGE:dom3+"):
            ajouter({"type": "simple", "matchId": ids[k], "code": code,
                     "modulation": mod}, J.proba(code))

    # 3. plusieurs sélections d'un même match (corrélations exactes)
    J = jumeau(matchs[ids[0]])
    for legs in (["1X2:1", "BTTS:oui"], ["DC:1N", "OU:2.5:plus", "CORNERS_OU:9.5:plus"]):
        ajouter({"type": "combine", "matchId": ids[0], "legs": legs},
                proba_combine([(ids[0], s) for s in legs], {ids[0]: J})["proba"])

    # 4. ticket multi-matchs (règle « une sélection par match »)
    legs = [{"matchId": mid, "code": "DC:1N"} for mid in ids]
    ajouter({"type": "ticket", "legs": legs},
            proba_combine([(l["matchId"], l["code"]) for l in legs],
                          {mid: jumeau(matchs[mid]) for mid in ids}, True)["proba"])

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"donnees": str(DONNEES), "cas": cas}, f, ensure_ascii=False)
        chemin = f.name
    try:
        r = subprocess.run(["node", str(HARNAIS), chemin], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"Harnais Node en échec : {r.stderr[:2000]}")
        obtenus = [x["proba"] for x in json.loads(r.stdout)]
    finally:
        Path(chemin).unlink(missing_ok=True)

    assert len(obtenus) == len(refs), (len(obtenus), len(refs))
    ecarts = [abs(a - b) for a, b in zip(obtenus, refs)]
    pire = max(range(len(ecarts)), key=lambda i: ecarts[i])
    print(f"{len(refs)} probabilités comparées — écart maximal "
          f"{ecarts[pire]:.3e} sur : {json.dumps(cas[pire], ensure_ascii=False)[:120]}")
    assert ecarts[pire] < 1e-9, f"Parité rompue : {ecarts[pire]}"
    print("Parité navigateur ↔ Python : OK")


if __name__ == "__main__":
    main()
