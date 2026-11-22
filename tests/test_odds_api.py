import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from missa import odds_api

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def evenement(dom, ext, ko, h2h, ou=None, bookmakers=("pinnacle", "bet365")):
    bks = []
    for i, b in enumerate(bookmakers):
        f = 1 + 0.02 * i
        m = [{"key": "h2h", "outcomes": [{"name": dom, "price": h2h[0] * f}, {"name": "Draw", "price": h2h[1] * f},
                                         {"name": ext, "price": h2h[2] * f}]}]
        if ou:
            m.append({"key": "totals", "outcomes": [{"name": "Over", "price": ou[0] * f, "point": 2.5},
                                                    {"name": "Under", "price": ou[1] * f, "point": 2.5}]})
        bks.append({"key": b, "title": b, "last_update": ko, "markets": m})
    return {"id": dom + ext, "sport_key": "soccer_epl", "commence_time": ko,
            "home_team": dom, "away_team": ext, "bookmakers": bks}


EQUIPES = {"E0": ["Man United", "Nott'm Forest", "Arsenal", "Chelsea"]}


def test_appariement_et_cotes():
    ko = "2099-11-22T15:00:00Z"
    evs = {"soccer_epl": [evenement("Manchester United", "Nottingham Forest", ko, [1.8, 3.8, 4.5], [1.9, 1.95]),
                          evenement("Arsenal", "Inconnu FC", ko, [1.5, 4.2, 6.0])]}
    cal, inconnus = odds_api.vers_calendrier(evs, EQUIPES)
    r = cal.iloc[0]
    assert (r.domicile, r.exterieur, r.championnat) == ("Man United", "Nott'm Forest", "E0")
    assert r.ouv_H == pytest.approx(1.8)            # Pinnacle comme référence
    assert r.max_H == pytest.approx(1.8 * 1.02)     # meilleure cote du marché
    assert r.ouv_plus25 == pytest.approx(1.9)
    assert r.coup_envoi == pd.Timestamp("2099-11-22 15:00:00")
    assert inconnus == ["E0: Inconnu FC"]


def test_fusion_priorite_odds_api():
    d = pd.Timestamp("2099-11-22")
    odds = pd.DataFrame([{"championnat": "E0", "date": d, "coup_envoi": d, "domicile": "Arsenal", "exterieur": "Chelsea", "ouv_H": 2.0}])
    fd = pd.DataFrame([{"championnat": "E0", "date": d, "coup_envoi": d, "domicile": "Arsenal", "exterieur": "Chelsea", "ouv_H": 2.5},
                       {"championnat": "E2", "date": d, "coup_envoi": d, "domicile": "A", "exterieur": "B", "ouv_H": 3.0}])
    f = odds_api.fusionner(odds, fd)
    assert len(f) == 2 and f[f.championnat == "E0"].ouv_H.iloc[0] == 2.0


def test_budget_credits(tmp_path, monkeypatch):
    import publier
    appels = []
    ko = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    def faux(cle, sport, **k):
        appels.append(sport)
        return [evenement("Arsenal", "Chelsea", ko, [2.0, 3.5, 3.8], [1.8, 2.0])], 400

    monkeypatch.setattr(odds_api, "recuperer", faux)
    monkeypatch.setenv("ODDS_API_KEY", "test")
    monkeypatch.setenv("ODDS_API_SPORTS", "soccer_epl")
    monkeypatch.delenv("PUBLICATION_URL", raising=False)
    cal, info = publier.cotes_odds_api(tmp_path)
    assert appels == ["soccer_epl"] and info["credits_restants"] == 400 and len(cal) == 1
    assert json.loads((tmp_path / "cotes_odds_api.json").read_text())["evenements"]["soccer_epl"]
    monkeypatch.delenv("ODDS_API_KEY")
    assert publier.cotes_odds_api(tmp_path) == (None, {"active": False})


def test_choix_automatique(monkeypatch):
    def faux_get(url, params, timeout=30):
        if url.endswith("/sports/"):
            return [{"key": k, "group": "Soccer", "active": True, "has_outrights": False}
                    for k in ("soccer_epl", "soccer_brazil_campeonato", "soccer_mexico_ligamx", "soccer_japan_j_league")] + \
                   [{"key": "soccer_fifa_world_cup_winner", "group": "Soccer", "active": True, "has_outrights": True}]
        sport = url.split("/sports/")[1].split("/")[0]
        return [] if sport == "soccer_epl" else [{"id": "x"}]   # trêve : pas de Premier League
    monkeypatch.setattr(odds_api, "_get", faux_get)
    assert odds_api.choisir_sports("cle", max_sports=2) == ["soccer_brazil_campeonato", "soccer_mexico_ligamx"]
    assert "soccer_japan_j_league" in odds_api.choisir_sports("cle", max_sports=8)


def test_competition_sans_historique():
    evs = {"soccer_uefa_champs_league": [evenement("Real Madrid", "Liverpool", "2099-11-25T20:00:00Z", [2.2, 3.6, 3.2])]}
    evs["soccer_uefa_champs_league"][0]["sport_title"] = "UEFA Champions League"
    cal, _ = odds_api.vers_calendrier(evs, {})
    assert cal.iloc[0].championnat == "soccer_uefa_champs_league"
    assert cal.iloc[0].nom_championnat == "UEFA Champions League"
    from missa.pipeline import Moteur
    r = Moteur().predire(cal)
    m = r["championnats"][0]["matchs"][0]
    assert r["championnats"][0]["nom"] == "UEFA Champions League"
    assert m["methode"] == "Marché" and abs(m["marches"]["1"]["proba"] - 0.42) < 0.03


def test_commission_des_bourses():
    assert odds_api.cote_nette("betfair_ex_eu", 3.0) == pytest.approx(2.9)
    assert odds_api.cote_nette("pinnacle", 3.0) == 3.0
    ev = evenement("Arsenal", "Chelsea", "2099-11-22T15:00:00Z", [2.0, 3.5, 4.0], bookmakers=("pinnacle", "betfair_ex_eu"))
    cal, _ = odds_api.vers_calendrier({"soccer_epl": [ev]}, {"E0": ["Arsenal", "Chelsea"]})
    # Betfair affiche 4,08 mais rapporte net 1 + 3,08 × 0,95 = 3,93 < 4,0 de Pinnacle
    assert cal.iloc[0].max_A == pytest.approx(4.0) and cal.iloc[0].bk_A == "pinnacle"
