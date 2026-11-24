"""Parité du jumeau numérique de l'application web avec le moteur Python.

Nécessite numpy, scipy (requirements.txt) et Node.js pour exécuter le harnais.
Le test est ignoré automatiquement si l'un d'eux manque.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

RACINE = Path(__file__).resolve().parent.parent


def test_parite_navigateur_python():
    if not shutil.which("node"):
        pytest.skip("Node.js absent : parité navigateur non vérifiée")
    r = subprocess.run([sys.executable, str(RACINE / "web" / "tests" / "parite.py")],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Parité navigateur" in r.stdout
