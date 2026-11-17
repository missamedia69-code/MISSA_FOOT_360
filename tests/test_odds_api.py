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
