import json
import os

import pytest
from fastapi.testclient import TestClient

from missa.dixon_coles import matrice_scores


@pytest.fixture
def client(tmp_path, monkeypatch):
    P = matrice_scores(1.5, 1.0, -0.1, 9).tolist()
    m = lambda i: {"id": f"m{i}", "disponible": True, "championnat": "E0",
                   "coup_envoi": "2099-01-01T15:00:00", "domicile": f"A{i}", "exterieur": f"B{i}",
                   "selection_haute_confiance": "1N" if i == 1 else None,
                   "marches": {}, "matrice": P,
                   "jumeau": {"matrice": P, "part_1mt": [0.418, 0.0086], "corners": [5.3, 4.4, 56.0, 0.087],
                              "cartons": [1.9, 2.1, 0.33]}}
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"genere_le": "x", "avertissement": "y",
                             "championnats": [{"code": "E0", "nom": "PL", "matchs": [m(1), m(2)]}]}))
    monkeypatch.setenv("MISSA_PRONOSTICS", str(f))
    monkeypatch.setenv("MISSA_BASE", str(tmp_path / "t.db"))
    monkeypatch.setenv("MISSA_CLE_ADMIN", "secret")
    import importlib, api.main
    importlib.reload(api.main)
    return TestClient(api.main.app)


def test_listes(client):
    assert client.get("/championnats").json()[0]["nb_matchs"] == 2
    r = client.get("/matchs", params={"haute_confiance": True}).json()
    assert len(r["championnats"][0]["matchs"]) == 1
    assert "matrice" not in r["championnats"][0]["matchs"][0]
    assert "matrice" in client.get("/matchs/m1").json()


def test_combinaison(client):
    r = client.post("/combinaison", json={"selections": [
        {"match_id": "m1", "selection": "1", "cote": 1.8},
        {"match_id": "m2", "selection": "plus_2.5", "cote": 2.0}]}).json()
    assert 0 < r["proba"] < 1 and r["cote_bookmaker"] == pytest.approx(3.6)
    assert client.post("/combinaison", json={"selections": [
        {"match_id": "zz", "selection": "1"}]}).status_code == 404


def test_pronostic_admin(client):
    body = {"pronostiqueur": "Expert", "match_id": "m1", "selection": "1", "cote": 2.0}
    assert client.post("/pronostics", json=body).status_code == 403
    assert client.post("/pronostics", json=body, headers={"x-cle-admin": "secret"}).status_code == 201
    assert client.post("/pronostics", json=body, headers={"x-cle-admin": "secret"}).status_code == 409
    assert client.get("/pronostiqueurs").json()[0]["nom"] == "Expert"


def test_probabilite_jumeau(client):
    r = client.post("/probabilite", json={"selections": [
        {"match_id": "m1", "selection": "DC:1N & OU:3.5:moins"},
        {"match_id": "m2", "selection": "CORNERS_OU:9.5:plus"}]}).json()
    assert 0 < r["proba"] < 1
    base = client.post("/probabilite", json={"selections": [{"match_id": "m1", "selection": "1X2:1"}]}).json()
    mod = client.post("/probabilite", json={"selections": [{"match_id": "m1", "selection": "1X2:1"}],
                                            "modulations": {"m1": {"attaque_dom": 0.8}}}).json()
    assert mod["proba"] < base["proba"]
    assert client.post("/probabilite", json={"selections": [
        {"match_id": "m1", "selection": "INCONNU:1"}]}).status_code == 400
