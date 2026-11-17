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

import json  # noqa: E402

from missa import confiance, donnees, evaluation, marge  # noqa: E402
from missa.dixon_coles import matrice_scores  # noqa: E402
from missa.selections import ajuster_matrice, proba_selection  # noqa: E402
from missa.backtest import LogitOrdonne, preparer, trio  # noqa: E402
from missa.combinaison import PoolLogarithmique  # noqa: E402

SAISONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526", "2627"]
ENTRAINEMENT = ["1920", "2021", "2122", "2223"]
TEST = ["2324", "2425", "2526", "2627"]
CACHE = donnees.CACHE / "prepare.pkl"
RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "docs" / "resultats_backtest.md"
MODELE = RACINE / "data" / "modele.json"


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

    # 4) Plus/moins 2,5 buts : marché vs Dixon-Coles
    ou = te.dropna(subset=["marche_ouv_plus25"])
    y_ou = (ou.buts_dom + ou.buts_ext >= 3).to_numpy()
    lignes.append("\n## 4. Plus/moins 2,5 buts (log-loss, plus bas = mieux)\n")
    for nom, col in (("Dixon-Coles", "dc_plus25"), ("Marché avant clôture", "marche_ouv_plus25"),
                     ("Marché à la clôture", "marche_clo_plus25")):
        q = np.clip(ou[col].to_numpy(float), 1e-6, 1 - 1e-6)
        ll = -np.mean(np.where(y_ou, np.log(q), np.log(1 - q)))
        lignes.append(f"- {nom} : {ll:.5f}")

    # 5) Mode haute confiance : probabilités finales du moteur sur le test
    p_ou = te["marche_ouv_plus25"].fillna(te["dc_plus25"]).to_numpy(float)
    btts = np.empty(len(te))
    for n_, (k, r) in enumerate(te.iterrows()):
        P = matrice_scores(r.dc_lambda, r.dc_mu, r.dc_rho)
        P = ajuster_matrice(P, combi[n_], p_ou[n_])
        btts[n_] = proba_selection(P, "btts_oui")
    hg, ag = te.buts_dom.to_numpy(), te.buts_ext.to_numpy()
    probas = {"1X2": combi,
              "double_chance": np.stack([combi[:, 0] + combi[:, 1], combi[:, 0] + combi[:, 2],
                                         combi[:, 1] + combi[:, 2]], axis=1),
              "buts_2.5": np.stack([p_ou, 1 - p_ou], axis=1),
              "btts": np.stack([btts, 1 - btts], axis=1)}
    issues = {"1X2": np.stack([hg > ag, hg == ag, hg < ag], axis=1),
              "double_chance": np.stack([hg >= ag, hg != ag, hg <= ag], axis=1),
              "buts_2.5": np.stack([hg + ag >= 3, hg + ag <= 2], axis=1),
              "btts": np.stack([(hg > 0) & (ag > 0), (hg == 0) | (ag == 0)], axis=1)}
    cotes = {"1X2": maxi, "buts_2.5": te[["max_plus25", "max_moins25"]].to_numpy(float)}
    table = confiance.construire(probas, issues, cotes)
    confiance.sauvegarder(table)
    noms = {"1X2": "Résultat 1X2", "double_chance": "Double chance",
            "buts_2.5": "Plus/moins 2,5 buts", "btts": "Les deux équipes marquent"}
    lignes.append("\n## 5. Mode haute confiance (sélection la plus probable, saisons de test)\n")
    lignes.append("Taux réel = part des sélections réellement gagnantes. Rendement = en pariant à la "
                  "meilleure cote du marché (quand elle est connue).\n")
    for fam, tr_ in table.items():
        lignes.append(f"\n### {noms[fam]}\n")
        lignes.append("| Probabilité annoncée | Part des matchs | Sélections | Taux réel | Cote moy. | Rendement |")
        lignes.append("|---|---|---|---|---|---|")
        for t in tr_:
            cm = f"{t['cote_moyenne']:.2f}" if "cote_moyenne" in t else "—"
            rd = f"{t['rendement']:+.1%}" if "rendement" in t else "—"
            lignes.append(f"| {t['de']:.0%}–{min(t['a'],1):.0%} | {t['part_des_matchs']:.1%} | "
                          f"{t['n']} | **{t['taux_reel']:.1%}** | {cm} | {rd} |")

    # 6) Fiabilité : probabilité annoncée vs fréquence observée (1X2)
    lignes.append("\n## 6. Fiabilité des probabilités 1X2 (annoncé vs observé)\n")
    lignes.append("| Tranche | Sélections | Annoncé | Observé |\n|---|---|---|---|")
    for c in confiance.courbe_fiabilite(combi, issues["1X2"]):
        lignes.append(f"| {c['de']:.0%}–{c['a']:.0%} | {c['n']} | {c['annonce']:.1%} | {c['observe']:.1%} |")

    MODELE.write_text(json.dumps({
        "pool": {"sources": pool.sources, "poids": list(map(float, pool.poids)),
                 "biais": list(map(float, pool.biais))},
        "elo_logit": {"b": lo.b, "c1": lo.c1, "c2": lo.c2},
        "dixon_coles_xi": 0.0019, "elo": {"k": 20.0, "avantage_domicile": 70.0},
        "entrainement": ENTRAINEMENT, "test": TEST,
    }, indent=1), encoding="utf-8")

    texte = "\n".join(lignes) + "\n"
    SORTIE.write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
