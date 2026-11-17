"""Mesures de précision des probabilités 1X2 (résultat : 0 = domicile, 1 = nul, 2 = extérieur)."""
from __future__ import annotations

import numpy as np


def _onehot(resultats) -> np.ndarray:
    r = np.asarray(resultats, int)
    o = np.zeros((len(r), 3))
    o[np.arange(len(r)), r] = 1
    return o


def rps(probas, resultats) -> float:
    """Ranked Probability Score moyen (0 = parfait)."""
    p = np.cumsum(np.asarray(probas, float), axis=1)
    o = np.cumsum(_onehot(resultats), axis=1)
    return float(np.mean(np.sum((p - o) ** 2, axis=1) / 2))


def log_loss(probas, resultats) -> float:
    p = np.clip(np.asarray(probas, float), 1e-12, 1)
    return float(-np.mean(np.log(p[np.arange(len(p)), np.asarray(resultats, int)])))


def brier(probas, resultats) -> float:
    return float(np.mean(np.sum((np.asarray(probas, float) - _onehot(resultats)) ** 2, axis=1)))


def resume(probas, resultats) -> dict:
    return {"n": len(resultats), "rps": rps(probas, resultats),
            "log_loss": log_loss(probas, resultats), "brier": brier(probas, resultats)}
