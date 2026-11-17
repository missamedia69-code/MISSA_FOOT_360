"""Modèle de Dixon-Coles (1997) avec pondération temporelle.

log λ = avantage_domicile + attaque[dom] + defense[ext]   (buts attendus à domicile)
log μ = attaque[ext] + defense[dom]                      (buts attendus à l'extérieur)
Correction τ des petits scores (0-0, 1-0, 0-1, 1-1) avec le paramètre ρ.
Poids d'un match = exp(−ξ · jours écoulés)  (ξ ≈ 0,0018–0,0023 / jour en Europe).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

XI_DEFAUT = 0.0019


@dataclass
class DixonColes:
    xi: float = XI_DEFAUT
    max_buts: int = 10
    penalite: float = 1e-3  # légère régularisation L2 (équipes avec peu de matchs)
    rho_fixe: float | None = None  # 0 pour des comptages sans correction (corners, cartons)
    equipes: list = field(default_factory=list)
    attaque: np.ndarray | None = None
    defense: np.ndarray | None = None
    domicile: float = 0.25
    rho: float = -0.1

    def ajuster(self, matchs: pd.DataFrame, date_ref: pd.Timestamp) -> "DixonColes":
        m = matchs[matchs["date"] < date_ref].dropna(subset=["buts_dom", "buts_ext"])
        self.equipes = sorted(set(m["domicile"]) | set(m["exterieur"]))
        idx = {e: i for i, e in enumerate(self.equipes)}
        n = len(self.equipes)
        h = m["domicile"].map(idx).to_numpy()
        a = m["exterieur"].map(idx).to_numpy()
        x = m["buts_dom"].to_numpy(float)
        y = m["buts_ext"].to_numpy(float)
        jours = (date_ref - m["date"]).dt.days.to_numpy(float)
        w = np.exp(-self.xi * jours)
        c00, c01 = (x == 0) & (y == 0), (x == 0) & (y == 1)
        c10, c11 = (x == 1) & (y == 0), (x == 1) & (y == 1)

        def nll(theta):
            att, dfn = theta[:n], theta[n:2 * n]
            hfa, rho = theta[2 * n], theta[2 * n + 1]
            ll = hfa + att[h] + dfn[a]
            lm = att[a] + dfn[h]
            lam, mu = np.exp(ll), np.exp(lm)
            tau = np.ones_like(lam)
            tau[c00] = 1 - lam[c00] * mu[c00] * rho
            tau[c01] = 1 + lam[c01] * rho
            tau[c10] = 1 + mu[c10] * rho
            tau[c11] = 1 - rho
            tau = np.maximum(tau, 1e-10)
            f = -np.sum(w * (np.log(tau) + x * ll - lam + y * lm - mu))
            # gradients
            g_ll = x - lam
            g_lm = y - mu
            g_rho = np.zeros_like(lam)
            t = tau
            g_ll[c00] += -lam[c00] * mu[c00] * rho / t[c00]
            g_lm[c00] += -lam[c00] * mu[c00] * rho / t[c00]
            g_rho[c00] = -lam[c00] * mu[c00] / t[c00]
            g_ll[c01] += lam[c01] * rho / t[c01]
            g_rho[c01] = lam[c01] / t[c01]
            g_lm[c10] += mu[c10] * rho / t[c10]
            g_rho[c10] = mu[c10] / t[c10]
            g_rho[c11] = -1 / t[c11]
            g_ll, g_lm, g_rho = -w * g_ll, -w * g_lm, -w * g_rho
            g = np.zeros_like(theta)
            np.add.at(g, h, g_ll)          # attaque domicile
            np.add.at(g, n + a, g_ll)      # défense extérieur
            np.add.at(g, a, g_lm)          # attaque extérieur
            np.add.at(g, n + h, g_lm)      # défense domicile
            g[2 * n] = g_ll.sum()
            g[2 * n + 1] = g_rho.sum()
            # contrainte somme(attaque) = 0 + régularisation
            s = att.sum()
            f += 10.0 * s * s + self.penalite * np.sum(theta[:2 * n] ** 2)
            g[:n] += 20.0 * s
            g[:2 * n] += 2 * self.penalite * theta[:2 * n]
            return f, g

        theta0 = np.zeros(2 * n + 2)
        theta0[2 * n], theta0[2 * n + 1] = 0.25, -0.05
        r = (self.rho_fixe, self.rho_fixe) if self.rho_fixe is not None else (-0.3, 0.3)
        theta0[2 * n + 1] = 0.0 if self.rho_fixe is not None else theta0[2 * n + 1]
        bornes = [(-3, 3)] * (2 * n) + [(-1, 1), r]
        res = minimize(nll, theta0, jac=True, method="L-BFGS-B", bounds=bornes)
        th = res.x
        self.attaque, self.defense = th[:n], th[n:2 * n]
        self.domicile, self.rho = th[2 * n], th[2 * n + 1]
        return self

    def buts_attendus(self, dom: str, ext: str) -> tuple[float, float] | None:
        try:
            i, j = self.equipes.index(dom), self.equipes.index(ext)
        except ValueError:
            return None  # équipe inconnue (promue sans historique)
        lam = np.exp(self.domicile + self.attaque[i] + self.defense[j])
        mu = np.exp(self.attaque[j] + self.defense[i])
        return float(lam), float(mu)

    def matrice_scores(self, lam: float, mu: float) -> np.ndarray:
        return matrice_scores(lam, mu, self.rho, self.max_buts)

    def predire(self, dom: str, ext: str) -> dict | None:
        ba = self.buts_attendus(dom, ext)
        if ba is None:
            return None
        return marches(self.matrice_scores(*ba)) | {"lambda": ba[0], "mu": ba[1]}


def matrice_scores(lam: float, mu: float, rho: float = 0.0, max_buts: int = 10) -> np.ndarray:
    k = np.arange(max_buts + 1)
    P = np.outer(poisson.pmf(k, lam), poisson.pmf(k, mu))
    P[0, 0] *= 1 - lam * mu * rho
    P[0, 1] *= 1 + lam * rho
    P[1, 0] *= 1 + mu * rho
    P[1, 1] *= 1 - rho
    return P / P.sum()


def marches(P: np.ndarray) -> dict:
    """Probabilités des principaux marchés à partir de la matrice des scores P[dom, ext]."""
    i, j = np.indices(P.shape)
    total = i + j
    return {
        "1": P[i > j].sum(), "N": P[i == j].sum(), "2": P[i < j].sum(),
        "plus_2.5": P[total >= 3].sum(), "moins_2.5": P[total <= 2].sum(),
        "btts_oui": P[(i > 0) & (j > 0)].sum(), "btts_non": P[(i == 0) | (j == 0)].sum(),
        "score_probable": tuple(int(v) for v in np.unravel_index(P.argmax(), P.shape)),
    }
