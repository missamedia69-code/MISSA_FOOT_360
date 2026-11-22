"""Expériences : quelles techniques avancées améliorent réellement le moteur ?

Données : 5 grands championnats, entraînement 2019/20–2022/23, test 2023/24–2026/27 (jamais vu).
Toutes les variables sont calculées AVANT chaque match (aucune fuite d'information).

E1  Pi-ratings (Constantinou & Fenton 2013) -> 1X2 par logit ordonné
E2  Notes de forme : moyennes exponentielles des buts et des TIRS CADRÉS pour/contre (à la Wheatcroft)
E3  Gradient boosting (approche gagnante des Soccer Prediction Challenges) :
      a) sans les cotes (comparable à la littérature)   b) avec les cotes
E4  Combinaison marché + modèles (pool logarithmique appris) avec les nouvelles sources
E5  Scores exacts : correction Dixon-Coles (ρ) vs Poisson indépendant, après calage sur le marché
E6  Recalibrage du marché (biais favori/outsider résiduel)
Résultats : docs/recherche/04_experiences.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402

from missa import evaluation  # noqa: E402
from missa.backtest import LogitOrdonne, trio  # noqa: E402
from missa.combinaison import PoolLogarithmique  # noqa: E402
from missa.dixon_coles import matrice_scores  # noqa: E402
from missa.selections import ajuster_matrice  # noqa: E402

ENTRAINEMENT = ["1920", "2021", "2122", "2223"]
TEST = ["2324", "2425", "2526", "2627"]
SORTIE = RACINE / "docs" / "recherche" / "04_experiences.md"


# ----------------------------------------------------------------------------- variables
def pi_attendu(r: float) -> float:
    return np.sign(r) * (10 ** (abs(r) / 3) - 1)


def ajouter_variables(df: pd.DataFrame, lam: float = 0.06, gam: float = 0.6, demi_vie: float = 8.0) -> pd.DataFrame:
    """Pi-ratings et moyennes exponentielles (buts, tirs cadrés), calculés avant chaque match."""
    a = 1 - 0.5 ** (1 / demi_vie)
    out = {k: np.full(len(df), np.nan) for k in (
        "pi_e", "pi_hh", "pi_aa", "f_bp_d", "f_bc_d", "f_cp_d", "f_cc_d", "f_bp_e", "f_bc_e", "f_cp_e", "f_cc_e",
        "repos_d", "repos_e", "n_d", "n_e")}
    for champ, g in df.groupby("championnat"):
        pi: dict = {}
        forme: dict = {}
        dernier: dict = {}
        for idx, r in g.sort_values("date").iterrows():
            k = df.index.get_loc(idx)
            h, w = r.domicile, r.exterieur
            hh, ha = pi.get(h, (0.0, 0.0))
            ah, aa = pi.get(w, (0.0, 0.0))
            e = pi_attendu(hh) - pi_attendu(aa)
            out["pi_e"][k], out["pi_hh"][k], out["pi_aa"][k] = e, hh, aa
            for t, suf in ((h, "d"), (w, "e")):
                f = forme.get(t)
                if f is not None:
                    out[f"f_bp_{suf}"][k], out[f"f_bc_{suf}"][k], out[f"f_cp_{suf}"][k], out[f"f_cc_{suf}"][k], n = f
                    out[f"n_{suf}"][k] = n
                if t in dernier:
                    out[f"repos_{suf}"][k] = min((r.date - dernier[t]).days, 30)
            # --- mises à jour après le match ---
            diff = r.buts_dom - r.buts_ext
            err = abs(diff - e)
            wv = 3 * np.log10(1 + err)
            wh = wv if e < diff else -wv
            pi[h] = (hh + lam * wh, ha + lam * gam * wh)
            pi[w] = (ah + lam * gam * (-wh), aa + lam * (-wh))
            cd = r.cadres_dom if np.isfinite(r.cadres_dom) else np.nan
            ce = r.cadres_ext if np.isfinite(r.cadres_ext) else np.nan
            for t, bp, bc, cp, cc in ((h, r.buts_dom, r.buts_ext, cd, ce), (w, r.buts_ext, r.buts_dom, ce, cd)):
                f = forme.get(t)
                if f is None:
                    forme[t] = (bp, bc, cp, cc, 1)
                else:
                    nv = [x if not np.isfinite(y) else (1 - a) * x + a * y if np.isfinite(x) else y
                          for x, y in zip(f[:4], (bp, bc, cp, cc))]
                    forme[t] = (*nv, f[4] + 1)
                dernier[t] = r.date
    for k, v in out.items():
        df[k] = v
    return df


# ----------------------------------------------------------------------------- outils
def resume(nom, p, y):
    r = evaluation.resume(p, y)
    return {"nom": nom, "rps": r["rps"], "log_loss": r["log_loss"], "brier": r["brier"]}


def ic_diff(p_a, p_b, y, n=2000, seed=0):
    """Intervalle à 95 % (bootstrap) de la différence de log-loss A − B (négatif = A meilleur)."""
    y = np.asarray(y, int)
    la = -np.log(np.clip(p_a[np.arange(len(y)), y], 1e-12, 1))
    lb = -np.log(np.clip(p_b[np.arange(len(y)), y], 1e-12, 1))
    d = la - lb
    rng = np.random.default_rng(seed)
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return float(d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    df = pd.read_pickle(RACINE / "data" / "cache" / "prepare_jumeau.pkl").reset_index(drop=True)
    df = ajouter_variables(df)
    df = df.dropna(subset=["dc_H", "marche_ouv_H", "elo_ecart", "pi_e", "f_bp_d", "f_bp_e"])
    df = df[(df.n_d >= 5) & (df.n_e >= 5)]
    tr, te = df[df.saison.isin(ENTRAINEMENT)].copy(), df[df.saison.isin(TEST)].copy()
    ytr, yte = tr.resultat.to_numpy(), te.resultat.to_numpy()
    lignes = ["# Expériences : techniques avancées testées sur nos données\n",
              f"Entraînement : {len(tr)} matchs (2019/20–2022/23) — test : {len(te)} matchs (2023/24–2026/27, jamais vus).\n",
              "Plus bas = mieux pour RPS, log-loss et Brier. La référence à battre est le **marché avant clôture**.\n"]
    res = []
    marche_tr, marche_te = trio(tr, "marche_ouv"), trio(te, "marche_ouv")
    res.append(resume("Marché avant clôture (référence)", marche_te, yte))
    res.append(resume("Marché à la clôture (plafond)", trio(te, "marche_clo"), yte))
    res.append(resume("Dixon-Coles", trio(te, "dc"), yte))
    lo_elo = LogitOrdonne().ajuster(tr.elo_ecart, ytr)
    res.append(resume("Elo", lo_elo.predire(te.elo_ecart), yte))

    # E1 pi-ratings
    lo_pi = LogitOrdonne().ajuster(tr.pi_e * 100, ytr)
    p_pi_tr, p_pi_te = lo_pi.predire(tr.pi_e * 100), lo_pi.predire(te.pi_e * 100)
    res.append(resume("E1 Pi-ratings", p_pi_te, yte))

    # E2/E3 gradient boosting
    forme = ["f_bp_d", "f_bc_d", "f_cp_d", "f_cc_d", "f_bp_e", "f_bc_e", "f_cp_e", "f_cc_e", "repos_d", "repos_e"]
    sans = ["pi_e", "pi_hh", "pi_aa", "elo_ecart", "dc_H", "dc_D", "dc_A", "dc_lambda", "dc_mu"] + forme
    avec = sans + ["marche_ouv_H", "marche_ouv_D", "marche_ouv_A"]
    gb = {}
    for nom, cols in (("E3a Boosting sans cotes (pi, Elo, DC, forme, tirs cadrés)", sans),
                      ("E3b Boosting avec cotes", avec)):
        m = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.03, max_depth=3, l2_regularization=1.0,
                                           min_samples_leaf=80, early_stopping=True, validation_fraction=0.2,
                                           random_state=0)
        m.fit(tr[cols], ytr)
        gb[nom] = (m.predict_proba(tr[cols]), m.predict_proba(te[cols]))
        res.append(resume(nom, gb[nom][1], yte))
    # E2 : forme seule (tirs cadrés) via boosting
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.03, max_depth=3, min_samples_leaf=80,
                                       early_stopping=True, random_state=0).fit(tr[forme], ytr)
    p_forme_tr, p_forme_te = m.predict_proba(tr[forme]), m.predict_proba(te[forme])
    res.append(resume("E2 Forme seule (buts + tirs cadrés, moyennes exponentielles)", p_forme_te, yte))

    # E6 recalibrage du marché seul
    pool_m = PoolLogarithmique(["marche"]).ajuster({"marche": marche_tr}, ytr)
    p_cal = pool_m.predire({"marche": marche_te})
    res.append(resume("E6 Marché recalibré", p_cal, yte))

    # E4 combinaisons — prédictions d'entraînement HORS ÉCHANTILLON (une saison prédite par un
    # modèle entraîné sur les autres), sinon la combinaison surestime les modèles flexibles.
    def hors_echantillon(fabrique, cols):
        p = np.zeros((len(tr), 3))
        for s_ in ENTRAINEMENT:
            m_ = tr.saison == s_
            mod = fabrique().fit(tr.loc[~m_, cols], ytr[~m_.to_numpy()])
            p[m_.to_numpy()] = mod.predict_proba(tr.loc[m_, cols])
        return p

    def gbm():
        return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.03, max_depth=3, l2_regularization=1.0,
                                              min_samples_leaf=80, early_stopping=True, random_state=0)
    p_forme_tr = hors_echantillon(gbm, forme)
    p_gb_tr = hors_echantillon(gbm, sans)
    p_pi_tr = np.zeros((len(tr), 3))
    for s_ in ENTRAINEMENT:
        m_ = (tr.saison == s_).to_numpy()
        lo_ = LogitOrdonne().ajuster(tr.pi_e[~m_] * 100, ytr[~m_])
        p_pi_tr[m_] = lo_.predire(tr.pi_e[m_] * 100)
    srcs_tr = {"marche": marche_tr, "dc": trio(tr, "dc"), "elo": lo_elo.predire(tr.elo_ecart), "pi": p_pi_tr,
               "forme": p_forme_tr, "gb_sans": p_gb_tr}
    srcs_te = {"marche": marche_te, "dc": trio(te, "dc"), "elo": lo_elo.predire(te.elo_ecart), "pi": p_pi_te,
               "forme": p_forme_te, "gb_sans": gb["E3a Boosting sans cotes (pi, Elo, DC, forme, tirs cadrés)"][1]}
    poids = {}
    for nom, sources in (("E4a Pool actuel (marché + DC + Elo)", ["marche", "dc", "elo"]),
                         ("E4b Pool + pi-ratings + forme", ["marche", "dc", "elo", "pi", "forme"]),
                         ("E4c Pool marché + boosting sans cotes", ["marche", "gb_sans"]),
                         ("E4d Pool marché + DC + Elo + forme (tirs cadrés)", ["marche", "dc", "elo", "forme"])):
        pool = PoolLogarithmique(sources).ajuster({s: srcs_tr[s] for s in sources}, ytr)
        p = pool.predire({s: srcs_te[s] for s in sources})
        poids[nom] = pool.resume()
        res.append(resume(nom, p, yte) | {"p": p})

    lignes.append("\n## 1. Résultat 1X2\n")
    lignes.append("| Modèle | RPS | Log-loss | Brier |\n|---|---|---|---|")
    for r in res:
        lignes.append(f"| {r['nom']} | {r['rps']:.5f} | {r['log_loss']:.5f} | {r['brier']:.5f} |")
    lignes.append("\nPoids appris dans les combinaisons : " + "; ".join(f"{k} → {v}" for k, v in poids.items()))

    lignes.append("\n## 2. Gain par rapport au marché (log-loss, intervalle de confiance 95 % par bootstrap)\n")
    lignes.append("Négatif = meilleur que le marché. Si l'intervalle contient 0, le gain n'est pas prouvé.\n")
    lignes.append("| Modèle | Différence | IC 95 % |\n|---|---|---|")
    for r in res:
        if "p" in r or r["nom"].startswith(("E3b", "E6")):
            p = r.get("p")
            if p is None:
                p = gb["E3b Boosting avec cotes"][1] if r["nom"].startswith("E3b") else p_cal
            d, lo_, hi_ = ic_diff(p, marche_te, yte)
            lignes.append(f"| {r['nom']} | {d:+.5f} | [{lo_:+.5f} ; {hi_:+.5f}] |")

    # E5 scores exacts
    combi = res[[r["nom"] for r in res].index("E4a Pool actuel (marché + DC + Elo)")]["p"]
    p_ou = te["marche_ouv_plus25"].fillna(te["dc_plus25"]).to_numpy(float)
    ll = {"Dixon-Coles (ρ estimé)": [], "Poisson indépendant (ρ = 0)": []}
    for n_, (_, r) in enumerate(te.iterrows()):
        i, j = min(int(r.buts_dom), 9), min(int(r.buts_ext), 9)
        for nom, rho in (("Dixon-Coles (ρ estimé)", r.dc_rho), ("Poisson indépendant (ρ = 0)", 0.0)):
            P = ajuster_matrice(matrice_scores(r.dc_lambda, r.dc_mu, rho), combi[n_], p_ou[n_])
            ll[nom].append(-np.log(max(P[i, j], 1e-12)))
    lignes.append("\n## 3. Scores exacts (log-loss du score final, après calage sur le marché)\n")
    for nom, v in ll.items():
        lignes.append(f"- {nom} : {np.mean(v):.5f}")
    d = np.array(ll["Dixon-Coles (ρ estimé)"]) - np.array(ll["Poisson indépendant (ρ = 0)"])
    rng = np.random.default_rng(1)
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
    lignes.append(f"- Différence Dixon-Coles − Poisson : {d.mean():+.5f} (IC 95 % [{np.percentile(bs, 2.5):+.5f} ; {np.percentile(bs, 97.5):+.5f}])")

    SORTIE.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
