"""Décision : valeur attendue (EV), correction selon le délai avant le match, mise.

Rétention de la value jusqu'à la clôture (ValueBetFactory / football-data, 2026) :
< 1 h ≈ 70–99 % ; 1–6 h ≈ 40–94 % ; 6–24 h ≈ 12–51 % ; > 24 h ≈ 0–26 %.
On applique des valeurs prudentes (bas de fourchette, marchés de liquidité moyenne).
"""
from __future__ import annotations

RETENTION = ((1, 0.70), (6, 0.45), (24, 0.25), (float("inf"), 0.10))


def retention(heures_avant_match: float) -> float:
    for seuil, r in RETENTION:
        if heures_avant_match < seuil:
            return r
    return RETENTION[-1][1]


def valeur_attendue(proba: float, cote: float) -> float:
    """EV brute = p × cote − 1."""
    return proba * cote - 1.0


def valeur_corrigee(proba: float, cote: float, heures_avant_match: float) -> float:
    ev = valeur_attendue(proba, cote)
    return ev * retention(heures_avant_match) if ev > 0 else ev


def kelly_fractionnaire(proba: float, cote: float, fraction: float = 0.25,
                        plafond: float = 0.02) -> float:
    """Part de bankroll : Kelly × fraction, plafonnée (Kelly plein est trop risqué)."""
    b = cote - 1.0
    f = (proba * cote - 1.0) / b if b > 0 else 0.0
    return max(0.0, min(plafond, f * fraction))


def clv(cote_prise: float, cote_juste_cloture: float) -> float:
    return cote_prise / cote_juste_cloture - 1.0
