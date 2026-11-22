"""Forme récente des équipes : moyennes exponentielles des buts et des TIRS CADRÉS pour/contre.

C'est la seule source testée qui améliore le marché de façon prouvée (docs/recherche/05).
Les moyennes sont calculées AVANT chaque match (aucune fuite d'information).
Le modèle qui transforme ces variables en probabilités 1X2 est une régression logistique
multinomiale (coefficients dans data/modele.json, portables et sans dépendance).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEMI_VIE = 8.0  # en matchs
VARIABLES = ["f_bp_d", "f_bc_d", "f_cp_d", "f_cc_d", "f_bp_e", "f_bc_e", "f_cp_e", "f_cc_e", "repos_d", "repos_e"]
MIN_MATCHS = 5


class EtatForme:
    """Moyennes exponentielles par équipe, mises à jour match après match."""

    def __init__(self, demi_vie: float = DEMI_VIE):
        self.a = 1 - 0.5 ** (1 / demi_vie)
        self.forme: dict = {}
        self.dernier: dict = {}

    def variables(self, dom: str, ext: str, date: pd.Timestamp) -> dict | None:
        """Variables avant le match ; None si une équipe a moins de MIN_MATCHS matchs ou pas de tirs."""
        out = {}
        for t, s in ((dom, "d"), (ext, "e")):
            f = self.forme.get(t)
            if f is None or f[4] < MIN_MATCHS or not np.isfinite(f[2]) or not np.isfinite(f[3]):
                return None
            out[f"f_bp_{s}"], out[f"f_bc_{s}"], out[f"f_cp_{s}"], out[f"f_cc_{s}"] = f[:4]
            out[f"repos_{s}"] = min((date - self.dernier[t]).days, 30) if t in self.dernier else 7
        return out

    def mettre_a_jour(self, dom, ext, buts_dom, buts_ext, cadres_dom, cadres_ext, date) -> None:
        cd = cadres_dom if cadres_dom is not None and np.isfinite(cadres_dom) else np.nan
        ce = cadres_ext if cadres_ext is not None and np.isfinite(cadres_ext) else np.nan
        for t, bp, bc, cp, cc in ((dom, buts_dom, buts_ext, cd, ce), (ext, buts_ext, buts_dom, ce, cd)):
            f = self.forme.get(t)
            if f is None:
                self.forme[t] = (bp, bc, cp, cc, 1)
            else:
                nv = [y if not np.isfinite(x) else (x if not np.isfinite(y) else (1 - self.a) * x + self.a * y)
                      for x, y in zip(f[:4], (bp, bc, cp, cc))]
                self.forme[t] = (*nv, f[4] + 1)
            self.dernier[t] = date


def ajouter(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les variables de forme à un historique (par championnat, dans l'ordre des dates)."""
    df = df.copy()
    for v in VARIABLES:
        df[v] = np.nan
    for _, g in df.groupby("championnat"):
        etat = EtatForme()
        for idx, r in g.sort_values("date").iterrows():
            v = etat.variables(r.domicile, r.exterieur, r.date)
            if v:
                for k, x in v.items():
                    df.at[idx, k] = x
            etat.mettre_a_jour(r.domicile, r.exterieur, r.buts_dom, r.buts_ext,
                               r.get("cadres_dom"), r.get("cadres_ext"), r.date)
    return df


class LogistiqueForme:
    """Régression logistique multinomiale (descente de gradient, régularisation L2)."""

    def __init__(self, l2: float = 1.0):
        self.l2 = l2

    def ajuster(self, X: np.ndarray, y: np.ndarray, iterations: int = 3000) -> "LogistiqueForme":
        from scipy.optimize import minimize
        X = np.asarray(X, float)
        self.moy, self.ect = X.mean(0), X.std(0) + 1e-9
        Z = (X - self.moy) / self.ect
        n, k = Z.shape
        Y = np.eye(3)[np.asarray(y, int)]

        def f(t):
            W, b = t[: k * 3].reshape(k, 3), t[k * 3:]
            S = Z @ W + b
            S -= S.max(1, keepdims=True)
            P = np.exp(S)
            P /= P.sum(1, keepdims=True)
            loss = -np.mean(np.sum(Y * np.log(np.clip(P, 1e-12, 1)), 1)) + self.l2 / n * np.sum(W ** 2)
            G = (P - Y) / n
            return loss, np.r_[(Z.T @ G + 2 * self.l2 / n * W).ravel(), G.sum(0)]

        r = minimize(f, np.zeros(k * 3 + 3), jac=True, method="L-BFGS-B", options={"maxiter": iterations})
        self.W, self.b = r.x[: k * 3].reshape(k, 3), r.x[k * 3:]
        return self

    def predict_proba(self, X) -> np.ndarray:
        Z = (np.asarray(X, float) - self.moy) / self.ect
        S = Z @ self.W + self.b
        S -= S.max(1, keepdims=True)
        P = np.exp(S)
        return P / P.sum(1, keepdims=True)

    def vers_json(self) -> dict:
        return {"moy": self.moy.tolist(), "ect": self.ect.tolist(), "W": self.W.tolist(), "b": self.b.tolist(),
                "variables": VARIABLES}

    @classmethod
    def depuis_json(cls, d: dict) -> "LogistiqueForme":
        m = cls()
        m.moy, m.ect, m.W, m.b = (np.array(d[k]) for k in ("moy", "ect", "W", "b"))
        return m
