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

CHAMPIONNATS = {"E0": "Premier League", "SP1": "Liga", "I1": "Serie A",
                "D1": "Bundesliga", "F1": "Ligue 1"}

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


def charger_saison(code: str, saison: str, cache: Path = CACHE) -> pd.DataFrame:
    f = telecharger(code, saison, cache)
    df = pd.read_csv(f, encoding="utf-8-sig", on_bad_lines="skip")
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
    df["date"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])
    out = pd.DataFrame({
        "championnat": code, "saison": saison, "date": df["date"],
        "domicile": df["HomeTeam"].str.strip(), "exterieur": df["AwayTeam"].str.strip(),
        "buts_dom": df["FTHG"].astype(int), "buts_ext": df["FTAG"].astype(int),
    })
    pinnacle_ok = (df["date"] < DATE_PINNACLE_PEU_FIABLE).to_numpy()
    # Cotes d'ouverture (relevées avant le match) et de clôture
    ouv_pin = _choisir_cotes(df, ["PS", "P"])
    ouv_marche = _choisir_cotes(df, ["Avg", "BbAv", "B365"])
    clo_pin = _choisir_cotes(df, ["PSC"])
    clo_marche = _choisir_cotes(df, ["AvgC", "B365C"])
    ouv = np.where(pinnacle_ok[:, None] & ~np.isnan(ouv_pin), ouv_pin, ouv_marche)
    clo = np.where(pinnacle_ok[:, None] & ~np.isnan(clo_pin), clo_pin, clo_marche)
    meilleure = _choisir_cotes(df, ["Max", "BbMx"])
    for i, s in enumerate("HDA"):
        out[f"ouv_{s}"] = ouv[:, i]
        out[f"clo_{s}"] = clo[:, i]
        out[f"max_{s}"] = meilleure[:, i]
    for nom, col in (("tirs_dom", "HS"), ("tirs_ext", "AS"), ("cadres_dom", "HST"),
                     ("cadres_ext", "AST")):
        out[nom] = pd.to_numeric(df[col], errors="coerce") if col in df.columns else np.nan
    return out.reset_index(drop=True)


def charger(codes=tuple(CHAMPIONNATS), saisons=None, cache: Path = CACHE) -> pd.DataFrame:
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
