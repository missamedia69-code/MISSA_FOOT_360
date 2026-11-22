"""Performances mesurées du moteur, pour l'écran « Statistiques » de l'application.

Saisons de test 2023/24 → 2026/27 (jamais vues pendant l'apprentissage), 5 grands championnats.
Pour chaque type de pari : la sélection la plus probable du moteur, sa probabilité annoncée moyenne
et son taux de réussite réel. Également par championnat et par niveau de confiance.
Résultat : data/stats_moteur.json (publié avec les pronostics).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from missa import donnees  # noqa: E402
from missa.backtest import LogitOrdonne, trio  # noqa: E402
from missa.combinaison import PoolLogarithmique  # noqa: E402
from missa.dixon_coles import matrice_scores  # noqa: E402
from missa.selections import ajuster_matrice, proba_selection  # noqa: E402

TEST = ["2324", "2425", "2526", "2627"]


def main():
    df = pd.read_pickle(donnees.CACHE / "prepare_jumeau.pkl")
    cfg = json.loads((RACINE / "data" / "modele.json").read_text())
    te = df[df.saison.isin(TEST)].dropna(subset=["dc_H", "marche_ouv_H", "elo_ecart"]).copy()
    pool = PoolLogarithmique(cfg["pool"]["sources"])
    pool.poids, pool.biais = np.array(cfg["pool"]["poids"]), np.array(cfg["pool"]["biais"])
    lo = LogitOrdonne()
    lo.b, lo.c1, lo.c2 = (cfg["elo_logit"][k] for k in ("b", "c1", "c2"))
    p = pool.predire({"marche_ouv": trio(te, "marche_ouv"), "dixon_coles": trio(te, "dc"), "elo": lo.predire(te.elo_ecart)})
    p_ou = te["marche_ouv_plus25"].fillna(te["dc_plus25"]).to_numpy(float)
    btts = np.array([proba_selection(ajuster_matrice(matrice_scores(r.dc_lambda, r.dc_mu, r.dc_rho), p[n], p_ou[n]), "btts_oui")
                     for n, r in enumerate(te.itertuples())])
    hg, ag = te.buts_dom.to_numpy(), te.buts_ext.to_numpy()

    def meilleur(probas, issues):
        k = probas.argmax(1)
        return probas[np.arange(len(k)), k], issues[np.arange(len(k)), k]

    familles = {
        "Résultat final (1X2)": (p, np.stack([hg > ag, hg == ag, hg < ag], 1)),
        "Double chance": (np.stack([p[:, 0] + p[:, 1], p[:, 0] + p[:, 2], p[:, 1] + p[:, 2]], 1),
                          np.stack([hg >= ag, hg != ag, hg <= ag], 1)),
        "Plus/moins 2,5 buts": (np.stack([p_ou, 1 - p_ou], 1), np.stack([hg + ag >= 3, hg + ag <= 2], 1)),
        "Les deux équipes marquent": (np.stack([btts, 1 - btts], 1),
                                      np.stack([(hg > 0) & (ag > 0), (hg == 0) | (ag == 0)], 1)),
    }
    par_type = []
    tout_p, tout_o = [], []
    for nom, (pr, iss) in familles.items():
        pb, ok = meilleur(pr, iss)
        tout_p.append(pb), tout_o.append(ok)
        par_type.append({"type": nom, "n": int(len(pb)), "annonce": round(float(pb.mean()), 4),
                         "reussite": round(float(ok.mean()), 4)})
    pb_all, ok_all = np.concatenate(tout_p), np.concatenate(tout_o)
    niveaux = []
    for nom, lo_, hi in (("Très haute (≥ 85 %)", .85, 1.01), ("Haute (75–85 %)", .75, .85),
                         ("Moyenne (60–75 %)", .60, .75), ("Faible (< 60 %)", 0, .60)):
        m = (pb_all >= lo_) & (pb_all < hi)
        niveaux.append({"niveau": nom, "n": int(m.sum()), "annonce": round(float(pb_all[m].mean()), 4),
                        "reussite": round(float(ok_all[m].mean()), 4)})
    pb1, ok1 = meilleur(*familles["Résultat final (1X2)"])
    par_championnat = []
    for c in sorted(te.championnat.unique()):
        m = (te.championnat == c).to_numpy()
        par_championnat.append({"championnat": donnees.CHAMPIONNATS.get(c, c), "n": int(m.sum()),
                                "reussite_1x2": round(float(ok1[m].mean()), 4)})
    fiab = json.loads((RACINE / "data" / "fiabilite_marches.json").read_text())["familles"]
    stats = {
        "periode": "saisons 2023/24 à 2026/27 (jamais vues par le moteur)", "matchs": int(len(te)),
        "pronostics_evalues": int(len(pb_all)), "reussis": int(ok_all.sum()),
        "reussite_globale": round(float(ok_all.mean()), 4), "annonce_moyenne": round(float(pb_all.mean()), 4),
        "par_type": par_type, "par_niveau": niveaux, "par_championnat": par_championnat,
        "combines": fiab.get("combines_multi", []),
    }
    (RACINE / "data" / "stats_moteur.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1)[:2500])


if __name__ == "__main__":
    main()
