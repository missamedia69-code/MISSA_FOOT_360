"""Journal des paris « value » publiés : la preuve, en conditions réelles, que la méthode marche
(ou pas).

- À chaque publication, les nouveaux paris value sont ajoutés (première cote vue, horodatée).
- Après le match : cote juste de CLÔTURE (football-data, marge retirée) et résultat.
- Mesures : CLV moyen (meilleur indicateur de rentabilité future), rendement réel à mise égale.
Le journal est publié avec les pronostics (journal_value.json) et repris à la publication suivante.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import marge


def ajouter(journal: list[dict], value: list[dict], maintenant: datetime | None = None) -> int:
    """Ajoute les paris value pas encore présents (clé : match + sélection). Renvoie le nombre ajouté."""
    maintenant = maintenant or datetime.now(timezone.utc)
    deja = {(j["match_id"], j["selection"]) for j in journal}
    n = 0
    for v in value:
        if (v["match_id"], v["selection"]) in deja:
            continue
        journal.append({k: v[k] for k in ("match_id", "championnat", "coup_envoi", "domicile", "exterieur",
                                          "selection", "libelle", "proba", "meilleure_cote", "bookmaker",
                                          "valeur_brute")}
                       | {"publie_le": maintenant.isoformat(timespec="seconds")})
        n += 1
    return n


def _gagne(sel: str, bd: int, be: int) -> bool:
    return {"1": bd > be, "N": bd == be, "2": bd < be,
            "plus_2.5": bd + be >= 3, "moins_2.5": bd + be <= 2}[sel]


def cloturer(journal: list[dict], resultats: dict) -> int:
    """resultats[match_id] = ligne d'historique (buts_dom, buts_ext, clo_H/D/A, clo_plus25/moins25).
    Renseigne CLV, résultat et gain des paris joués. Renvoie le nombre de paris clôturés."""
    n = 0
    for j in journal:
        if "gagne" in j or j["match_id"] not in resultats:
            continue
        r = resultats[j["match_id"]]
        sel = j["selection"]
        p_clo = None
        if sel in ("1", "N", "2") and np.isfinite(r.get("clo_H", np.nan)):
            p = marge.probabilites([r["clo_H"], r["clo_D"], r["clo_A"]], "puissance")
            p_clo = float(p["1N2".index(sel)])
        elif sel in ("plus_2.5", "moins_2.5") and np.isfinite(r.get("clo_plus25", np.nan)):
            p = marge.probabilites([r["clo_plus25"], r["clo_moins25"]], "abrams")
            p_clo = float(p[0] if sel == "plus_2.5" else p[1])
        g = _gagne(sel, int(r["buts_dom"]), int(r["buts_ext"]))
        j["gagne"] = g
        j["gain"] = round(j["meilleure_cote"] - 1 if g else -1.0, 4)
        if p_clo:
            j["clv"] = round(j["meilleure_cote"] * p_clo - 1, 4)
        n += 1
    return n


def resume(journal: list[dict]) -> dict:
    regles = [j for j in journal if "gagne" in j]
    clv = [j["clv"] for j in regles if "clv" in j]
    gains = [j["gain"] for j in regles]
    r = {"publies": len(journal), "regles": len(regles), "en_attente": len(journal) - len(regles)}
    if clv:
        c = np.array(clv)
        r["clv_moyen"] = round(float(c.mean()), 4)
        r["clv_positif"] = round(float(np.mean(c > 0)), 4)
        if len(c) > 1 and c.std(ddof=1) > 0:
            r["clv_t_score"] = round(float(c.mean() / (c.std(ddof=1) / np.sqrt(len(c)))), 2)
    if gains:
        r["rendement"] = round(float(np.mean(gains)), 4)
        r["reussite"] = round(float(np.mean([j["gagne"] for j in regles])), 4)
        r["valeur_annoncee_moyenne"] = round(float(np.mean([j["valeur_brute"] for j in regles])), 4)
    return r


def index_resultats(historique: pd.DataFrame, identifiant) -> dict:
    """match_id -> ligne de résultat, à partir d'un historique football-data."""
    out = {}
    for r in historique.itertuples():
        out[identifiant(r.championnat, r.date, r.domicile, r.exterieur)] = {
            "buts_dom": r.buts_dom, "buts_ext": r.buts_ext,
            "clo_H": getattr(r, "clo_H", np.nan), "clo_D": getattr(r, "clo_D", np.nan),
            "clo_A": getattr(r, "clo_A", np.nan), "clo_plus25": getattr(r, "clo_plus25", np.nan),
            "clo_moins25": getattr(r, "clo_moins25", np.nan)}
    return out
