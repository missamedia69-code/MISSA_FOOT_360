"""Modèles par équipe pour les corners et les cartons (même structure que Dixon-Coles, sans ρ).

corners attendus du domicile = exp(avantage + « obtient des corners »[dom] + « concède des corners »[ext])
Idem pour les cartons (« reçoit des cartons » / « provoque des cartons »).
"""
from __future__ import annotations

import pandas as pd

from .dixon_coles import DixonColes

COLONNES = {"corners": ("corners_dom", "corners_ext"), "cartons": ("jaunes_dom", "jaunes_ext")}


def ajuster(hist: pd.DataFrame, quoi: str, date_ref: pd.Timestamp, xi: float = 0.0019) -> DixonColes | None:
    cd, ce = COLONNES[quoi]
    if cd not in hist.columns:
        return None
    h = hist.dropna(subset=[cd, ce])
    if len(h) < 150:
        return None
    h = h.assign(buts_dom=h[cd], buts_ext=h[ce])[["date", "domicile", "exterieur", "buts_dom", "buts_ext"]]
    return DixonColes(xi=xi, rho_fixe=0.0).ajuster(h, date_ref)


def moyennes(modele: DixonColes | None, dom: str, ext: str, defaut: tuple) -> tuple[float, float]:
    if modele is None:
        return defaut
    r = modele.buts_attendus(dom, ext)
    return r if r is not None else defaut
