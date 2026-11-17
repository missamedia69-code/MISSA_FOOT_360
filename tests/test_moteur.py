import numpy as np
import pandas as pd
import pytest

from missa import marge, evaluation, valeur
from missa.dixon_coles import DixonColes, matrice_scores, marches
from missa.elo import Elo
from missa.pronostiqueurs import Pronostic, evaluer
from missa.combinaison import PoolLogarithmique


# --- Retrait de marge : exemples des articles de football-data -------------------------

def test_marge_1x2():
    assert marge.marge([1.44, 4.42, 6.25]) == pytest.approx(0.08, abs=0.002)


def test_proportionnelle_exemple_buchdahl():
    # 1,5 / 5 / 7,5 avec 8 % de marge -> 1,44 / 4,42 / 6,25
    p = marge.proportionnelle([1.5 / 1.04, 5 / (1 + 0.08 * 5 / 3), 7.5 / 1.2])
    assert 1 / p == pytest.approx([1.5, 5, 7.5], rel=1e-3)


def test_abrams_exemple_de():
    # 1,179 / 5,5 -> vraies cotes 1,2 / 6
    f, l = marge.abrams(1.179, 5.5)
    assert f == pytest.approx(1.2, abs=0.002)
    assert l == pytest.approx(6.0, abs=0.01)


@pytest.mark.parametrize("m", marge.METHODES)
def test_methodes_somment_a_un(m):
    p = marge.probabilites([1.9, 3.6, 4.2], m)
    assert p.sum() == pytest.approx(1.0)
    assert np.all(p > 0)


@pytest.mark.parametrize("m", ["proportionnelle", "puissance", "odds_ratio", "shin"])
def test_biais_favori_outsider(m):
    # ces méthodes retirent plus de marge à l'outsider que la méthode égale
    cotes = [1.30, 5.50, 10.0]
    assert marge.probabilites(cotes, m)[2] < marge.egale(cotes)[2]


# --- Dixon-Coles ------------------------------------------------------------------------

def test_matrice_somme_et_correction():
    P0 = matrice_scores(1.4, 1.1, 0.0)
    P = matrice_scores(1.4, 1.1, -0.13)
    assert P.sum() == pytest.approx(1.0)
    assert P[0, 0] > P0[0, 0] and P[1, 1] > P0[1, 1]   # rho < 0 : plus de 0-0 et 1-1
    m = marches(P)
    assert m["1"] + m["N"] + m["2"] == pytest.approx(1.0)
    assert m["plus_2.5"] + m["moins_2.5"] == pytest.approx(1.0)


def test_btts_independant():
    P = matrice_scores(1.1, 1.9, 0.0, max_buts=15)
    assert marches(P)["btts_oui"] == pytest.approx(0.567, abs=0.002)  # exemple opisthokonta


def test_dixon_coles_retrouve_les_forces():
    rng = np.random.default_rng(0)
    equipes = [f"E{i}" for i in range(10)]
    att = np.linspace(-0.4, 0.4, 10)
    lignes = []
    d0 = pd.Timestamp("2020-01-01")
    for r in range(8):
        for i in range(10):
            for j in range(10):
                if i != j:
                    lam = np.exp(0.3 + att[i] - att[j] * 0.5)
                    mu = np.exp(att[j] - att[i] * 0.5)
                    lignes.append((d0 + pd.Timedelta(days=r * 40), equipes[i], equipes[j],
                                   rng.poisson(lam), rng.poisson(mu)))
    df = pd.DataFrame(lignes, columns=["date", "domicile", "exterieur", "buts_dom", "buts_ext"])
    m = DixonColes(xi=0.0).ajuster(df, pd.Timestamp("2021-06-01"))
    assert m.domicile == pytest.approx(0.3, abs=0.1)
    assert np.corrcoef(m.attaque, att)[0, 1] > 0.9
    pr = m.predire("E9", "E0")
    assert pr["1"] > 0.6


# --- Elo ----------------------------------------------------------------------------------

def test_elo_exemples_wikipedia():
    e = Elo(avantage_domicile=0)
    assert e.attendu("A", "B") == pytest.approx(0.5)
    assert Elo.multiplicateur(3) == pytest.approx(1.75)
    assert Elo.multiplicateur(5) == pytest.approx(2.0)
    e.mettre_a_jour("A", "B", 2, 0)
    assert e.note("A") > 1500 > e.note("B")
    assert e.note("A") + e.note("B") == pytest.approx(3000)


# --- Évaluation ---------------------------------------------------------------------------

def test_rps_exemple():
    assert evaluation.rps([[0.6, 0.3, 0.1]], [1]) == pytest.approx(0.185)
    assert evaluation.rps([[1, 0, 0]], [0]) == 0
    assert evaluation.brier([[1 / 3] * 3], [0]) == pytest.approx(0.6667, abs=1e-4)


# --- Valeur / pronostiqueurs --------------------------------------------------------------

def test_clv_exemple_buchdahl():
    # cote 1,80 jouée, clôture 1,65 avec 3 % de marge -> ≈ +5,9 %
    assert valeur.clv(1.80, 1.65 * 1.03) == pytest.approx(0.059, abs=0.001)


def test_retention_et_kelly():
    assert valeur.valeur_corrigee(0.55, 2.0, 48) < valeur.valeur_corrigee(0.55, 2.0, 0.5)
    assert valeur.kelly_fractionnaire(0.4, 2.0) == 0.0
    assert 0 < valeur.kelly_fractionnaire(0.55, 2.0) <= 0.02


def test_pronostiqueur_talent_vs_hasard():
    rng = np.random.default_rng(1)
    # proba juste de clôture 0,5 -> cote juste 2,0
    bon = [Pronostic("A", str(i), "1", 2.0 * (1 + rng.normal(0.04, 0.05)), 0.5) for i in range(100)]
    hasard = [Pronostic("B", str(i), "1", 2.0 * (1 + rng.normal(0.0, 0.05)), 0.5) for i in range(100)]
    triche = [Pronostic("C", str(i), "1", 2.0, 0.5, horodatage_avant_match=False) for i in range(100)]
    assert evaluer(bon)["ajustement"] > 0
    assert evaluer(hasard)["ajustement"] == 0
    assert evaluer(triche)["n"] == 0


def test_pool_ignore_source_inutile():
    rng = np.random.default_rng(2)
    n = 4000
    vrai = rng.dirichlet([5, 3, 3], n)
    y = np.array([rng.choice(3, p=p) for p in vrai])
    bruit = rng.dirichlet([1, 1, 1], n)
    pool = PoolLogarithmique(["marche", "bruit"]).ajuster({"marche": vrai, "bruit": bruit}, y)
    w = pool.resume()
    assert w["marche"] == pytest.approx(1.0, abs=0.15)
    assert abs(w["bruit"]) < 0.1
