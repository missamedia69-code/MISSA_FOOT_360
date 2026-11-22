from datetime import datetime, timezone

import numpy as np
import pytest

from missa import journal


def v(mid, sel, cote, p=0.5):
    return {"match_id": mid, "championnat": "PL", "coup_envoi": "2099-01-01T15:00:00Z", "domicile": "A",
            "exterieur": "B", "selection": sel, "libelle": sel, "proba": p, "meilleure_cote": cote,
            "bookmaker": "X", "valeur_brute": p * cote - 1}


def test_ajout_sans_doublon():
    jr = []
    assert journal.ajouter(jr, [v("m1", "1", 2.2), v("m2", "plus_2.5", 2.1)]) == 2
    assert journal.ajouter(jr, [v("m1", "1", 2.5)]) == 0      # même pari : on garde la 1re cote vue
    assert jr[0]["meilleure_cote"] == 2.2


def test_cloture_clv_et_gain():
    jr = []
    journal.ajouter(jr, [v("m1", "1", 2.2), v("m2", "plus_2.5", 2.1), v("m3", "N", 3.5)])
    res = {"m1": {"buts_dom": 2, "buts_ext": 0, "clo_H": 1.95, "clo_D": 3.6, "clo_A": 4.2,
                  "clo_plus25": np.nan, "clo_moins25": np.nan},
           "m2": {"buts_dom": 1, "buts_ext": 0, "clo_H": np.nan, "clo_D": np.nan, "clo_A": np.nan,
                  "clo_plus25": 1.9, "clo_moins25": 2.0}}
    assert journal.cloturer(jr, res) == 2
    assert jr[0]["gagne"] and jr[0]["gain"] == pytest.approx(1.2) and jr[0]["clv"] > 0
    assert not jr[1]["gagne"] and jr[1]["gain"] == -1
    r = journal.resume(jr)
    assert r["publies"] == 3 and r["regles"] == 2 and r["en_attente"] == 1
    assert r["rendement"] == pytest.approx(0.1)
    assert journal.cloturer(jr, res) == 0  # pas de double clôture
