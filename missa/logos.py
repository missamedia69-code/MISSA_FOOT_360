"""Logos des équipes (écussons) via TheSportsDB (API gratuite, clé publique « 123 »).

Table persistante data/logos.json : nom d'équipe tel qu'il apparaît dans les pronostics
-> adresse de l'écusson (ou null si introuvable, avec la date de la tentative pour réessayer
plus tard). Les recherches sont limitées (30 requêtes/minute sur la clé gratuite) : chaque
publication complète la table petit à petit.

Sécurité contre les homonymes : on n'accepte un résultat que si c'est une équipe de football
du bon pays (déduit du championnat) quand le pays est connu.
"""
from __future__ import annotations

import datetime as dt
import json
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from missa.odds_api import ALIAS

FICHIER = Path(__file__).resolve().parent.parent / "data" / "logos.json"
API = "https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t="
REESSAYER_APRES_JOURS = 30

# Pays des championnats (codes football-data et The Odds API)
PAYS = {
    "E0": "England", "E1": "England", "E2": "England", "E3": "England", "EC": "England",
    "SP1": "Spain", "SP2": "Spain", "D1": "Germany", "D2": "Germany", "I1": "Italy", "I2": "Italy",
    "F1": "France", "F2": "France", "N1": "Netherlands", "B1": "Belgium", "P1": "Portugal",
    "T1": "Turkey", "G1": "Greece", "SC0": "Scotland", "SC1": "Scotland", "SC2": "Scotland", "SC3": "Scotland",
    "ARG": "Argentina", "BRA": "Brazil", "MEX": "Mexico", "USA": "USA",
    "soccer_australia_aleague": "Australia",
}

# Noms courts de football-data -> nom complet à chercher
INVERSE = {v: k for k, v in ALIAS.items()}
EXTRA_NOMS = {
    "Nott'm Forest": "Nottingham Forest", "Sheffield United": "Sheffield United", "Wolves": "Wolverhampton",
    "Ath Madrid": "Atletico Madrid", "Ath Bilbao": "Athletic Bilbao", "Sociedad": "Real Sociedad",
    "Vallecano": "Rayo Vallecano", "Espanol": "Espanyol", "M'gladbach": "Borussia Monchengladbach",
    "Ein Frankfurt": "Eintracht Frankfurt", "Paris SG": "Paris Saint-Germain", "St Etienne": "Saint-Etienne",
    "Man United": "Manchester United", "Man City": "Manchester City", "PSV Eindhoven": "PSV",
    "Derby": "Derby County", "Lille": "Lille OSC", "Sp Gijon": "Sporting Gijon", "Oviedo": "Real Oviedo",
    "Santander": "Racing Santander", "La Coruna": "Deportivo La Coruna", "Valladolid": "Real Valladolid",
    "Peterboro": "Peterborough United", "Preston": "Preston North End", "Rotherham": "Rotherham United",
    "Bristol Rvs": "Bristol Rovers", "Boston Utd": "Boston United", "Raith Rvs": "Raith Rovers",
    "Queen of Sth": "Queen of the South", "For Sittard": "Fortuna Sittard", "Nijmegen": "NEC",
    "Den Haag": "ADO Den Haag", "Buyuksehyr": "Istanbul Basaksehir", "Dresden": "Dynamo Dresden",
    "Braunschweig": "Eintracht Braunschweig", "Doncaster": "Doncaster Rovers", "Lincoln": "Lincoln City",
    "Oldham": "Oldham Athletic", "Sutton": "Sutton United", "Hamilton": "Hamilton Academical",
    "Ayr": "Ayr United", "AEK": "AEK Athens", "Larisa": "AEL Larissa", "Levadeiakos": "Levadiakos",
    "Nancy": "AS Nancy", "Metz": "FC Metz", "Reims": "Stade de Reims", "Annecy": "FC Annecy",
    "Monaco": "AS Monaco", "Twente": "FC Twente", "Utrecht": "FC Utrecht", "Groningen": "FC Groningen",
    "Swansea": "Swansea City", "Cardiff": "Cardiff City", "Celta B": "Celta Vigo B",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum() or c == " ").strip()


def charger() -> dict:
    return json.loads(FICHIER.read_text(encoding="utf-8")) if FICHIER.exists() else {}


def sauver(table: dict) -> None:
    FICHIER.write_text(json.dumps(dict(sorted(table.items())), ensure_ascii=False, indent=0), encoding="utf-8")


def _chercher(nom: str) -> list[dict]:
    url = API + urllib.parse.quote(nom)
    req = urllib.request.Request(url, headers={"User-Agent": "missa-foot-360"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return (json.loads(r.read().decode("utf-8")) or {}).get("teams") or []


# Pays acceptés en plus (clubs gallois en Angleterre, Monaco en France…)
SYNONYMES = {"Netherlands": {"Netherlands", "The Netherlands", "Holland"}, "England": {"England", "Wales"},
             "France": {"France", "Monaco"}, "USA": {"USA", "United States", "Canada"}}


def _choisir(candidats: list[dict], nom: str, pays: str | None) -> str | None:
    bons = [t for t in candidats if t.get("strSport") == "Soccer" and t.get("strBadge")]
    if pays:
        bons = [t for t in bons if (t.get("strCountry") or "") in SYNONYMES.get(pays, {pays})]
    if not bons:
        return None
    n = _norm(nom)
    # préférence : nom exact, puis nom alternatif, puis premier résultat
    for t in bons:
        if _norm(t.get("strTeam", "")) == n:
            return t["strBadge"]
    for t in bons:
        if n in _norm(t.get("strTeamAlternate") or ""):
            return t["strBadge"]
    return bons[0]["strBadge"]


def fusionner(*tables: dict | None) -> dict:
    """Réunit plusieurs tables ; une entrée avec logo l'emporte sur une tentative échouée."""
    out: dict = {}
    for t in tables:
        for nom, e in (t or {}).items():
            if not isinstance(e, dict):
                continue
            if nom not in out or (e.get("url") and not out[nom].get("url")):
                out[nom] = e
    return out


def completer(equipes: dict[str, str | None], max_requetes: int = 40, pause: float = 2.1,
              table: dict | None = None, sauvegarder: bool = True, forcer: bool = False) -> dict:
    """equipes : nom -> code de championnat (pour le pays). Complète la table (data/logos.json par défaut)."""
    table = charger() if table is None else table
    aujourd_hui = dt.date.today()
    faites = 0
    for nom, code in equipes.items():
        e = table.get(nom)
        if isinstance(e, dict) and e.get("url"):
            continue
        if isinstance(e, dict) and e.get("essai") and not forcer:
            if (aujourd_hui - dt.date.fromisoformat(e["essai"])).days < REESSAYER_APRES_JOURS:
                continue
        if faites >= max_requetes:
            break
        pays = PAYS.get(code or "")
        url = None
        for essai in dict.fromkeys([EXTRA_NOMS.get(nom), INVERSE.get(nom), nom, f"{nom} FC", f"FC {nom}"]):
            if not essai or faites >= max_requetes:
                continue
            try:
                url = _choisir(_chercher(essai), essai, pays)
            except Exception:
                url = None
            faites += 1
            time.sleep(pause)
            if url:
                break
        table[nom] = {"url": url} if url else {"url": None, "essai": aujourd_hui.isoformat()}
    if sauvegarder:
        sauver(table)
    return table


def adresses(table: dict, noms) -> dict[str, str]:
    """Adresses (version réduite « /small », 250 px) des équipes demandées qui ont un logo."""
    out = {}
    for n in noms:
        e = table.get(n)
        if isinstance(e, dict) and e.get("url"):
            out[n] = e["url"] + "/small"
    return out
