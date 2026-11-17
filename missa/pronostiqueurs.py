"""Évaluation des pronostiqueurs par la valeur obtenue contre la cote de clôture (CLV).

Principes (Buchdahl, football-data.co.uk) :
- on ne juge JAMAIS sur le profit, le taux de réussite ou les séries (trop de hasard) ;
- CLV d'un pronostic = cote_conseillée / cote_juste_de_clôture − 1  (marge retirée) ;
- le t-score du CLV persiste dans le temps (R² ≈ 0,5 entre 1re et 2de moitié, pente ≈ 0,7),
  les profits non ;
- minimum ~50 pronostics, pronostic horodaté AVANT le match, jamais modifié.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

MIN_PRONOS = 50
PERSISTANCE = 0.7  # talent futur ≈ 0,7 × talent passé (régression vers la moyenne)


@dataclass
class Pronostic:
    pronostiqueur: str
    match_id: str
    issue: int                 # 0 = 1, 1 = N, 2 = 2
    cote_conseillee: float
    cote_juste_cloture: float  # cote de clôture sans marge pour la même issue
    horodatage_avant_match: bool = True

    @property
    def clv(self) -> float:
        return self.cote_conseillee / self.cote_juste_cloture - 1.0


def evaluer(pronos: list[Pronostic]) -> dict:
    """Note d'un pronostiqueur à partir de ses pronostics valides."""
    valides = [p for p in pronos if p.horodatage_avant_match]
    clv = np.array([p.clv for p in valides])
    n = len(clv)
    if n < 2:
        return {"n": n, "clv_moyen": float(clv.mean()) if n else 0.0, "t_score": 0.0,
                "fiable": False, "poids": 0.0, "pct_battu": float("nan")}
    t = float(clv.mean() / (clv.std(ddof=1) / np.sqrt(n))) if clv.std(ddof=1) > 0 else 0.0
    p_battu = float(np.mean(clv > 0))
    # test binomial : proportion de pronostics battant la clôture vs 50 %
    p_val = float(stats.binomtest(int(np.sum(clv > 0)), n, 0.5, alternative="greater").pvalue)
    fiable = n >= MIN_PRONOS
    talent = PERSISTANCE * t if fiable else PERSISTANCE * t * n / MIN_PRONOS
    return {"n": n, "clv_moyen": float(clv.mean()), "t_score": t, "pct_battu": p_battu,
            "p_valeur_battu": p_val, "fiable": fiable, "talent_estime": talent,
            "poids": poids_depuis_talent(talent)}


def poids_depuis_talent(talent: float) -> float:
    """Poids dans la combinaison : 0 sans preuve, croissant avec le t-score (plafonné).
    Un talent très négatif donne un poids négatif (signal inverse)."""
    return float(np.clip(talent / 10.0, -0.3, 0.3)) if abs(talent) >= 2.0 else 0.0


def signal_consensus(pronos_match: list[tuple[int, float]]) -> np.ndarray:
    """Ajustement 1X2 à partir des pronostics pondérés [(issue, poids)] sur un match.
    Renvoie un vecteur de log-ajustement à ajouter aux log-probabilités."""
    adj = np.zeros(3)
    for issue, poids in pronos_match:
        adj[issue] += poids
    return adj - adj.mean()
