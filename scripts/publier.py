"""Publication automatique (lancée par GitHub Actions toutes les 3 heures).

1. Importe les pronostics d'experts de data/experts/pronostics.csv (s'il existe).
2. Clôture automatiquement les pronostics des matchs joués (cotes de clôture de football-data)
   -> CLV et note de chaque expert.
3. Calcule les pronostics des prochains matchs (calendrier football-data).
4. Écrit publication/pronostics.json, publication/pronostiqueurs.json, publication/etat.json.

Usage : .venv/bin/python scripts/publier.py [--sortie publication] [--calendrier url_ou_fichier]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from missa import donnees, journal, odds_api  # noqa: E402
from missa.pipeline import Moteur, identifiant, saisons_precedentes  # noqa: E402
from missa.stockage import Stockage  # noqa: E402

CSV_EXPERTS = RACINE / "data" / "experts" / "pronostics.csv"


def cloturer(stockage: Stockage) -> int:
    """Renseigne la cote juste de clôture des pronostics dont le match est joué."""
    ouverts = [p for p in stockage.pronostics() if p["proba_juste_cloture"] is None]
    champs = {p["match_id"].split("-")[0] for p in ouverts}
    n = 0
    for champ in champs:
        parts = []
        for s in saisons_precedentes(pd.Timestamp.now(), 2):
            try:
                parts.append(donnees.charger_saison(champ, s))
            except Exception:
                pass
        if not parts:
            continue
        h = pd.concat(parts)
        index = {identifiant(champ, r.date, r.domicile, r.exterieur): r for r in h.itertuples()}
        for mid in {p["match_id"] for p in ouverts if p["match_id"].startswith(champ + "-")}:
            r = index.get(mid)
            if r is None:
                continue
            cotes = {}
            if pd.notna(r.clo_H):
                cotes["1x2"] = [r.clo_H, r.clo_D, r.clo_A]
            if pd.notna(r.clo_plus25):
                cotes["ou25"] = [r.clo_plus25, r.clo_moins25]
            if cotes:
                n += stockage.cloturer_match(mid, cotes)
    return n


def cotes_odds_api(sortie: Path) -> tuple[pd.DataFrame | None, dict]:
    """Cotes fraîches de The Odds API, en respectant un budget de crédits.

    Variables d'environnement :
      ODDS_API_KEY              clé (secret GitHub) — sans clé, cette étape est ignorée
      ODDS_API_SPORTS           championnats, séparés par des virgules (défaut : 8 championnats)
      ODDS_API_FREQUENCE_HEURES intervalle minimal entre deux appels (défaut 24 h ≈ 480 crédits/mois)
      PUBLICATION_URL           adresse de la publication précédente (pour réutiliser les cotes)
    """
    cle = os.environ.get("ODDS_API_KEY", "").strip()
    info = {"active": bool(cle)}
    choix = os.environ.get("ODDS_API_SPORTS", "").strip()
    max_sports = int(os.environ.get("ODDS_API_MAX_SPORTS") or 8)
    freq = float(os.environ.get("ODDS_API_FREQUENCE_HEURES") or 24)
    precedent = None
    base = os.environ.get("PUBLICATION_URL", "").rstrip("/")
    if base:
        try:
            with urllib.request.urlopen(base + "/cotes_odds_api.json", timeout=30) as r:
                precedent = json.loads(r.read())
        except Exception:
            precedent = None
    maintenant = datetime.now(timezone.utc)
    instantane = precedent
    if not cle:  # pas de clé : on réutilise les dernières cotes publiées (sans appel à l'API)
        if not precedent:
            return None, info
        info["reutilise"] = True
    age = None
    if precedent:
        age = (maintenant - datetime.fromisoformat(precedent["recupere_le"])).total_seconds() / 3600
    if cle and (precedent is None or age >= freq):
        if choix and choix != "auto":
            sports = [x.strip() for x in choix.split(",") if x.strip()]
        else:  # automatique : compétitions avec des matchs dans les 48 h (appels gratuits)
            try:
                sports = odds_api.choisir_sports(cle, max_sports)
            except Exception as e:
                info.setdefault("erreurs", []).append(f"choix automatique : {e}")
                sports = odds_api.PAR_DEFAUT
        info["sports_interroges"] = sports
        evenements, restant = {}, None
        for sp in sports:
            if restant is not None and restant < 2:
                info["arret"] = "crédits épuisés"
                break
            try:
                evenements[sp], restant = odds_api.recuperer(cle, sp)
            except Exception as e:
                info.setdefault("erreurs", []).append(f"{sp} : {e}")
        if evenements:
            instantane = {"recupere_le": maintenant.isoformat(timespec="seconds"),
                          "credits_restants": restant, "evenements": evenements}
    if not instantane:
        return None, info
    (sortie / "cotes_odds_api.json").write_text(json.dumps(instantane), encoding="utf-8")
    equipes = {}
    for sp in instantane["evenements"]:
        champ = odds_api.SPORTS.get(sp)
        if not champ:
            continue
        noms = set()
        if champ in donnees.EXTRA:
            try:
                h = donnees.charger_extra(champ)
                noms |= set(h.domicile) | set(h.exterieur)
            except Exception:
                pass
        for s_ in ([] if champ in donnees.EXTRA else saisons_precedentes(pd.Timestamp.now(), 2)):
            try:
                h = donnees.charger_saison(champ, s_)
                noms |= set(h.domicile) | set(h.exterieur)
            except Exception:
                pass
        equipes[champ] = sorted(noms)
    cal, inconnus = odds_api.vers_calendrier(instantane["evenements"], equipes)
    info |= {"recupere_le": instantane["recupere_le"], "credits_restants": instantane.get("credits_restants"),
             "matchs": int(len(cal)), "noms_non_reconnus": inconnus}
    return cal, info


def charger_precedent(nom: str):
    """Fichier de la publication précédente (branche « pronostics »), ou None."""
    base = os.environ.get("PUBLICATION_URL", "").rstrip("/")
    if not base:
        return None
    try:
        with urllib.request.urlopen(f"{base}/{nom}", timeout=30) as r:
            return json.loads(r.read())
    except Exception:
        return None


def suivre_value(res: dict, sortie: Path) -> dict:
    """Journal des paris value : ajout des nouveaux, clôture des matchs joués, résumé."""
    jr = charger_precedent("journal_value.json") or []
    ajoutes = journal.ajouter(jr, res.get("value", []))
    attente = [j for j in jr if "gagne" not in j]
    resultats = {}
    for champ in {j["match_id"].split("-")[0] for j in attente}:
        try:
            if champ in donnees.EXTRA:
                h = donnees.charger_extra(champ)
            elif champ in donnees.CHAMPIONNATS:
                h = pd.concat([donnees.charger_saison(champ, s_) for s_ in saisons_precedentes(pd.Timestamp.now(), 1)])
            else:
                continue
            resultats |= journal.index_resultats(h, identifiant)
        except Exception as e:
            print(f"[publier] résultats {champ} indisponibles : {e}")
    clotures = journal.cloturer(jr, resultats)
    (sortie / "journal_value.json").write_text(json.dumps(jr, ensure_ascii=False), encoding="utf-8")
    # journal des pronostics publiés (réussite réelle du moteur)
    jp = charger_precedent("journal_pronostics.json") or []
    journal.ajouter_pronostics(jp, res["championnats"])
    attente_p = {j["match_id"].split("-")[0] for j in jp if "gagne" not in j} - {m.split("-")[0] for m in resultats}
    for champ in attente_p:
        try:
            h = (donnees.charger_extra(champ) if champ in donnees.EXTRA else
                 pd.concat([donnees.charger_saison(champ, s_) for s_ in saisons_precedentes(pd.Timestamp.now(), 1)])
                 if champ in donnees.CHAMPIONNATS else None)
            if h is not None:
                resultats |= journal.index_resultats(h, identifiant)
        except Exception as e:
            print(f"[publier] résultats {champ} indisponibles : {e}")
    journal.cloturer_pronostics(jp, resultats)
    (sortie / "journal_pronostics.json").write_text(json.dumps(jp, ensure_ascii=False), encoding="utf-8")
    res["suivi_pronostics"] = journal.resume_pronostics(jp)
    # scores finaux récents : l'application vérifie elle-même les tickets enregistrés
    res["resultats"] = {j["match_id"]: [int(x) for x in j["score"].split("-")] for j in jp[-600:] if "score" in j}
    return journal.resume(jr) | {"ajoutes": ajoutes, "clotures": clotures}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sortie", default=str(RACINE / "publication"))
    ap.add_argument("--calendrier", default=donnees.URL_CALENDRIER)
    a = ap.parse_args()
    sortie = Path(a.sortie)
    sortie.mkdir(parents=True, exist_ok=True)

    stockage = Stockage(Path(tempfile.mkdtemp()) / "experts.db")
    rapport_experts = {"importes": 0, "refuses": []}
    if CSV_EXPERTS.exists():
        rapport_experts = stockage.importer_csv(CSV_EXPERTS)
        rapport_experts["clotures"] = cloturer(stockage)

    try:
        calendrier = donnees.charger_calendrier(a.calendrier)
    except Exception as e:  # football-data indisponible : on continue avec The Odds API
        print(f"[publier] calendrier football-data indisponible : {e}")
        calendrier = pd.DataFrame(columns=["championnat", "date", "coup_envoi", "domicile", "exterieur"])
    cal_odds, info_odds = cotes_odds_api(sortie)
    calendrier = odds_api.fusionner(cal_odds, calendrier)
    # on ne publie que les matchs à venir (ou commencés depuis moins de 2 heures)
    limite = pd.Timestamp.now(tz="UTC").tz_localize(None) - pd.Timedelta(hours=2)
    calendrier = calendrier[calendrier["coup_envoi"].fillna(calendrier["date"]) >= limite]
    res = Moteur(stockage=stockage).predire(calendrier)
    res["suivi_value"] = suivre_value(res, sortie)
    stats = RACINE / "data" / "stats_moteur.json"
    if stats.exists():
        res["stats_moteur"] = json.loads(stats.read_text(encoding="utf-8"))
    nb = sum(len(c["matchs"]) for c in res["championnats"])

    (sortie / "pronostics.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    (sortie / "pronostiqueurs.json").write_text(json.dumps(stockage.classement(), ensure_ascii=False),
                                                encoding="utf-8")
    etat = {"genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "matchs": nb, "championnats": [c["code"] for c in res["championnats"] if c["matchs"]],
            "experts": rapport_experts, "the_odds_api": info_odds, "suivi_value": res["suivi_value"]}
    (sortie / "etat.json").write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(etat, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
