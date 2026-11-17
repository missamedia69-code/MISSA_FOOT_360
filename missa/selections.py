"""Sélections de paris et probabilité d'une combinaison (« combiné »).

Chaque sélection est une condition sur le score final (buts_dom = i, buts_ext = j).
- Sélections sur des matchs DIFFÉRENTS : probabilités multipliées (matchs indépendants).
- Plusieurs sélections sur le MÊME match : probabilité conjointe lue dans la matrice des scores
  (ex. « 1 » + « plus de 2,5 » n'est pas le produit des deux, car ils sont corrélés).

La matrice des scores de Dixon-Coles est d'abord ajustée (« raking ») pour reproduire exactement
les probabilités finales du moteur sur le 1X2 et le plus/moins 2,5.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# code -> (libellé, condition sur (i, j))
SELECTIONS = {
    "1": ("Victoire domicile", lambda i, j: i > j),
    "N": ("Match nul", lambda i, j: i == j),
    "2": ("Victoire extérieur", lambda i, j: i < j),
    "1N": ("Double chance 1N", lambda i, j: i >= j),
    "12": ("Double chance 12", lambda i, j: i != j),
    "N2": ("Double chance N2", lambda i, j: i <= j),
    "plus_1.5": ("Plus de 1,5 but", lambda i, j: i + j >= 2),
    "moins_1.5": ("Moins de 1,5 but", lambda i, j: i + j <= 1),
    "plus_2.5": ("Plus de 2,5 buts", lambda i, j: i + j >= 3),
    "moins_2.5": ("Moins de 2,5 buts", lambda i, j: i + j <= 2),
    "plus_3.5": ("Plus de 3,5 buts", lambda i, j: i + j >= 4),
    "moins_3.5": ("Moins de 3,5 buts", lambda i, j: i + j <= 3),
    "btts_oui": ("Les deux équipes marquent", lambda i, j: (i > 0) & (j > 0)),
    "btts_non": ("Une équipe ne marque pas", lambda i, j: (i == 0) | (j == 0)),
    "dom_marque": ("Le domicile marque", lambda i, j: i > 0),
    "ext_marque": ("L'extérieur marque", lambda i, j: j > 0),
}


def masque(code: str, taille: int) -> np.ndarray:
    i, j = np.indices((taille, taille))
    if code.startswith("score:"):  # score exact, ex. « score:2-1 »
        a, b = (int(v) for v in code[6:].split("-"))
        return (i == a) & (j == b)
    return SELECTIONS[code][1](i, j)


def libelle(code: str) -> str:
    if code.startswith("score:"):
        return f"Score exact {code[6:]}"
    return SELECTIONS[code][0]


def ajuster_matrice(P: np.ndarray, p1x2=None, p_plus25=None, iterations: int = 100) -> np.ndarray:
    """Ajuste P pour que ses marges 1X2 et plus/moins 2,5 égalent les cibles (raking)."""
    P = np.asarray(P, float).copy()
    n = P.shape[0]
    zones = []
    if p1x2 is not None and np.all(np.isfinite(p1x2)):
        zones.append(([masque(c, n) for c in ("1", "N", "2")], np.asarray(p1x2, float)))
    if p_plus25 is not None and np.isfinite(p_plus25):
        zones.append(([masque("plus_2.5", n), masque("moins_2.5", n)],
                      np.array([p_plus25, 1 - p_plus25])))
    for _ in range(iterations if zones else 0):
        for masques, cibles in zones:
            for m, c in zip(masques, cibles):
                s = P[m].sum()
                if s > 0:
                    P[m] *= c / s
    return P / P.sum()


def proba_selection(P: np.ndarray, code: str) -> float:
    return float(P[masque(code, P.shape[0])].sum())


@dataclass
class Selection:
    match_id: str
    code: str
    cote: float | None = None  # cote proposée par le bookmaker (facultatif)


def proba_combinaison(selections: list[Selection], matrices: dict[str, np.ndarray]) -> dict:
    """Probabilité d'un combiné, cote juste, cote bookmaker et valeur attendue."""
    par_match: dict[str, list[str]] = {}
    for s in selections:
        par_match.setdefault(s.match_id, []).append(s.code)
    proba = 1.0
    details = []
    for mid, codes in par_match.items():
        P = matrices[mid]
        m = np.ones_like(P, dtype=bool)
        for c in codes:
            m &= masque(c, P.shape[0])
        p = float(P[m].sum())
        details.append({"match_id": mid, "selections": codes, "proba": p})
        proba *= p
    cotes = [s.cote for s in selections]
    cote_bk = float(np.prod(cotes)) if cotes and all(c and c > 1 for c in cotes) else None
    # avertissement : les bookmakers refusent souvent les combinés sur un même match
    meme_match = any(len(v) > 1 for v in par_match.values())
    return {
        "proba": proba,
        "cote_juste": (1 / proba) if proba > 0 else None,
        "cote_bookmaker": cote_bk,
        "valeur_attendue": (proba * cote_bk - 1) if cote_bk else None,
        "par_match": details,
        "selections_meme_match": meme_match,
    }
