import numpy as np
import pytest

from missa.dixon_coles import matrice_scores
from missa.jumeau import JumeauMatch, catalogue, proba_combine


@pytest.fixture
def J():
    return JumeauMatch(matrice_scores(1.7, 1.0, -0.1, 9), corners=(5.8, 4.1, 56.0, 0.09), cartons=(1.8, 2.2, 0.4))


def test_grilles_normalisees(J):
    for comp in ("buts", "corners", "cartons"):
        assert J.grille(comp)[0].sum() == pytest.approx(1.0)


@pytest.mark.parametrize("groupe", ["1X2", "1X2@MT1", "1X2@MT2", "CORNERS_1X2", "CARTONS_1X2"])
def test_resultats_somment_a_un(J, groupe):
    assert sum(J.proba(f"{groupe}:{o}") for o in "1N2") == pytest.approx(1.0)


def test_mi_temps_fin_de_match(J):
    total = sum(J.proba(f"MTFT:{a}/{b}") for a in "1N2" for b in "1N2")
    assert total == pytest.approx(1.0)
    # cohérence : somme sur la mi-temps = résultat final
    assert sum(J.proba(f"MTFT:{a}/1") for a in "1N2") == pytest.approx(J.proba("1X2:1"))


def test_score_final_conserve(J):
    assert J.proba("1X2:1") == pytest.approx(J.matrice[np.triu_indices(10, 1)[::-1]].sum())
    assert J.proba("CS:1-0") == pytest.approx(J.matrice[1, 0])


def test_buts_par_mi_temps(J):
    # environ 44 % des buts en 1re mi-temps
    m1 = sum(n * J.proba(f"TG@MT1:{n}") for n in range(10))
    m = sum(n * J.proba(f"TG:{n}") for n in range(19))
    assert m1 / m == pytest.approx(0.44, abs=0.015)
    assert J.proba("OU@MT1:0.5:plus") < J.proba("OU:0.5:plus")


def test_combinaisons_et_ou(J):
    a, b = J.proba("1X2:1"), J.proba("OU:2.5:plus")
    et = J.proba("1X2:1 & OU:2.5:plus")
    assert J.proba("1X2:1 | OU:2.5:plus") == pytest.approx(a + b - et)
    assert J.proba(["1X2:1", "OU:2.5:plus"]) == pytest.approx(et)
    assert J.proba("1X2:1 & 1X2:2") == 0
    # buts et corners indépendants : produit
    assert J.proba("1X2:1 & CORNERS_OU:9.5:plus") == pytest.approx(a * J.proba("CORNERS_OU:9.5:plus"))
    with pytest.raises(ValueError):
        J.proba("1X2:1 | CORNERS_OU:9.5:plus")


def test_marges_et_handicaps(J):
    assert J.proba("HCP3:-1:N") == pytest.approx(J.proba("MARGE:dom1"))
    assert J.proba("HCP2:-1.5:1") == pytest.approx(J.proba("MARGE:dom2") + J.proba("MARGE:dom3+"))
    assert J.proba("SANS_ENC:dom") == pytest.approx(J.proba("1X2:1 & CLEAN:dom:oui"))


def test_corners_et_cartons(J):
    m = sum(n * J.proba(f"CORNERS_TOTAL:{n}") for n in range(51))
    assert m == pytest.approx(9.9, abs=0.05)
    assert J.proba("CARTONS_OU:3.5:plus") + J.proba("CARTONS_OU:3.5:moins") == pytest.approx(1.0)


def test_modulation(J):
    K = J.moduler(attaque_dom=0.8)
    assert K.proba("1X2:1") < J.proba("1X2:1")
    assert K.proba("OU:2.5:plus") < J.proba("OU:2.5:plus")
    assert J.moduler(cartons=1.3).proba("CARTONS_OU:4.5:plus") > J.proba("CARTONS_OU:4.5:plus")


def test_catalogue_complet(J):
    n = 0
    for groupe, titre, options in catalogue():
        for code, _ in options:
            p = J.proba(code)
            assert 0 <= p <= 1
            n += 1
    assert n > 120


def test_combine_plusieurs_matchs(J):
    r = proba_combine([("a", "1X2:1"), ("b", "BTTS:oui"), ("a", "OU:1.5:plus")], {"a": J, "b": J})
    assert r["proba"] == pytest.approx(J.proba("1X2:1 & OU:1.5:plus") * J.proba("BTTS:oui"))
    assert r["meme_match"]


def test_regle_un_par_match(J):
    with pytest.raises(ValueError):
        proba_combine([("a", "1X2:1"), ("a", "BTTS:oui")], {"a": J}, un_par_match=True)
    assert proba_combine([("a", "1X2:1 & BTTS:oui")], {"a": J}, un_par_match=True)["proba"] > 0
