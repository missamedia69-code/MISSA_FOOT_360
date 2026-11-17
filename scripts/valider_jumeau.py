"""Validation du jumeau numérique sur des saisons jamais vues.

1. Corners et cartons : modèles par équipe ajustés au fil de l'eau (sans voir le futur).
2. Paramètres globaux (part des buts en 1re mi-temps, dispersion des corners, covariance des
   cartons) estimés sur les saisons d'ENTRAÎNEMENT seulement.
3. Sur les saisons de TEST : pour chaque marché du catalogue, probabilité annoncée vs fréquence
   réelle, et gain de précision par rapport à une prédiction naïve (fréquence moyenne).
4. Combinés aléatoires de 2 à 6 matchs : probabilité annoncée vs taux de réussite réel.

Résultats : docs/validation_jumeau.md et data/fiabilite_marches.json (utilisé par l'application).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from missa import comptages, donnees, marge  # noqa: E402
from missa.backtest import LogitOrdonne, trio  # noqa: E402
from missa.combinaison import PoolLogarithmique  # noqa: E402
from missa.dixon_coles import matrice_scores  # noqa: E402
from missa.jumeau import JumeauMatch, catalogue, composante, terme_buts, terme_comptage  # noqa: E402
from missa.selections import ajuster_matrice  # noqa: E402

ENTRAINEMENT = ["1920", "2021", "2122", "2223"]
TEST = ["2324", "2425", "2526", "2627"]
SORTIE_MD = RACINE / "docs" / "validation_jumeau.md"
SORTIE_JSON = RACINE / "data" / "fiabilite_marches.json"
CACHE = donnees.CACHE / "prepare_jumeau.pkl"
BORNES = np.array([0, .1, .2, .3, .4, .5, .6, .7, .8, .85, .9, .95, 1.0001])


def resultat(selection: str, r) -> bool:
    """La sélection a-t-elle gagné ? (mêmes fonctions que le calcul des probabilités)"""
    a, b, i, j = (np.int64(r[c]) for c in ("mt_dom", "mt_ext", "buts_dom", "buts_ext"))
    ok = True
    for disj in selection.split("&"):
        v = False
        for t in (t.strip() for t in disj.split("|")):
            comp = composante(t)
            if comp == "buts":
                v |= bool(terme_buts(t, a, b, i, j))
            else:
                x, y = (r["corners_dom"], r["corners_ext"]) if comp == "corners" else (r["jaunes_dom"], r["jaunes_ext"])
                nom, *opts = t.split(":")
                v |= bool(terme_comptage(nom.split("_", 1)[1], opts, np.int64(x), np.int64(y)))
        ok &= v
    return ok


def famille(code: str) -> str:
    comp = composante(code)
    if comp != "buts":
        return comp
    if "&" in code:
        return "combines_officiels"
    if any(k in code for k in ("@MT", "MTFT", "MT_PLUS", "_2MT", "_1MT", "OU_2MT")):
        return "mi_temps"
    if code.startswith("CS"):
        return "score_exact"
    return "buts_match"


def preparer() -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_pickle(CACHE)
    df = pd.read_pickle(donnees.CACHE / "prepare.pkl")  # contient déjà mi-temps, corners, cartons
    for q in ("corners", "cartons"):
        df[f"{q}_m_dom"] = np.nan
        df[f"{q}_m_ext"] = np.nan
    for champ, g in df.groupby("championnat"):
        mois = g["date"].dt.to_period("M").unique()
        for m in mois:
            d = m.start_time
            hist = g[(g["date"] < d) & (g["date"] >= d - pd.Timedelta(days=3 * 365))]
            idx = g.index[g["date"].dt.to_period("M") == m]
            for q in ("corners", "cartons"):
                mod = comptages.ajuster(hist, q, d)
                if mod is None:
                    continue
                for k in idx:
                    r = mod.buts_attendus(df.at[k, "domicile"], df.at[k, "exterieur"])
                    if r:
                        df.loc[k, [f"{q}_m_dom", f"{q}_m_ext"]] = r
        print(f"[validation] {champ} prêt")
    df.to_pickle(CACHE)
    return df


def main():
    df = preparer()
    cfg = json.loads((RACINE / "data" / "modele.json").read_text())
    tr = df[df.saison.isin(ENTRAINEMENT)].dropna(subset=["mt_dom"])
    te = df[df.saison.isin(TEST)].dropna(subset=["dc_H", "marche_ouv_H", "elo_ecart", "mt_dom"])

    # --- paramètres globaux estimés sur l'entraînement ---------------------------------
    tot = tr.buts_dom + tr.buts_ext
    parts = [((tr.mt_dom + tr.mt_ext)[tot == n].sum() / (n * (tot == n).sum()), n, (tot == n).sum())
             for n in range(1, 8) if (tot == n).sum() > 50]
    sv, nv, wv = (np.array(v, float) for v in zip(*parts))
    b_part, a_part = np.polyfit(nv, sv, 1, w=np.sqrt(wv))
    c = tr.dropna(subset=["corners_m_dom", "corners_dom"])
    mt = c.corners_m_dom + c.corners_m_ext
    t = c.corners_dom + c.corners_ext
    k_total = float(np.mean(mt ** 2) / max(np.mean((t - mt) ** 2) - np.mean(mt), 1e-3))
    # corrélation de répartition (bêta-binomiale) ajustée sur la variance des corners du domicile
    p_ = c.corners_m_dom / mt
    var_t = np.mean((t - mt) ** 2)
    e_tt1 = var_t + np.mean(mt ** 2) - np.mean(mt)
    cible = np.mean((c.corners_dom - c.corners_m_dom) ** 2) - np.mean(p_ ** 2) * var_t
    base = np.mean(mt * p_ * (1 - p_))
    rho_corners = float(np.clip((cible - base) / (np.mean(p_ * (1 - p_)) * e_tt1), 0, 0.5))
    y = tr.dropna(subset=["cartons_m_dom", "jaunes_dom"])
    cov_cartons = float(np.mean((y.jaunes_dom - y.cartons_m_dom) * (y.jaunes_ext - y.cartons_m_ext)))
    params = {"part_1mt": [float(a_part), float(b_part)], "corners_k_total": k_total,
              "corners_rho": rho_corners, "cartons_cov": cov_cartons}
    print(params)

    # --- probabilités finales 1X2 (pool appris) --------------------------------------
    pool = PoolLogarithmique(cfg["pool"]["sources"])
    pool.poids, pool.biais = np.array(cfg["pool"]["poids"]), np.array(cfg["pool"]["biais"])
    lo = LogitOrdonne()
    lo.b, lo.c1, lo.c2 = (cfg["elo_logit"][k] for k in ("b", "c1", "c2"))
    combi = pool.predire({"marche_ouv": trio(te, "marche_ouv"), "dixon_coles": trio(te, "dc"),
                          "elo": lo.predire(te.elo_ecart)})
    p_ou = te["marche_ouv_plus25"].fillna(te["dc_plus25"]).to_numpy(float)

    codes = [(g, t, c_, l) for g, t, opts in catalogue() for c_, l in opts]
    base_tr = {}
    preds, obs, fam = [], [], []
    par_code: dict[str, list] = {c_: [[], []] for _, _, c_, _ in codes}
    jum = []
    for n, (k, r) in enumerate(te.iterrows()):
        P = ajuster_matrice(matrice_scores(r.dc_lambda, r.dc_mu, r.dc_rho), combi[n], p_ou[n])
        cm = (r.corners_m_dom, r.corners_m_ext) if np.isfinite(r.corners_m_dom) else (5.3, 4.4)
        ym = (r.cartons_m_dom, r.cartons_m_ext) if np.isfinite(r.cartons_m_dom) else (1.9, 2.1)
        J = JumeauMatch(P, (a_part, b_part), (cm[0], cm[1], k_total, rho_corners), (ym[0], ym[1], cov_cartons))
        jum.append(J)
        for _, _, code, _ in codes:
            if composante(code) == "corners" and not np.isfinite(r.corners_dom):
                continue
            p = J.proba(code)
            o = resultat(code, r)
            par_code[code][0].append(p)
            par_code[code][1].append(o)
            preds.append(p), obs.append(o), fam.append(famille(code))

    # fréquences naïves : sur l'entraînement
    for _, _, code, _ in codes:
        rr = tr.dropna(subset=["corners_dom"]) if composante(code) == "corners" else tr
        base_tr[code] = float(np.mean([resultat(code, row) for _, row in rr.sample(min(3000, len(rr)), random_state=0).iterrows()]))

    lignes = ["# Validation du jumeau numérique (saisons de test jamais vues)\n",
              f"Matchs de test : {len(te)}. Paramètres estimés sur l'entraînement : part des buts en "
              f"1re mi-temps = {a_part:.3f} + {b_part:.4f} × buts du match ; corners : dispersion du "
              f"total k = {k_total:.1f}, corrélation de répartition = {rho_corners:.3f} ; "
              f"covariance des cartons = {cov_cartons:.2f}.\n",
              "Gain de précision = réduction de l'erreur (score de Brier) par rapport à une prédiction "
              "naïve qui annoncerait toujours la fréquence moyenne. Plus c'est haut, mieux c'est.\n"]
    lignes.append("\n## 1. Marché par marché\n")
    lignes.append("| Groupe | Marché | Sélection | Annoncé (moy.) | Réel | Gain de précision |")
    lignes.append("|---|---|---|---|---|---|")
    for g, t, code, lib in codes:
        p, o = np.array(par_code[code][0]), np.array(par_code[code][1], float)
        if len(p) == 0:
            continue
        b_mod = np.mean((p - o) ** 2)
        b_nai = np.mean((base_tr[code] - o) ** 2)
        gain = 1 - b_mod / b_nai if b_nai > 0 else 0
        lignes.append(f"| {g} | {t} | {lib} | {p.mean():.1%} | {o.mean():.1%} | {gain:+.1%} |")

    # --- fiabilité par famille et tranche --------------------------------------------
    preds, obs, fam = np.array(preds), np.array(obs, float), np.array(fam)
    fiab = {}
    lignes.append("\n## 2. Fiabilité : probabilité annoncée vs fréquence réelle, par famille\n")
    for f in sorted(set(fam)):
        m = fam == f
        tab = []
        lignes.append(f"\n### {f}\n\n| Annoncé | Sélections | Réel |\n|---|---|---|")
        for lo_, hi in zip(BORNES[:-1], BORNES[1:]):
            s = m & (preds >= lo_) & (preds < hi)
            if s.sum() < 30:
                continue
            tab.append({"de": float(lo_), "a": float(min(hi, 1)), "n": int(s.sum()),
                        "annonce": float(preds[s].mean()), "reel": float(obs[s].mean())})
            lignes.append(f"| {lo_:.0%}–{min(hi, 1):.0%} | {s.sum()} | {obs[s].mean():.1%} (annoncé {preds[s].mean():.1%}) |")
        fiab[f] = tab

    # --- combinés aléatoires multi-matchs ------------------------------------------
    rng = np.random.default_rng(0)
    simples = [c_ for _, _, c_, _ in codes if composante(c_) == "buts"]
    te_idx = list(range(len(te)))
    combis = []
    for _ in range(20000):
        nb = int(rng.integers(2, 7))
        ms = rng.choice(te_idx, nb, replace=False)
        p_tot, ok = 1.0, True
        for mi in ms:
            J = jum[mi]
            for _ in range(20):  # sélection « raisonnable » (probabilité 40–95 %)
                code = simples[rng.integers(len(simples))]
                p = J.proba(code)
                if 0.4 <= p <= 0.95:
                    break
            p_tot *= p
            ok &= resultat(code, te.iloc[mi])
        combis.append((p_tot, ok))
    cp, co = np.array(combis, float).T
    lignes.append("\n## 3. Combinés de 2 à 6 matchs (20 000 combinés aléatoires)\n")
    lignes.append("| Probabilité annoncée | Combinés | Taux de réussite réel |\n|---|---|---|")
    tab = []
    for lo_, hi in zip([0, .05, .1, .2, .3, .4, .5, .6, .7], [.05, .1, .2, .3, .4, .5, .6, .7, 1.0001]):
        s = (cp >= lo_) & (cp < hi)
        if s.sum() < 30:
            continue
        tab.append({"de": lo_, "a": min(hi, 1), "n": int(s.sum()), "annonce": float(cp[s].mean()), "reel": float(co[s].mean())})
        lignes.append(f"| {lo_:.0%}–{min(hi, 1):.0%} (moy. {cp[s].mean():.1%}) | {s.sum()} | **{co[s].mean():.1%}** |")
    fiab["combines_multi"] = tab

    SORTIE_JSON.write_text(json.dumps({"parametres": params, "familles": fiab}, indent=1), encoding="utf-8")
    cfg["jumeau"] = params
    (RACINE / "data" / "modele.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    SORTIE_MD.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print("\n".join(lignes[:6]))
    print("\n".join(l for l in lignes if l.startswith("| ") and ("%" in l))[:200])


if __name__ == "__main__":
    main()
