"""Cotes en continu via The Odds API (https://the-odds-api.com, documentation v4).

GET https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey=…&regions=eu&markets=h2h,totals
     &oddsFormat=decimal&dateFormat=iso
Coût d'un appel : (nombre de marchés) × (nombre de régions) crédits. Offre gratuite : 500 crédits/mois.
L'en-tête « x-requests-remaining » indique les crédits restants.

Ce module transforme la réponse en calendrier au format du moteur (mêmes colonnes que
donnees.charger_calendrier) : cotes de référence (Pinnacle si disponible, sinon moyenne des
bookmakers) et meilleures cotes du marché, pour le 1X2 et le plus/moins 2,5.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

URL = "https://api.the-odds-api.com/v4/sports/{sport}/odds/"

# clé The Odds API -> code football-data (pour l'historique des équipes)
SPORTS = {
    "soccer_epl": "E0", "soccer_efl_champ": "E1", "soccer_england_league1": "E2",
    "soccer_england_league2": "E3", "soccer_spl": "SC0", "soccer_spain_la_liga": "SP1",
    "soccer_spain_segunda_division": "SP2", "soccer_italy_serie_a": "I1", "soccer_italy_serie_b": "I2",
    "soccer_germany_bundesliga": "D1", "soccer_germany_bundesliga2": "D2",
    "soccer_france_ligue_one": "F1", "soccer_france_ligue_two": "F2",
    "soccer_netherlands_eredivisie": "N1", "soccer_belgium_first_div": "B1",
    "soccer_portugal_primeira_liga": "P1", "soccer_turkey_super_league": "T1",
    "soccer_greece_super_league": "G1",
    # championnats « extra » (historique football-data par pays)
    "soccer_brazil_campeonato": "BRA", "soccer_argentina_primera_division": "ARG",
    "soccer_mexico_ligamx": "MEX", "soccer_usa_mls": "USA", "soccer_japan_j_league": "JPN",
    "soccer_norway_eliteserien": "NOR", "soccer_sweden_allsvenskan": "SWE",
    "soccer_denmark_superliga": "DNK", "soccer_austria_bundesliga": "AUT",
    "soccer_switzerland_superleague": "SWZ", "soccer_poland_ekstraklasa": "POL",
    "soccer_china_superleague": "CHN", "soccer_finland_veikkausliiga": "FIN",
    "soccer_league_of_ireland": "IRL",
}

# ordre de priorité quand le budget de crédits ne permet pas de tout prendre
PRIORITE = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a",
    "soccer_germany_bundesliga", "soccer_france_ligue_one", "soccer_uefa_europa_league",
    "soccer_brazil_campeonato", "soccer_argentina_primera_division", "soccer_mexico_ligamx",
    "soccer_efl_champ", "soccer_portugal_primeira_liga", "soccer_netherlands_eredivisie",
    "soccer_uefa_europa_conference_league", "soccer_usa_mls", "soccer_turkey_super_league",
    "soccer_belgium_first_div", "soccer_spl",
]
PAR_DEFAUT = ["soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a",
              "soccer_germany_bundesliga", "soccer_france_ligue_one", "soccer_efl_champ",
              "soccer_portugal_primeira_liga", "soccer_netherlands_eredivisie"]

# noms usuels (The Odds API) -> noms football-data
ALIAS = {
    "manchester united": "Man United", "manchester city": "Man City", "tottenham hotspur": "Tottenham",
    "wolverhampton wanderers": "Wolves", "newcastle united": "Newcastle", "nottingham forest": "Nott'm Forest",
    "brighton and hove albion": "Brighton", "west ham united": "West Ham", "leeds united": "Leeds",
    "leicester city": "Leicester", "ipswich town": "Ipswich", "afc bournemouth": "Bournemouth",
    "sheffield wednesday": "Sheffield Weds", "queens park rangers": "QPR", "west bromwich albion": "West Brom",
    "atletico madrid": "Ath Madrid", "athletic bilbao": "Ath Bilbao", "real betis": "Betis",
    "celta vigo": "Celta", "rayo vallecano": "Vallecano", "real sociedad": "Sociedad", "espanyol": "Espanol",
    "deportivo alaves": "Alaves", "borussia dortmund": "Dortmund", "borussia monchengladbach": "M'gladbach",
    "bayer leverkusen": "Leverkusen", "eintracht frankfurt": "Ein Frankfurt", "vfb stuttgart": "Stuttgart",
    "fc st. pauli": "St Pauli", "1. fc koln": "FC Koln", "fc koln": "FC Koln", "1. fc heidenheim": "Heidenheim",
    "inter milan": "Inter", "ac milan": "Milan", "as roma": "Roma", "paris saint germain": "Paris SG",
    "saint etienne": "St Etienne", "olympique lyonnais": "Lyon", "olympique marseille": "Marseille",
    "psv eindhoven": "PSV Eindhoven", "sporting lisbon": "Sp Lisbon", "sporting cp": "Sp Lisbon",
    "fc porto": "Porto", "sc braga": "Sp Braga", "vitoria guimaraes": "Guimaraes",
    # Brésil
    "atletico mineiro": "Atletico-MG", "athletico paranaense": "Athletico-PR", "atletico paranaense": "Athletico-PR",
    "botafogo": "Botafogo RJ", "red bull bragantino": "Bragantino", "flamengo": "Flamengo RJ",
    "vasco da gama": "Vasco", "chapecoense": "Chapecoense-SC", "sao paulo": "Sao Paulo",
    # Argentine
    "atletico tucuman": "Atl. Tucuman", "argentinos juniors": "Argentinos Jrs", "estudiantes": "Estudiantes L.P.",
    "estudiantes de la plata": "Estudiantes L.P.", "gimnasia la plata": "Gimnasia L.P.",
    "newell's old boys": "Newells Old Boys", "independiente rivadavia": "Ind. Rivadavia",
    "deportivo riestra": "Dep. Riestra", "talleres": "Talleres Cordoba", "union santa fe": "Union de Santa Fe",
    "sarmiento": "Sarmiento Junin", "san martin de san juan": "San Martin S.J.",
    # Mexique
    "atletico san luis": "Atl. San Luis", "america": "Club America", "club america": "Club America",
    "leon": "Club Leon", "tijuana": "Club Tijuana", "guadalajara": "Guadalajara Chivas", "chivas": "Guadalajara Chivas",
    "fc juarez": "Juarez", "mazatlan": "Mazatlan FC", "tigres": "Tigres UANL", "pumas unam": "UNAM Pumas",
    "pumas": "UNAM Pumas",
}

ABREVIATIONS = {"atl": "atletico", "jrs": "juniors", "dep": "deportivo", "ind": "independiente",
                "utd": "united", "st": "saint", "lp": "la plata"}


def _norm(nom: str) -> str:
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode().lower()
    s = s.replace("l.p.", "lp").replace("s.j.", "sj")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    mots = [ABREVIATIONS.get(m, m) for m in s.split()]
    mots = [m for m in mots if m not in ("fc", "afc", "cf", "sc", "ac", "as", "ssc", "us", "ss", "sv",
                                         "vfl", "vfb", "tsg", "1", "club", "cd", "ca", "de", "the")]
    return " ".join(mots)


def _score(a: str, b: str) -> float:
    """Ressemblance entre deux noms normalisés (mots communs ou préfixes, ≥ 3 lettres)."""
    A, B = a.split(), b.split()
    if not A or not B:
        return 0.0
    communs = sum(1 for x in A if any(x == y or (len(x) >= 3 and len(y) >= 3 and (x.startswith(y) or y.startswith(x)))
                                       for y in B))
    return communs / max(len(A), len(B))


def apparier(nom: str, candidats: list[str]) -> str | None:
    """Nom d'équipe The Odds API -> nom football-data. None si aucune correspondance SÛRE
    (mieux vaut un match sans historique qu'un match calculé avec la mauvaise équipe)."""
    if not candidats:
        return None
    cle = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode().lower().strip()
    if cle in ALIAS and ALIAS[cle] in candidats:
        return ALIAS[cle]
    normes = {_norm(c): c for c in candidats}
    n = _norm(nom)
    if n in normes:
        return normes[n]
    notes = sorted(((_score(n, k), difflib.SequenceMatcher(None, n, k).ratio(), c) for k, c in normes.items()),
                   reverse=True)
    meilleur = notes[0]
    second = notes[1] if len(notes) > 1 else (0, 0, None)
    if meilleur[0] >= 0.5 and meilleur[0] > second[0]:
        return meilleur[2]
    if meilleur[0] == 0 and meilleur[1] >= 0.85 and meilleur[1] - second[1] > 0.1:
        return meilleur[2]  # faute d'orthographe proche (ex. accents, tirets)
    return None


def _get(url: str, params: dict, timeout: int = 30):
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": "missa-foot-360"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def sports_actifs(cle: str) -> list[dict]:
    """Compétitions de football en cours (appel gratuit, sans crédit)."""
    return [s for s in _get("https://api.the-odds-api.com/v4/sports/", {"apiKey": cle})
            if s.get("group") == "Soccer" and s.get("active") and not s.get("has_outrights")]


def nb_matchs_proches(cle: str, sport: str, heures: float = 48) -> int:
    """Nombre de matchs dans les prochaines heures (liste des événements : appel gratuit)."""
    maintenant = pd.Timestamp.now(tz="UTC")
    evs = _get(f"https://api.the-odds-api.com/v4/sports/{sport}/events/",
               {"apiKey": cle, "dateFormat": "iso",
                "commenceTimeFrom": maintenant.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "commenceTimeTo": (maintenant + pd.Timedelta(hours=heures)).strftime("%Y-%m-%dT%H:%M:%SZ")})
    return len(evs)


def choisir_sports(cle: str, max_sports: int = 8, heures: float = 48) -> list[str]:
    """Compétitions qui ont des matchs bientôt, par ordre de priorité, dans la limite du budget."""
    actifs = {s["key"] for s in sports_actifs(cle)}
    ordre = [s for s in PRIORITE if s in actifs] + sorted(a for a in actifs if a not in PRIORITE)
    choix = []
    for sp in ordre:
        if len(choix) >= max_sports:
            break
        try:
            if nb_matchs_proches(cle, sp, heures) > 0:
                choix.append(sp)
        except Exception:
            continue
    return choix


def recuperer(cle: str, sport: str, regions: str = "eu", marches: str = "h2h,totals",
              timeout: int = 30) -> tuple[list, int | None]:
    q = urllib.parse.urlencode({"apiKey": cle, "regions": regions, "markets": marches,
                                "oddsFormat": "decimal", "dateFormat": "iso"})
    req = urllib.request.Request(URL.format(sport=sport) + "?" + q, headers={"User-Agent": "missa-foot-360"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        restant = r.headers.get("x-requests-remaining")
        return json.loads(r.read()), (int(float(restant)) if restant is not None else None)


def _cotes_evenement(ev: dict) -> dict:
    """Référence (Pinnacle sinon moyenne) et meilleures cotes : 1X2 et plus/moins 2,5."""
    h2h, tot, pin_h2h, pin_tot = [], [], None, None
    dom, ext = ev["home_team"], ev["away_team"]
    for b in ev.get("bookmakers", []):
        for m in b.get("markets", []):
            o = {x["name"]: x for x in m.get("outcomes", [])}
            if m["key"] == "h2h" and {dom, ext, "Draw"} <= set(o):
                v = [o[dom]["price"], o["Draw"]["price"], o[ext]["price"]]
                h2h.append(v)
                if b["key"] == "pinnacle":
                    pin_h2h = v
            elif m["key"] == "totals" and o.get("Over", {}).get("point") == 2.5 and "Under" in o:
                v = [o["Over"]["price"], o["Under"]["price"]]
                tot.append(v)
                if b["key"] == "pinnacle":
                    pin_tot = v
    r = {}
    if h2h:
        a = np.array(h2h, float)
        ref = pin_h2h if pin_h2h else a.mean(axis=0)
        for k, s in enumerate("HDA"):
            r[f"ouv_{s}"], r[f"max_{s}"] = float(ref[k]), float(a[:, k].max())
    if tot:
        a = np.array(tot, float)
        ref = pin_tot if pin_tot else a.mean(axis=0)
        for k, s in enumerate(("plus25", "moins25")):
            r[f"ouv_{s}"], r[f"max_{s}"] = float(ref[k]), float(a[:, k].max())
    r["nb_bookmakers"] = len(ev.get("bookmakers", []))
    return r


def vers_calendrier(evenements: dict[str, list], equipes: dict[str, list[str]]) -> tuple[pd.DataFrame, list]:
    """evenements[sport] = réponse de l'API ; equipes[code football-data] = noms connus.
    Renvoie (calendrier, noms non reconnus)."""
    lignes, inconnus = [], []
    for sport, evs in evenements.items():
        champ = SPORTS.get(sport, sport)   # compétition sans historique : code = clé de l'API
        for ev in evs:
            dom = apparier(ev["home_team"], equipes.get(champ, []))
            ext = apparier(ev["away_team"], equipes.get(champ, []))
            for brut, trouve in ((ev["home_team"], dom), (ev["away_team"], ext)):
                if trouve is None and sport in SPORTS:  # compétitions sans historique : normal
                    inconnus.append(f"{champ}: {brut}")
            ko = pd.Timestamp(ev["commence_time"]).tz_convert("UTC").tz_localize(None)
            lignes.append({"championnat": champ, "nom_championnat": ev.get("sport_title", champ),
                           "date": ko.normalize(), "coup_envoi": ko,
                           "domicile": dom or ev["home_team"], "exterieur": ext or ev["away_team"],
                           "source": "the-odds-api", **_cotes_evenement(ev)})
    cols = ["championnat", "date", "coup_envoi", "domicile", "exterieur"] + \
        [f"{p}_{s}" for s in ("H", "D", "A", "plus25", "moins25") for p in ("ouv", "max")]
    df = pd.DataFrame(lignes)
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df, sorted(set(inconnus))


def fusionner(odds: pd.DataFrame, fd: pd.DataFrame) -> pd.DataFrame:
    """Calendrier final : matchs The Odds API (cotes fraîches) + matchs football-data des
    championnats non couverts ou absents de The Odds API."""
    if odds is None or odds.empty:
        return fd
    if fd is None or fd.empty:
        return odds.reset_index(drop=True)
    cle = lambda d: d["championnat"] + "|" + d["domicile"] + "|" + d["exterieur"] + "|" + d["date"].dt.strftime("%Y-%m-%d")  # noqa: E731
    deja = set(cle(odds))
    reste = fd[~cle(fd).isin(deja)] if not fd.empty else fd
    return pd.concat([odds, reste], ignore_index=True)
