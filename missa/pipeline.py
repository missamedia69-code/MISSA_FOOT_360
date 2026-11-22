"""Pronostics des prochains matchs : du calendrier aux probabilités finales.

Pour chaque match :
1. cotes du marché -> probabilités justes (1X2 : méthode puissance ; plus/moins : Abrams)
2. Dixon-Coles (historique des 3 dernières saisons du championnat) et Elo
3. combinaison avec les poids appris au backtest (data/modele.json)
4. matrice des scores ajustée aux probabilités finales (sert aux combinés)
5. avis des pronostiqueurs au talent prouvé (ajustement de la matrice)
6. pour chaque sélection : probabilité, cote juste, meilleure cote, valeur, niveau de confiance
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from . import comptages, confiance, donnees, marge, valeur
from .backtest import LogitOrdonne
from .combinaison import PoolLogarithmique
from .dixon_coles import DixonColes, matrice_scores
from .elo import Elo
from .jumeau import JumeauMatch, catalogue
from .pronostiqueurs import ajuster_matrice as ajuster_par_pronostiqueurs
from .selections import SELECTIONS, ajuster_matrice, libelle, proba_selection

RACINE = Path(__file__).resolve().parent.parent
MODELE = RACINE / "data" / "modele.json"
TAILLE_MATRICE = 10  # scores de 0 à 9
AVERTISSEMENT = ("Probabilités statistiques, pas des certitudes. Aucun pronostic n'est sûr. "
                 "Jouer comporte des risques : endettement, dépendance. Interdit aux mineurs.")
FAMILLE_DE = {c: f for f, codes in confiance.FAMILLES.items() for c in codes}


def code_saison(d: pd.Timestamp) -> str:
    a = d.year % 100
    return f"{a:02d}{a + 1:02d}" if d.month >= 7 else f"{a - 1:02d}{a:02d}"


def saisons_precedentes(d: pd.Timestamp, n: int = 3) -> list[str]:
    s = code_saison(d)
    a = int(s[:2])
    return [f"{(a - k) % 100:02d}{(a - k + 1) % 100:02d}" for k in range(n - 1, -1, -1)]


def identifiant(champ: str, d: pd.Timestamp, dom: str, ext: str) -> str:
    slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")  # noqa: E731
    return f"{champ}-{d:%Y%m%d}-{slug(dom)}-{slug(ext)}"


def lambdas_depuis_marche(p1x2, p_plus25=None) -> tuple[float, float]:
    """Buts attendus (λ, μ) qui reproduisent au mieux les probabilités du marché."""
    k = np.arange(TAILLE_MATRICE)

    def err(t):
        lam, mu = np.exp(t)
        P = np.outer(poisson.pmf(k, lam), poisson.pmf(k, mu))
        P /= P.sum()
        i, j = np.indices(P.shape)
        e = (P[i > j].sum() - p1x2[0]) ** 2 + (P[i < j].sum() - p1x2[2]) ** 2
        if p_plus25 is not None and np.isfinite(p_plus25):
            e += (P[i + j >= 3].sum() - p_plus25) ** 2
        return e

    r = minimize(err, np.log([1.4, 1.1]), method="Nelder-Mead")
    return tuple(float(v) for v in np.exp(r.x))


SEUIL_VALUE = 0.03  # valeur minimale (3 %) : meilleure cote × probabilité − 1


def liste_value(champs: list) -> list[dict]:
    """Paris « value » façon Kaunitz/Buchdahl : la meilleure cote du marché dépasse le prix juste
    estimé par le consensus (marché sans marge + moteur). Triés par valeur décroissante."""
    out = []
    for c in champs:
        for m in c["matchs"]:
            for code in m.get("selections_value", []):
                e = m["marches"][code]
                out.append({
                    "match_id": m["id"], "championnat": c["nom"], "coup_envoi": m["coup_envoi"],
                    "domicile": m["domicile"], "exterieur": m["exterieur"], "selection": code,
                    "libelle": e["libelle"], "proba": e["proba"], "cote_juste": e["cote_juste"],
                    "meilleure_cote": e["meilleure_cote"], "bookmaker": e.get("bookmaker"),
                    "valeur_brute": e["valeur_brute"], "valeur_corrigee": e["valeur"],
                    "mise_kelly": round(valeur.kelly_fractionnaire(e["proba"], e["meilleure_cote"]), 4),
                })
    return sorted(out, key=lambda v: -v["valeur_brute"])


def _resume_match(r, equipe: str) -> dict:
    dom = r.domicile == equipe
    bp, bc = (r.buts_dom, r.buts_ext) if dom else (r.buts_ext, r.buts_dom)
    return {"date": r.date.strftime("%Y-%m-%d"), "adversaire": r.exterieur if dom else r.domicile,
            "lieu": "dom" if dom else "ext", "score": f"{int(bp)}-{int(bc)}",
            "res": "V" if bp > bc else "N" if bp == bc else "D"}


def analyse_match(h: pd.DataFrame | None, dom: str, ext: str, sources: dict, p1x2) -> dict:
    """Éléments d'explication : forme récente, confrontations, moyennes, avis de chaque source."""
    out = {"sources": {k: [round(float(x), 4) for x in v] for k, v in sources.items()},
           "final": [round(float(x), 4) for x in p1x2]}
    if h is None or h.empty:
        return out
    h = h.sort_values("date")
    for equipe, cle in ((dom, "dom"), (ext, "ext")):
        mt = h[(h.domicile == equipe) | (h.exterieur == equipe)]
        der = mt.tail(10)
        if der.empty:
            continue
        bp = np.where(der.domicile == equipe, der.buts_dom, der.buts_ext)
        bc = np.where(der.domicile == equipe, der.buts_ext, der.buts_dom)
        lieu = mt[mt.domicile == equipe].tail(10) if cle == "dom" else mt[mt.exterieur == equipe].tail(10)
        res_lieu = [_resume_match(r, equipe)["res"] for r in lieu.itertuples()]
        out[f"forme_{cle}"] = [_resume_match(r, equipe) for r in mt.tail(5).itertuples()][::-1]
        out[f"stats_{cle}"] = {
            "matchs": int(len(der)), "buts_marques": round(float(bp.mean()), 2), "buts_encaisses": round(float(bc.mean()), 2),
            "plus_2_5": round(float(np.mean(bp + bc >= 3)), 2), "btts": round(float(np.mean((bp > 0) & (bc > 0))), 2),
            "clean_sheets": round(float(np.mean(bc == 0)), 2),
            "lieu": {"v": res_lieu.count("V"), "n": res_lieu.count("N"), "d": res_lieu.count("D"),
                     "type": "à domicile" if cle == "dom" else "à l'extérieur"},
        }
    h2h = h[((h.domicile == dom) & (h.exterieur == ext)) | ((h.domicile == ext) & (h.exterieur == dom))].tail(6)
    out["confrontations"] = [{"date": r.date.strftime("%Y-%m-%d"), "domicile": r.domicile, "exterieur": r.exterieur,
                              "score": f"{int(r.buts_dom)}-{int(r.buts_ext)}"} for r in h2h.itertuples()][::-1]
    return out


class Moteur:
    def __init__(self, stockage=None, cache: Path = donnees.CACHE):
        cfg = json.loads(MODELE.read_text()) if MODELE.exists() else {}
        self.cfg = cfg
        self.calibration = confiance.charger()
        self.stockage = stockage
        self.cache = cache
        self.pool = None
        if "pool" in cfg:
            self.pool = PoolLogarithmique(cfg["pool"]["sources"])
            self.pool.poids = np.array(cfg["pool"]["poids"])
            self.pool.biais = np.array(cfg["pool"]["biais"])
        self.logit = None
        if "elo_logit" in cfg:
            self.logit = LogitOrdonne()
            self.logit.b, self.logit.c1, self.logit.c2 = (cfg["elo_logit"][k] for k in ("b", "c1", "c2"))
        self._modeles: dict = {}
        self._historiques: dict = {}
        self.params_jumeau = cfg.get("jumeau", {})
        f = RACINE / "data" / "fiabilite_marches.json"
        self.fiabilite = json.loads(f.read_text())["familles"] if f.exists() else {}

    # --- modèles par championnat ----------------------------------------------------------
    def _historique(self, champ: str, d: pd.Timestamp) -> pd.DataFrame | None:
        if champ in donnees.EXTRA:
            try:
                h = donnees.charger_extra(champ, self.cache)
                return h[h["date"] < d]
            except Exception:
                return None
        if champ not in donnees.CHAMPIONNATS:
            return None  # compétition sans historique (coupes, sélections) : marché seul
        parts = []
        for s in saisons_precedentes(d):
            try:
                parts.append(donnees.charger_saison(champ, s, self.cache))
            except Exception:
                pass
        if not parts:
            return None
        h = pd.concat(parts, ignore_index=True).sort_values("date")
        return h[h["date"] < d]

    def modeles(self, champ: str, d: pd.Timestamp):
        cle = (champ, d.normalize())
        if cle not in self._modeles:
            h = self._historique(champ, d)
            dc = elo = None
            if h is not None and len(h) >= 200:
                dc = DixonColes(xi=self.cfg.get("dixon_coles_xi", 0.0019)).ajuster(h, d)
                elo = Elo(**self.cfg.get("elo", {}))
                saison = None
                for _, r in h.iterrows():
                    if r["saison"] != saison:
                        saison = r["saison"]
                        elo.nouvelle_saison(set(h.loc[h["saison"] == saison, "domicile"]))
                    elo.mettre_a_jour(r["domicile"], r["exterieur"], int(r["buts_dom"]),
                                      int(r["buts_ext"]))
            corners = comptages.ajuster(h, "corners", d) if h is not None else None
            cartons = comptages.ajuster(h, "cartons", d) if h is not None else None
            self._modeles[cle] = (dc, elo, corners, cartons)
            self._historiques[cle] = h
        return self._modeles[cle]

    # --- un match -----------------------------------------------------------------------------
    def predire_match(self, m: pd.Series, maintenant: datetime | None = None) -> dict:
        champ, d = m["championnat"], pd.Timestamp(m["date"])
        dc, elo, mod_corners, mod_cartons = self.modeles(champ, d)
        mid = identifiant(champ, d, m["domicile"], m["exterieur"])
        sources = {}
        p_marche = marge.probabilites([m.get("ouv_H"), m.get("ouv_D"), m.get("ouv_A")], "puissance")
        if np.all(np.isfinite(p_marche)):
            sources["marche_ouv"] = p_marche
        pr_dc = dc.predire(m["domicile"], m["exterieur"]) if dc else None
        if pr_dc:
            sources["dixon_coles"] = np.array([pr_dc["1"], pr_dc["N"], pr_dc["2"]])
        if elo and self.logit and m["domicile"] in elo.notes and m["exterieur"] in elo.notes:
            sources["elo"] = self.logit.predire([elo.ecart(m["domicile"], m["exterieur"])])[0]

        if not sources:
            return {"id": mid, "disponible": False, "raison": "Ni cotes ni historique"}
        if self.pool is not None and all(s in sources for s in self.pool.sources):
            p1x2 = self.pool.predire({s: sources[s][None, :] for s in self.pool.sources})[0]
            methode = "Marché + modèles (poids appris)"
        elif "marche_ouv" in sources:
            p1x2, methode = sources["marche_ouv"], "Marché"
        else:
            p1x2, methode = sources["dixon_coles"], "Dixon-Coles (pas de cotes disponibles)"

        p_ou = marge.probabilites([m.get("ouv_plus25"), m.get("ouv_moins25")], "abrams")[0]
        if not np.isfinite(p_ou) and pr_dc:
            p_ou = pr_dc["plus_2.5"]

        if pr_dc:
            P = matrice_scores(pr_dc["lambda"], pr_dc["mu"], dc.rho, TAILLE_MATRICE - 1)
        else:
            P = matrice_scores(*lambdas_depuis_marche(p1x2, p_ou), -0.1, TAILLE_MATRICE - 1)
        P = ajuster_matrice(P, p1x2, p_ou)

        avis = self.stockage.avis_match(mid) if self.stockage else []
        P = ajuster_par_pronostiqueurs(P, [(a["selection"], a["ajustement"]) for a in avis])

        coup_envoi = pd.Timestamp(m.get("coup_envoi") if pd.notna(m.get("coup_envoi")) else d)
        maintenant = pd.Timestamp(maintenant) if maintenant else pd.Timestamp.now(tz="UTC").tz_localize(None)
        heures = max(0.0, (coup_envoi - maintenant).total_seconds() / 3600)
        meilleures = {"1": m.get("max_H"), "N": m.get("max_D"), "2": m.get("max_A"),
                      "plus_2.5": m.get("max_plus25"), "moins_2.5": m.get("max_moins25")}
        chez = {"1": m.get("bk_H"), "N": m.get("bk_D"), "2": m.get("bk_A"),
                "plus_2.5": m.get("bk_plus25"), "moins_2.5": m.get("bk_moins25")}
        marches = {}
        for code in SELECTIONS:
            p = proba_selection(P, code)
            c = meilleures.get(code)
            c = float(c) if c is not None and np.isfinite(c) and c > 1 else None
            e = {"libelle": libelle(code), "proba": round(p, 4),
                 "cote_juste": round(1 / p, 2) if p > 0 else None, "meilleure_cote": c}
            if c:
                e["valeur"] = round(valeur.valeur_corrigee(p, c, heures), 4)
                e["valeur_brute"] = round(valeur.valeur_attendue(p, c), 4)
                if isinstance(chez.get(code), str):
                    e["bookmaker"] = chez[code]
            if code in FAMILLE_DE:
                e["confiance"] = confiance.niveau(self.calibration, FAMILLE_DE[code], p)
            marches[code] = e

        pj = self.params_jumeau
        cm = comptages.moyennes(mod_corners, m["domicile"], m["exterieur"], (5.3, 4.4))
        ym = comptages.moyennes(mod_cartons, m["domicile"], m["exterieur"], (1.9, 2.1))
        jumeau = JumeauMatch(P, tuple(pj.get("part_1mt", (0.418, 0.0086))),
                             (cm[0], cm[1], pj.get("corners_k_total", 56.0), pj.get("corners_rho", 0.087)),
                             (ym[0], ym[1], pj.get("cartons_cov", 0.33)))

        i, j = np.unravel_index(P.argmax(), P.shape)
        principal = max(("1", "N", "2"), key=lambda c: marches[c]["proba"])
        candidats = [c for c in marches if marches[c].get("confiance", {}).get("haute_confiance")]
        sure = max(candidats, key=lambda c: marches[c]["proba"]) if candidats else None
        values = sorted([c for c in marches if marches[c].get("valeur_brute", -1) >= SEUIL_VALUE],
                        key=lambda c: -marches[c]["valeur_brute"])
        return {
            "id": mid, "disponible": True, "championnat": champ,
            "coup_envoi": coup_envoi.isoformat() + "Z", "domicile": m["domicile"],
            "exterieur": m["exterieur"], "methode": methode,
            "buts_attendus": [round(float(np.sum(np.arange(len(P)) * P.sum(1))), 2),
                              round(float(np.sum(np.arange(len(P)) * P.sum(0))), 2)],
            "score_probable": f"{i}-{j}", "pronostic_principal": principal,
            "selection_haute_confiance": sure, "selections_value": values,
            "marches": marches, "pronostiqueurs": avis,
            "matrice": np.round(P, 5).tolist(),
            "jumeau": jumeau.vers_json(),
            "corners_attendus": [round(cm[0], 2), round(cm[1], 2)],
            "cartons_attendus": [round(ym[0], 2), round(ym[1], 2)],
            "analyse": analyse_match(self._historiques.get((champ, d.normalize())), m["domicile"], m["exterieur"],
                                     sources, p1x2),
        }

    # --- une journée ---------------------------------------------------------------------------
    def predire(self, calendrier: pd.DataFrame, maintenant: datetime | None = None) -> dict:
        champs = []
        for code, g in calendrier.groupby("championnat"):
            matchs = [self.predire_match(r, maintenant) for _, r in g.sort_values("coup_envoi").iterrows()]
            nom = g["nom_championnat"].dropna().iloc[0] if "nom_championnat" in g and g["nom_championnat"].notna().any() else code
            champs.append({"code": code, "nom": donnees.CHAMPIONNATS.get(code, nom),
                           "matchs": [x for x in matchs if x.get("disponible")]})
        return {"genere_le": datetime.now().isoformat(timespec="seconds"),
                "avertissement": AVERTISSEMENT, "championnats": champs,
                "value": liste_value(champs),
                "catalogue": [{"groupe": g, "titre": t, "options": [{"code": c, "libelle": l} for c, l in o]}
                              for g, t, o in catalogue()],
                "fiabilite": self.fiabilite}
