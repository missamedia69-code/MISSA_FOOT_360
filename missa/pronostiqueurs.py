"""Pronostiqueurs : notation par la valeur obtenue contre la cote de clôture (CLV) et
intégration de leurs pronostics dans les probabilités du moteur.

Principes (Buchdahl, football-data.co.uk) :
- on ne juge JAMAIS sur le profit, le taux de réussite ou les séries (trop de hasard) ;
- CLV d'un pronostic = cote_conseillée × proba_juste_de_clôture − 1  (marge retirée) ;
- le t-score du CLV persiste dans le temps (pente ≈ 0,7 entre 1re et 2de moitié), les profits non ;
- minimum ~50 pronostics, pronostic horodaté AVANT le match, jamais modifié.

Intégration : un pronostiqueur au talent prouvé fait monter (ou, s'il est prouvé mauvais,
descendre) la probabilité de sa sélection d'un pourcentage égal à son avantage attendu.
Sans preuve statistique : ajustement nul (son avis est affiché mais ne pèse pas).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from .selections import masque

MIN_PRONOS = 50
PERSISTANCE = 0.7      # talent futur ≈ 0,7 × talent passé (régression vers la moyenne)
T_MIN = 2.0            # t-score minimal pour considérer le talent (ou l'incompétence) prouvé
AJUST_MAX = 0.10       # ajustement maximal par pronostiqueur (±10 % relatif)
AJUST_TOTAL_MAX = 0.15 # ajustement cumulé maximal sur une sélection


@dataclass
class Pronostic:
    pronostiqueur: str
    match_id: str
    selection: str             # code de selections.SELECTIONS (« 1 », « plus_2.5 »…)
    cote_conseillee: float
    proba_juste_cloture: float | None = None  # renseignée après le coup d'envoi
    horodatage_avant_match: bool = True

    @property
    def clv(self) -> float | None:
        if self.proba_juste_cloture is None:
            return None
        return self.cote_conseillee * self.proba_juste_cloture - 1.0


def evaluer(pronos: list[Pronostic]) -> dict:
    """Note d'un pronostiqueur à partir de ses pronostics clôturés et valides."""
    clv = np.array([p.clv for p in pronos if p.horodatage_avant_match and p.clv is not None])
    n = len(clv)
    base = {"n": n, "clv_moyen": float(clv.mean()) if n else 0.0, "t_score": 0.0,
            "pct_battu": float(np.mean(clv > 0)) if n else None, "p_valeur": None,
            "fiable": False, "ajustement": 0.0, "statut": "Pas encore de données"}
    if n < 2 or clv.std(ddof=1) == 0:
        return base
    t = float(clv.mean() / (clv.std(ddof=1) / np.sqrt(n)))
    p_val = float(stats.binomtest(int(np.sum(clv > 0)), n, 0.5, alternative="greater").pvalue)
    fiable = n >= MIN_PRONOS
    ajust = ajustement_depuis(clv.mean(), t, fiable)
    if not fiable:
        statut = f"En observation ({n}/{MIN_PRONOS} pronostics)"
    elif t >= T_MIN:
        statut = "Talent prouvé : bat la cote de clôture"
    elif t <= -T_MIN:
        statut = "Fait systématiquement moins bien que le marché"
    else:
        statut = "Pas de différence prouvée avec le marché"
    return base | {"t_score": t, "p_valeur": p_val, "fiable": fiable, "ajustement": ajust,
                   "statut": statut}


def ajustement_depuis(clv_moyen: float, t_score: float, fiable: bool) -> float:
    """Ajustement relatif appliqué aux probabilités des sélections de ce pronostiqueur."""
    if not fiable or abs(t_score) < T_MIN:
        return 0.0
    return float(np.clip(PERSISTANCE * clv_moyen, -AJUST_MAX, AJUST_MAX))


def ajuster_matrice(P: np.ndarray, avis: list[tuple[str, float]]) -> np.ndarray:
    """Applique les avis [(sélection, ajustement relatif)] à la matrice des scores.

    Les cases du score compatibles avec la sélection sont multipliées par (1 + ajustement),
    puis la matrice est renormalisée. Ajustement cumulé plafonné par sélection."""
    P = np.asarray(P, float).copy()
    cumul: dict[str, float] = {}
    for sel, a in avis:
        cumul[sel] = cumul.get(sel, 0.0) + a
    for sel, a in cumul.items():
        a = float(np.clip(a, -AJUST_TOTAL_MAX, AJUST_TOTAL_MAX))
        if a != 0:
            P[masque(sel, P.shape[0])] *= 1 + a
    return P / P.sum()
