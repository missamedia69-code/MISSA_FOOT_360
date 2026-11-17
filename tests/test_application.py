from datetime import datetime, timedelta

import numpy as np
import pytest

from missa import confiance
from missa.dixon_coles import matrice_scores
from missa.pipeline import lambdas_depuis_marche, saisons_precedentes
from missa.pronostiqueurs import Pronostic, ajuster_matrice as ajuster_pronos, evaluer
from missa.selections import Selection, ajuster_matrice, proba_combinaison, proba_selection
from missa.stockage import Stockage
import pandas as pd


@pytest.fixture
def P():
    return matrice_scores(1.6, 1.0, -0.1)


def test_raking_reproduit_les_cibles(P):
    Q = ajuster_matrice(P, [0.5, 0.3, 0.2], 0.45)
    assert [proba_selection(Q, c) for c in ("1", "N", "2")] == pytest.approx([0.5, 0.3, 0.2], abs=1e-6)
    assert proba_selection(Q, "plus_2.5") == pytest.approx(0.45, abs=1e-6)


def test_combinaison_matchs_differents_produit(P):
    m = {"a": P, "b": P}
    r = proba_combinaison([Selection("a", "1"), Selection("b", "N")], m)
    assert r["proba"] == pytest.approx(proba_selection(P, "1") * proba_selection(P, "N"))
    assert r["cote_juste"] == pytest.approx(1 / r["proba"])


def test_combinaison_meme_match_correlee(P):
    r = proba_combinaison([Selection("a", "1", 1.8), Selection("a", "plus_2.5", 1.9)], {"a": P})
    produit = proba_selection(P, "1") * proba_selection(P, "plus_2.5")
    assert r["proba"] != pytest.approx(produit, rel=1e-3)   # corrélation prise en compte
    assert r["proba"] <= min(proba_selection(P, "1"), proba_selection(P, "plus_2.5"))
    assert r["selections_meme_match"] and r["cote_bookmaker"] == pytest.approx(3.42)
    # sélections incompatibles : probabilité nulle
    assert proba_combinaison([Selection("a", "1"), Selection("a", "2")], {"a": P})["proba"] == 0


def test_score_exact(P):
    assert proba_selection(P, "score:1-0") == pytest.approx(P[1, 0])


def test_lambdas_depuis_marche():
    lam, mu = lambdas_depuis_marche([0.55, 0.25, 0.20], 0.55)
    Q = matrice_scores(lam, mu, 0.0)
    assert proba_selection(Q, "1") == pytest.approx(0.55, abs=0.02)


def test_saisons():
    assert saisons_precedentes(pd.Timestamp("2026-11-20")) == ["2425", "2526", "2627"]
    assert saisons_precedentes(pd.Timestamp("2027-03-01")) == ["2425", "2526", "2627"]


def test_confiance_niveau():
    t = confiance.construire({"double_chance": np.array([[0.9, 0.5, 0.6]] * 100)},
                             {"double_chance": np.array([[True, False, True]] * 100)})
    n = confiance.niveau(t, "double_chance", 0.91)
    assert n["haute_confiance"] and n["taux_historique"] == 1.0


# --- pronostiqueurs ------------------------------------------------------------------------

def test_pronostiqueur_talent_ajuste_la_matrice(P):
    rng = np.random.default_rng(1)
    bon = [Pronostic("A", str(i), "1", 2.0 * (1 + rng.normal(0.05, 0.05)), 0.5) for i in range(80)]
    note = evaluer(bon)
    assert note["fiable"] and note["ajustement"] > 0
    Q = ajuster_pronos(P, [("1", note["ajustement"])])
    assert proba_selection(Q, "1") > proba_selection(P, "1")
    hasard = [Pronostic("B", str(i), "1", 2.0 * (1 + rng.normal(0, 0.05)), 0.5) for i in range(80)]
    assert evaluer(hasard)["ajustement"] == 0


def test_stockage_regles(tmp_path):
    s = Stockage(tmp_path / "t.db")
    ko = datetime(2026, 11, 20, 15)
    s.ajouter_pronostic("Expert", "m1", "1", 2.1, ko, maintenant=ko - timedelta(hours=5))
    with pytest.raises(ValueError):  # après le coup d'envoi
        s.ajouter_pronostic("Expert", "m2", "1", 2.1, ko, maintenant=ko + timedelta(minutes=1))
    with pytest.raises(Exception):   # modification interdite
        s.db.execute("UPDATE pronostics SET cote = 3 WHERE match_id = 'm1'")
    with pytest.raises(Exception):   # suppression interdite
        s.db.execute("DELETE FROM pronostics")
    assert s.cloturer_match("m1", {"1x2": [1.9, 3.6, 4.2]}) == 1
    p = s.pronostics("Expert")[0]
    assert p["proba_juste_cloture"] == pytest.approx(0.5, abs=0.05)
    assert s.classement()[0]["nom"] == "Expert"
