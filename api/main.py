"""API MISSA FOOT 360 (FastAPI) — consommée par l'application Android.

Lancer :  .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000

GET  /championnats                 liste des championnats du jour avec nombre de matchs
GET  /matchs                       matchs (filtres : championnat, date, haute_confiance)
GET  /matchs/{id}                  détail d'un match (tous les marchés, matrice des scores)
POST /combinaison                  probabilité d'un combiné
GET  /confiance                    tables du mode haute confiance (historique mesuré)
GET  /pronostiqueurs               classement par CLV
POST /pronostics                   ajout d'un pronostic (réservé admin, clé MISSA_CLE_ADMIN)
POST /admin/regenerer              recalcul des pronostics (réservé admin)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from missa import confiance  # noqa: E402
from missa.jumeau import JumeauMatch, proba_combine  # noqa: E402
from missa.selections import SELECTIONS, Selection, libelle, proba_combinaison  # noqa: E402
from missa.stockage import Stockage  # noqa: E402

FICHIER = Path(os.environ.get("MISSA_PRONOSTICS", RACINE / "data" / "pronostics.json"))
CLE_ADMIN = os.environ.get("MISSA_CLE_ADMIN", "")

app = FastAPI(title="MISSA FOOT 360", version="1.0")
stockage = Stockage(os.environ.get("MISSA_BASE", RACINE / "data" / "missa.db"))
_cache: dict = {"mtime": None, "donnees": None}


def donnees() -> dict:
    if not FICHIER.exists():
        raise HTTPException(503, "Pronostics pas encore générés")
    mt = FICHIER.stat().st_mtime
    if _cache["mtime"] != mt:
        _cache["donnees"] = json.loads(FICHIER.read_text(encoding="utf-8"))
        _cache["mtime"] = mt
    return _cache["donnees"]


def tous_les_matchs() -> dict:
    return {m["id"]: m | {"nom_championnat": c["nom"]}
            for c in donnees()["championnats"] for m in c["matchs"]}


def resume(m: dict) -> dict:
    """Version légère pour les listes (sans la matrice)."""
    return {k: v for k, v in m.items() if k not in ("matrice",)}


def verifier_admin(cle: str | None):
    if not CLE_ADMIN or cle != CLE_ADMIN:
        raise HTTPException(403, "Clé administrateur invalide")


@app.get("/")
def accueil():
    d = donnees()
    return {"application": "MISSA FOOT 360", "genere_le": d["genere_le"],
            "avertissement": d["avertissement"]}


@app.get("/championnats")
def championnats():
    return [{"code": c["code"], "nom": c["nom"], "nb_matchs": len(c["matchs"])}
            for c in donnees()["championnats"] if c["matchs"]]


@app.get("/matchs")
def matchs(championnat: str | None = None, date: str | None = Query(None, description="AAAA-MM-JJ"),
           haute_confiance: bool = False, avec_matrice: bool = False):
    d = donnees()
    out = []
    for c in d["championnats"]:
        if championnat and c["code"] != championnat:
            continue
        lst = [m for m in c["matchs"]
               if (not date or m["coup_envoi"].startswith(date))
               and (not haute_confiance or m.get("selection_haute_confiance"))]
        if lst:
            out.append({"code": c["code"], "nom": c["nom"],
                        "matchs": lst if avec_matrice else [resume(m) for m in lst]})
    return {"genere_le": d["genere_le"], "avertissement": d["avertissement"], "championnats": out}


@app.get("/matchs/{match_id}")
def match(match_id: str):
    m = tous_les_matchs().get(match_id)
    if not m:
        raise HTTPException(404, "Match introuvable")
    return m


class SelectionIn(BaseModel):
    match_id: str
    selection: str
    cote: float | None = Field(None, gt=1.0)


class CombinaisonIn(BaseModel):
    selections: list[SelectionIn]


@app.post("/combinaison")
def combinaison(c: CombinaisonIn):
    if not c.selections:
        raise HTTPException(400, "Combinaison vide")
    tm = tous_les_matchs()
    matrices = {}
    for s in c.selections:
        if s.match_id not in tm:
            raise HTTPException(404, f"Match introuvable : {s.match_id}")
        if s.selection not in SELECTIONS and not s.selection.startswith("score:"):
            raise HTTPException(400, f"Sélection inconnue : {s.selection}")
        matrices[s.match_id] = np.array(tm[s.match_id]["matrice"])
    r = proba_combinaison([Selection(s.match_id, s.selection, s.cote) for s in c.selections],
                          matrices)
    r["libelles"] = [f"{tm[s.match_id]['domicile']} - {tm[s.match_id]['exterieur']} : "
                     f"{libelle(s.selection)}" for s in c.selections]
    return r


class ModulationIn(BaseModel):
    attaque_dom: float = Field(1.0, ge=0.3, le=2.0)
    attaque_ext: float = Field(1.0, ge=0.3, le=2.0)
    corners_dom: float = Field(1.0, ge=0.3, le=2.0)
    corners_ext: float = Field(1.0, ge=0.3, le=2.0)
    cartons: float = Field(1.0, ge=0.3, le=2.5)


class JambeIn(BaseModel):
    match_id: str
    selection: str  # ex. « 1X2:1 », « DC:1N & OU:3.5:moins », « CORNERS_OU:9.5:plus »


class ProbabiliteIn(BaseModel):
    selections: list[JambeIn]
    modulations: dict[str, ModulationIn] = {}


def jumeau_de(m: dict) -> JumeauMatch:
    j = m["jumeau"]
    return JumeauMatch(np.array(j["matrice"]), tuple(j["part_1mt"]), tuple(j["corners"]), tuple(j["cartons"]))


@app.post("/probabilite")
def probabilite(q: ProbabiliteIn):
    """Probabilité de n'importe quelle sélection ou combinaison, avec modulations éventuelles."""
    if not q.selections:
        raise HTTPException(400, "Aucune sélection")
    tm = tous_les_matchs()
    jumeaux = {}
    for s in q.selections:
        if s.match_id not in tm or "jumeau" not in tm[s.match_id]:
            raise HTTPException(404, f"Match introuvable : {s.match_id}")
        if s.match_id not in jumeaux:
            J = jumeau_de(tm[s.match_id])
            if s.match_id in q.modulations:
                J = J.moduler(**q.modulations[s.match_id].model_dump())
            jumeaux[s.match_id] = J
    try:
        return proba_combine([(s.match_id, s.selection) for s in q.selections], jumeaux)
    except (KeyError, ValueError, IndexError) as e:
        raise HTTPException(400, f"Sélection invalide : {e}")


@app.get("/catalogue")
def catalogue_marches():
    return donnees().get("catalogue", [])


@app.get("/confiance")
def table_confiance():
    return confiance.charger()


@app.get("/pronostiqueurs")
def pronostiqueurs():
    return stockage.classement()


class PronosticIn(BaseModel):
    pronostiqueur: str
    match_id: str
    selection: str
    cote: float = Field(gt=1.0)


@app.post("/pronostics", status_code=201)
def ajouter_pronostic(p: PronosticIn, x_cle_admin: str | None = Header(None)):
    verifier_admin(x_cle_admin)
    m = tous_les_matchs().get(p.match_id)
    if not m:
        raise HTTPException(404, "Match introuvable")
    try:
        i = stockage.ajouter_pronostic(p.pronostiqueur, p.match_id, p.selection, p.cote,
                                       datetime.fromisoformat(m["coup_envoi"]))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # doublon
        raise HTTPException(409, f"Pronostic refusé : {e}")
    return {"id": i}


@app.post("/admin/regenerer")
def regenerer(x_cle_admin: str | None = Header(None)):
    verifier_admin(x_cle_admin)
    from missa import donnees as dn
    from missa.pipeline import Moteur
    res = Moteur(stockage=stockage).predire(dn.charger_calendrier())
    FICHIER.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return {"matchs": sum(len(c["matchs"]) for c in res["championnats"])}
