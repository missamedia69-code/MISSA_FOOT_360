"""Mode « haute confiance » : pour chaque type de pari et chaque niveau de probabilité,
le taux de réussite RÉELLEMENT observé sur des saisons que le moteur n'a jamais vues.

L'application n'affiche donc jamais une promesse, mais un historique mesuré :
« sur 1 240 sélections de ce niveau, 90,3 % ont été gagnantes ».
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

FAMILLES = {
    "1X2": ["1", "N", "2"],
    "double_chance": ["1N", "12", "N2"],
    "buts_2.5": ["plus_2.5", "moins_2.5"],
    "btts": ["btts_oui", "btts_non"],
}
BORNES = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0001]
NIVEAUX = ((0.85, "Très haute confiance"), (0.75, "Haute confiance"),
           (0.60, "Confiance moyenne"), (0.0, "Confiance faible"))
N_MIN = 50
FICHIER = Path(__file__).resolve().parent.parent / "data" / "calibration.json"


def construire(probas: dict, issues: dict, cotes: dict | None = None) -> dict:
    """probas[famille] : (n, k) ; issues[famille] : (n, k) booléens ; cotes[famille] : (n, k)."""
    table = {}
    for fam, p in probas.items():
        p, o = np.asarray(p, float), np.asarray(issues[fam], bool)
        ok = ~np.isnan(p).any(axis=1)
        p, o = p[ok], o[ok]
        best = p.argmax(axis=1)
        pb = p[np.arange(len(p)), best]
        gagne = o[np.arange(len(o)), best]
        c = None
        if cotes and cotes.get(fam) is not None:
            c = np.asarray(cotes[fam], float)[ok][np.arange(len(p)), best]
        tranches = []
        for lo, hi in zip(BORNES[:-1], BORNES[1:]):
            m = (pb >= lo) & (pb < hi)
            if m.sum() == 0:
                continue
            t = {"de": lo, "a": min(hi, 1.0), "n": int(m.sum()),
                 "taux_reel": float(gagne[m].mean()), "proba_moyenne": float(pb[m].mean()),
                 "part_des_matchs": float(m.mean())}
            if c is not None and np.isfinite(c[m]).sum() > 0:
                mc = m & np.isfinite(c)
                t["cote_moyenne"] = float(c[mc].mean())
                t["rendement"] = float(np.where(gagne[mc], c[mc] - 1, -1).mean())
            tranches.append(t)
        table[fam] = tranches
    return table


def sauvegarder(table: dict, fichier: Path = FICHIER) -> None:
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps(table, indent=1, ensure_ascii=False), encoding="utf-8")


def charger(fichier: Path = FICHIER) -> dict:
    return json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {}


def niveau(table: dict, famille: str, proba: float) -> dict:
    """Historique réel de la tranche de probabilité correspondante + niveau de confiance."""
    for t in table.get(famille, []):
        if t["de"] <= proba < t["a"] or (proba >= 1.0 and t["a"] >= 1.0):
            taux = t["taux_reel"] if t["n"] >= N_MIN else min(t["taux_reel"], proba)
            label = next(l for s, l in NIVEAUX if taux >= s)
            return {"niveau": label, "taux_historique": t["taux_reel"], "n_historique": t["n"],
                    "haute_confiance": taux >= 0.85 and t["n"] >= N_MIN}
    return {"niveau": "Confiance faible", "taux_historique": None, "n_historique": 0,
            "haute_confiance": False}


def courbe_fiabilite(p, o, nb: int = 10) -> list[dict]:
    """Probabilité annoncée vs fréquence observée (toutes sélections confondues)."""
    p, o = np.ravel(p), np.ravel(o).astype(float)
    ok = np.isfinite(p)
    p, o = p[ok], o[ok]
    bords = np.linspace(0, 1, nb + 1)
    res = []
    for lo, hi in zip(bords[:-1], bords[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum():
            res.append({"de": lo, "a": hi, "n": int(m.sum()), "annonce": float(p[m].mean()),
                        "observe": float(o[m].mean())})
    return res
