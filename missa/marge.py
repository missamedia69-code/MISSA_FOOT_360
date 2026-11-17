"""Retrait de la marge du bookmaker : cotes -> probabilités « justes ».

Méthodes (cf. docs/recherche) :
- egale            : normalisation simple (biaisée, sert de référence)
- proportionnelle  : marge proportionnelle à la cote (Buchdahl)
- puissance        : fonction logarithmique / « power » (Buchdahl)
- odds_ratio       : même odds ratio pour chaque issue (Cheung)
- shin             : modèle de Shin (meilleur selon Štrumbelj 2014)
- abrams           : formule fermée pour les marchés à 2 issues (Abrams 2022)
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

METHODES = ("egale", "proportionnelle", "puissance", "odds_ratio", "shin")


def marge(cotes) -> float:
    """Marge M = somme(1/cote) - 1."""
    return float(np.sum(1.0 / np.asarray(cotes, float)) - 1.0)


def egale(cotes) -> np.ndarray:
    inv = 1.0 / np.asarray(cotes, float)
    return inv / inv.sum()


def proportionnelle(cotes) -> np.ndarray:
    """Cote juste = n·O / (n − M·O) ; renormalisée pour sommer à 1."""
    o = np.asarray(cotes, float)
    n, m = len(o), marge(o)
    juste = n * o / (n - m * o)
    if np.any(juste <= 0):  # marge trop forte pour une cote très longue
        return puissance(o)
    p = 1.0 / juste
    return p / p.sum()


def puissance(cotes) -> np.ndarray:
    """p_i = (1/O_i)^k avec k tel que Σ p_i = 1."""
    inv = 1.0 / np.asarray(cotes, float)
    if abs(inv.sum() - 1.0) < 1e-12:
        return inv.copy()
    k = brentq(lambda k: np.sum(inv ** k) - 1.0, 0.01, 100.0)
    return inv ** k


def odds_ratio(cotes) -> np.ndarray:
    """Probabilité implicite x_i liée à la vraie p_i par un odds ratio c commun."""
    x = 1.0 / np.asarray(cotes, float)

    def p_de(c):
        return x / (c - c * x + x)  # inverse de OR(x, p) = c

    if abs(x.sum() - 1.0) < 1e-12:
        return x.copy()
    c = brentq(lambda c: p_de(c).sum() - 1.0, 1e-6, 1e6)
    return p_de(c)


def shin(cotes) -> np.ndarray:
    """Modèle de Shin : z = proportion d'informés, résolu pour Σ π = 1."""
    o = 1.0 / np.asarray(cotes, float)
    s = o.sum()
    if s <= 1.0:
        return o / s

    def pi(z):
        return (np.sqrt(z * z + 4 * (1 - z) * o * o / s) - z) / (2 * (1 - z))

    z = brentq(lambda z: pi(z).sum() - 1.0, 0.0, 0.999)
    p = pi(z)
    return p / p.sum()


def abrams(cote_a: float, cote_b: float) -> tuple[float, float]:
    """Marché à 2 issues : cotes justes (formule d'Abrams). Renvoie (cote_juste_a, cote_juste_b)."""
    fav_premier = cote_a <= cote_b
    cf, cl = (cote_a, cote_b) if fav_premier else (cote_b, cote_a)
    p, q = 1.0 / cf, 1.0 / cl
    if p + q <= 1.0:
        juste_l, juste_f = cl, cf
    else:
        juste_l = np.log((1 - p) / q) / np.log((1 - q) / p) + 1.0
        juste_f = juste_l / (juste_l - 1.0)
    return (juste_f, juste_l) if fav_premier else (juste_l, juste_f)


def probabilites(cotes, methode: str = "puissance") -> np.ndarray:
    """Point d'entrée : cotes (2 ou 3 issues) -> probabilités justes."""
    cotes = np.asarray(cotes, float)
    if np.any(~np.isfinite(cotes)) or np.any(cotes <= 1.0):
        return np.full(len(cotes), np.nan)
    if methode == "abrams":
        if len(cotes) != 2:
            raise ValueError("abrams : marché à 2 issues uniquement")
        a, b = abrams(*cotes)
        return np.array([1 / a, 1 / b]) / (1 / a + 1 / b)
    return {"egale": egale, "proportionnelle": proportionnelle, "puissance": puissance,
            "odds_ratio": odds_ratio, "shin": shin}[methode](cotes)
