"""Chargement des fichiers football-data.co.uk (usage privé / développement uniquement).

URL : https://football-data.co.uk/mmz4281/{saison}/{code}.csv  (saison « 2425 » = 2024/25)
Les cotes « avant clôture » sont relevées le vendredi (week-end) ou le mardi (semaine) ;
les cotes de clôture ont le même code suivi de « C » (PSCH, AvgCH…).
"""
from __future__ import annotations

import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "cache"
URL = "https://football-data.co.uk/mmz4281/{saison}/{code}.csv"

CHAMPIONNATS = {
    "E0": "Angleterre - Premier League", "E1": "Angleterre - Championship",
    "E2": "Angleterre - League One", "E3": "Angleterre - League Two",
    "EC": "Angleterre - National League", "SC0": "Écosse - Premiership",
    "SC1": "Écosse - Championship", "SC2": "Écosse - League One", "SC3": "Écosse - League Two",
    "SP1": "Espagne - Liga", "SP2": "Espagne - Liga 2", "I1": "Italie - Serie A",
    "I2": "Italie - Serie B", "D1": "Allemagne - Bundesliga", "D2": "Allemagne - 2. Bundesliga",
    "F1": "France - Ligue 1", "F2": "France - Ligue 2", "N1": "Pays-Bas - Eredivisie",
    "B1": "Belgique - Pro League", "P1": "Portugal - Liga", "T1": "Turquie - Süper Lig",
    "G1": "Grèce - Super League",
}
GRANDS_CHAMPIONNATS = ("E0", "SP1", "I1", "D1", "F1")

# Ordre de préférence des sources de cotes. Pinnacle est signalé peu fiable dans
# football-data depuis le 23/07/2025 : on lui préfère alors la moyenne du marché.
DATE_PINNACLE_PEU_FIABLE = pd.Timestamp("2025-07-23")


def telecharger(code: str, saison: str, cache: Path = CACHE, pause: float = 1.5) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    f = cache / f"{code}_{saison}.csv"
    if not f.exists() or f.stat().st_size == 0:
        req = urllib.request.Request(URL.format(saison=saison, code=code),
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            f.write_bytes(r.read())
        time.sleep(pause)
    return f


def _trio(df: pd.DataFrame, prefixe: str) -> np.ndarray | None:
    cols = [f"{prefixe}H", f"{prefixe}D", f"{prefixe}A"]
    if all(c in df.columns for c in cols):
        return df[cols].to_numpy(float)
    return None


def _choisir_cotes(df: pd.DataFrame, prefixes: list[str]) -> np.ndarray:
    """Pour chaque ligne, première source de cotes disponible dans l'ordre donné."""
    out = np.full((len(df), 3), np.nan)
    for p in prefixes:
        t = _trio(df, p)
        if t is None:
            continue
        manque = np.isnan(out).any(axis=1) & ~np.isnan(t).any(axis=1)
        out[manque] = t[manque]
    return out


def _paire(df: pd.DataFrame, paires: list[tuple[str, str]]) -> np.ndarray:
    """Cotes d'un marché à 2 issues : première paire de colonnes disponible par ligne."""
    out = np.full((len(df), 2), np.nan)
    for a, b in paires:
        if a in df.columns and b in df.columns:
            t = df[[a, b]].apply(pd.to_numeric, errors="coerce").to_numpy(float)
            manque = np.isnan(out).any(axis=1) & ~np.isnan(t).any(axis=1)
            out[manque] = t[manque]
    return out


def extraire_cotes(df: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    """Cotes 1X2 et plus/moins 2,5 : avant clôture (ouv), clôture (clo) et meilleure (max)."""
    out = pd.DataFrame(index=df.index)
    pinnacle_ok = (dates < DATE_PINNACLE_PEU_FIABLE).to_numpy()[:, None]
    ouv_pin, ouv_marche = _choisir_cotes(df, ["PS", "P"]), _choisir_cotes(df, ["Avg", "BbAv", "B365"])
    clo_pin, clo_marche = _choisir_cotes(df, ["PSC"]), _choisir_cotes(df, ["AvgC", "B365C"])
    ouv = np.where(pinnacle_ok & ~np.isnan(ouv_pin), ouv_pin, ouv_marche)
    clo = np.where(pinnacle_ok & ~np.isnan(clo_pin), clo_pin, clo_marche)
    meilleure = _choisir_cotes(df, ["Max", "BbMx"])
    for i, s in enumerate("HDA"):
        out[f"ouv_{s}"], out[f"clo_{s}"], out[f"max_{s}"] = ouv[:, i], clo[:, i], meilleure[:, i]
    ou_ouv_pin = _paire(df, [("P>2.5", "P<2.5")])
    ou_ouv = _paire(df, [("Avg>2.5", "Avg<2.5"), ("BbAv>2.5", "BbAv<2.5"), ("B365>2.5", "B365<2.5")])
    ou_clo_pin = _paire(df, [("PC>2.5", "PC<2.5")])
    ou_clo = _paire(df, [("AvgC>2.5", "AvgC<2.5"), ("B365C>2.5", "B365C<2.5")])
    ou_max = _paire(df, [("Max>2.5", "Max<2.5"), ("BbMx>2.5", "BbMx<2.5")])
    ou_ouv = np.where(pinnacle_ok & ~np.isnan(ou_ouv_pin), ou_ouv_pin, ou_ouv)
    ou_clo = np.where(pinnacle_ok & ~np.isnan(ou_clo_pin), ou_clo_pin, ou_clo)
    for i, s in enumerate(("plus25", "moins25")):
        out[f"ouv_{s}"], out[f"clo_{s}"], out[f"max_{s}"] = ou_ouv[:, i], ou_clo[:, i], ou_max[:, i]
    return out


def _lire(f) -> pd.DataFrame:
    df = pd.read_csv(f, encoding="utf-8-sig", on_bad_lines="skip")
    df.columns = [c.lstrip("\ufeff") for c in df.columns]
    df = df.dropna(subset=["HomeTeam", "AwayTeam"]).copy()
    df["date"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")
    return df.dropna(subset=["date"])


def charger_saison(code: str, saison: str, cache: Path = CACHE) -> pd.DataFrame:
    df = _lire(telecharger(code, saison, cache)).dropna(subset=["FTHG", "FTAG"])
    out = pd.DataFrame({
        "championnat": code, "saison": saison, "date": df["date"],
        "domicile": df["HomeTeam"].str.strip(), "exterieur": df["AwayTeam"].str.strip(),
        "buts_dom": df["FTHG"].astype(int), "buts_ext": df["FTAG"].astype(int),
    })
    out = out.join(extraire_cotes(df, df["date"]))
    for nom, col in (("tirs_dom", "HS"), ("tirs_ext", "AS"), ("cadres_dom", "HST"),
                     ("cadres_ext", "AST"), ("mt_dom", "HTHG"), ("mt_ext", "HTAG"),
                     ("corners_dom", "HC"), ("corners_ext", "AC"), ("jaunes_dom", "HY"),
                     ("jaunes_ext", "AY"), ("rouges_dom", "HR"), ("rouges_ext", "AR")):
        out[nom] = pd.to_numeric(df[col], errors="coerce") if col in df.columns else np.nan
    return out.reset_index(drop=True)


URL_CALENDRIER = "https://www.football-data.co.uk/fixtures.csv"


def charger_calendrier(source=URL_CALENDRIER) -> pd.DataFrame:
    """Prochains matchs avec leurs cotes (football-data, mis à jour vendredi et mardi)."""
    if isinstance(source, str) and source.startswith("http"):
        req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            import io
            source = io.BytesIO(r.read())
    df = _lire(source)
    heure = df["Time"].fillna("15:00") if "Time" in df.columns else "15:00"
    out = pd.DataFrame({
        "championnat": df["Div"].str.strip(), "date": df["date"],
        "coup_envoi": pd.to_datetime(df["Date"] + " " + heure, dayfirst=True, format="mixed",
                                     errors="coerce"),
        "domicile": df["HomeTeam"].str.strip(), "exterieur": df["AwayTeam"].str.strip(),
    })
    return out.join(extraire_cotes(df, df["date"])).reset_index(drop=True)


def charger(codes=GRANDS_CHAMPIONNATS, saisons=None, cache: Path = CACHE) -> pd.DataFrame:
    if saisons is None:
        saisons = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
    parts = []
    for c in codes:
        for s in saisons:
            try:
                parts.append(charger_saison(c, s, cache))
            except Exception as e:  # saison absente, réseau…
                print(f"[donnees] {c} {s} ignoré : {e}")
    df = pd.concat(parts, ignore_index=True).sort_values(["date", "championnat"])
    df["resultat"] = np.select([df.buts_dom > df.buts_ext, df.buts_dom == df.buts_ext], [0, 1], 2)
    return df.reset_index(drop=True)
