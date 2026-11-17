"""Backtest « marche en avant » : chaque match est prédit uniquement avec les informations
disponibles AVANT lui (pas de fuite d'information).

Sources produites pour chaque match :
- marche_ouv : probabilités justes des cotes AVANT clôture (ce qu'on connaît au moment de parier)
- marche_clo : probabilités justes des cotes de CLÔTURE (référence de vérité, jamais utilisée pour prédire)
- dixon_coles : modèle de buts
- elo : classement Elo converti en 1X2 par régression logit ordonnée
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

from . import marge
from .dixon_coles import DixonColes
from .elo import Elo


def probas_marche(df: pd.DataFrame, prefixe: str, methode: str = "puissance") -> np.ndarray:
    cotes = df[[f"{prefixe}_H", f"{prefixe}_D", f"{prefixe}_A"]].to_numpy(float)
    return np.array([marge.probabilites(c, methode) for c in cotes])


def ajouter_dixon_coles(df: pd.DataFrame, xi: float = 0.0019, jours_refit: int = 7,
                        historique_jours: int = 3 * 365) -> pd.DataFrame:
    df = df.copy()
    for col in ("dc_H", "dc_D", "dc_A", "dc_lambda", "dc_mu", "dc_plus25", "dc_btts"):
        df[col] = np.nan
    for champ, g in df.groupby("championnat"):
        dates = g["date"].sort_values().unique()
        modele, derniere = None, None
        for d in dates:
            d = pd.Timestamp(d)
            if modele is None or (d - derniere).days >= jours_refit:
                hist = g[(g["date"] < d) & (g["date"] >= d - pd.Timedelta(days=historique_jours))]
                if len(hist) < 200:
                    continue
                modele, derniere = DixonColes(xi=xi).ajuster(hist, d), d
            for i in g.index[g["date"] == d]:
                pr = modele.predire(df.at[i, "domicile"], df.at[i, "exterieur"])
                if pr is None:
                    continue
                df.loc[i, ["dc_H", "dc_D", "dc_A", "dc_lambda", "dc_mu", "dc_plus25", "dc_btts"]] = [
                    pr["1"], pr["N"], pr["2"], pr["lambda"], pr["mu"], pr["plus_2.5"], pr["btts_oui"]]
    return df


def ajouter_elo(df: pd.DataFrame, k: float = 20.0, avantage: float = 70.0) -> pd.DataFrame:
    df = df.copy()
    df["elo_ecart"] = np.nan
    for champ, g in df.groupby("championnat"):
        elo = Elo(k=k, avantage_domicile=avantage)
        saison = None
        for i, r in g.iterrows():
            if r["saison"] != saison:
                saison = r["saison"]
                eq = set(g.loc[g["saison"] == saison, "domicile"])
                elo.nouvelle_saison(eq)
            df.at[i, "elo_ecart"] = elo.ecart(r["domicile"], r["exterieur"])
            elo.mettre_a_jour(r["domicile"], r["exterieur"], int(r["buts_dom"]), int(r["buts_ext"]))
    return df


class LogitOrdonne:
    """P(dom) / P(nul) / P(ext) en fonction d'une variable (écart Elo)."""

    def ajuster(self, x, y):
        x, y = np.asarray(x, float) / 100, np.asarray(y, int)

        def nll(t):
            b, c1, c2 = t[0], t[1], t[1] + np.exp(t[2])
            p = self._probas(x, b, c1, c2)
            return -np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)))

        r = minimize(nll, [0.3, -0.5, 0.0], method="Nelder-Mead")
        self.b, self.c1, self.c2 = r.x[0], r.x[1], r.x[1] + np.exp(r.x[2])
        return self

    @staticmethod
    def _probas(x, b, c1, c2):
        # variable latente : plus elle est haute, plus l'extérieur est favorisé
        p_dom = expit(c1 + b * x)
        p_dom_ou_nul = expit(c2 + b * x)
        return np.stack([p_dom, p_dom_ou_nul - p_dom, 1 - p_dom_ou_nul], axis=1)

    def predire(self, x):
        return self._probas(np.asarray(x, float) / 100, self.b, self.c1, self.c2)


def preparer(df: pd.DataFrame, methode_marge: str = "puissance") -> pd.DataFrame:
    df = ajouter_elo(ajouter_dixon_coles(df))
    for nom, pre in (("marche_ouv", "ouv"), ("marche_clo", "clo")):
        p = probas_marche(df, pre, methode_marge)
        df[[f"{nom}_H", f"{nom}_D", f"{nom}_A"]] = p
    return df


def trio(df: pd.DataFrame, nom: str) -> np.ndarray:
    return df[[f"{nom}_H", f"{nom}_D", f"{nom}_A"]].to_numpy(float)
