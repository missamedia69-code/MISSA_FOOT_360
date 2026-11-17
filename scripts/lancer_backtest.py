"""Backtest complet sur 5 grands championnats.

Entraînement des poids de combinaison : saisons 2019/20 → 2022/23
Test (jamais vu)                       : saisons 2023/24 → 2026/27 (en cours)
Les saisons 2017/18 et 2018/19 servent à « chauffer » Dixon-Coles et Elo.

Usage : .venv/bin/python scripts/lancer_backtest.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missa import donnees, evaluation, marge  # noqa: E402
from missa.backtest import LogitOrdonne, preparer, trio  # noqa: E402
from missa.combinaison import PoolLogarithmique  # noqa: E402

SAISONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526", "2627"]
ENTRAINEMENT = ["1920", "2021", "2122", "2223"]
TEST = ["2324", "2425", "2526", "2627"]
CACHE = donnees.CACHE / "prepare.pkl"
SORTIE = Path(__file__).resolve().parent.parent / "docs" / "resultats_backtest.md"


def main():
    if CACHE.exists():
        df = pd.read_pickle(CACHE)
    else:
        df = preparer(donnees.charger(saisons=SAISONS))
        df.to_pickle(CACHE)

    ok = df.dropna(subset=["dc_H", "elo_ecart", "marche_ouv_H", "marche_clo_H", "max_H"])
    tr, te = ok[ok.saison.isin(ENTRAINEMENT)], ok[ok.saison.isin(TEST)]
    lignes = [f"# Résultats du backtest\n",
              f"Matchs d'entraînement : {len(tr)} — matchs de test (jamais vus) : {len(te)}\n"]

    # Elo -> 1X2
    lo = LogitOrdonne().ajuster(tr.elo_ecart, tr.resultat)
    src_tr = {"marche_ouv": trio(tr, "marche_ouv"), "dixon_coles": trio(tr, "dc"),
              "elo": lo.predire(tr.elo_ecart)}
    src_te = {"marche_ouv": trio(te, "marche_ouv"), "dixon_coles": trio(te, "dc"),
              "elo": lo.predire(te.elo_ecart)}

    # 1) Méthodes de retrait de marge (sur les cotes de clôture, tout l'échantillon)
    lignes.append("\n## 1. Retrait de marge (cotes de clôture, log-loss : plus bas = mieux)\n")
    lignes.append("| Méthode | log-loss | RPS |\n|---|---|---|")
    cotes = ok[["clo_H", "clo_D", "clo_A"]].to_numpy(float)
    for m in marge.METHODES:
        p = np.array([marge.probabilites(c, m) for c in cotes])
        r = evaluation.resume(p, ok.resultat)
        lignes.append(f"| {m} | {r['log_loss']:.5f} | {r['rps']:.5f} |")

    # 2) Précision de chaque source et de la combinaison, sur le TEST
    pool = PoolLogarithmique(["marche_ouv", "dixon_coles", "elo"]).ajuster(src_tr, tr.resultat)
    combi = pool.predire(src_te)
    lignes.append("\n## 2. Précision sur les saisons de test\n")
    lignes.append("| Source | RPS | log-loss | Brier |\n|---|---|---|---|")
    base = np.tile(np.bincount(tr.resultat, minlength=3) / len(tr), (len(te), 1))
    for nom, p in [("Fréquences moyennes (naïf)", base), ("Elo", src_te["elo"]),
                   ("Dixon-Coles", src_te["dixon_coles"]),
                   ("Marché avant clôture", src_te["marche_ouv"]),
                   ("**Combinaison MISSA**", combi),
                   ("Marché à la clôture (référence)", trio(te, "marche_clo"))]:
        r = evaluation.resume(p, te.resultat)
        lignes.append(f"| {nom} | {r['rps']:.5f} | {r['log_loss']:.5f} | {r['brier']:.5f} |")
    lignes.append(f"\nPoids appris : {pool.resume()}\n")

    # 3) Simulation de paris : meilleure cote du marché (avant clôture) quand EV > seuil
    lignes.append("\n## 3. Paris simulés (meilleure cote avant clôture, mise de 1)\n")
    lignes.append("CLV = valeur obtenue par rapport à la cote juste de clôture "
                  "(meilleur indicateur de rentabilité future).\n")
    lignes.append("| Probabilités utilisées | Seuil EV | Paris | CLV moyen | Rendement réel | Cote moy. |")
    lignes.append("|---|---|---|---|---|---|")
    maxi = te[["max_H", "max_D", "max_A"]].to_numpy(float)
    clo = trio(te, "marche_clo")
    res = te.resultat.to_numpy()
    for nom, p in (("Marché avant clôture", src_te["marche_ouv"]), ("Combinaison MISSA", combi),
                   ("Dixon-Coles seul", src_te["dixon_coles"])):
        ev = p * maxi - 1
        for seuil in (0.02, 0.05):
            sel = np.argwhere(ev > seuil)
            if len(sel) == 0:
                continue
            i, k = sel[:, 0], sel[:, 1]
            cote = maxi[i, k]
            clv = cote * clo[i, k] - 1
            gain = np.where(res[i] == k, cote - 1, -1.0)
            lignes.append(f"| {nom} | {seuil:.0%} | {len(i)} | {clv.mean():+.2%} | "
                          f"{gain.mean():+.2%} | {cote.mean():.2f} |")

    texte = "\n".join(lignes) + "\n"
    SORTIE.write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
