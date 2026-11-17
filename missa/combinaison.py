"""Combinaison des sources de probabilités (marché, Dixon-Coles, Elo, pronostiqueurs…).

Pool logarithmique appris :  score_k = Σ_s w_s · log p_s,k + b_k  →  softmax.
Chaque source a UN poids (interprétable : « combien on lui fait confiance »).
Les poids sont appris sur des saisons passées puis évalués sur des saisons non vues.
Si une source n'apporte rien, son poids tend vers 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize


def _softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


@dataclass
class PoolLogarithmique:
    sources: list
    l2: float = 1e-3
    poids: np.ndarray | None = None
    biais: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def _scores(self, X, w, b):
        return np.einsum("s,nsk->nk", w, X) + b

    def ajuster(self, sources_probas: dict, resultats) -> "PoolLogarithmique":
        X = np.stack([np.log(np.clip(sources_probas[s], 1e-6, 1)) for s in self.sources], axis=1)
        y = np.asarray(resultats, int)
        S = len(self.sources)
        n = len(y)

        def f(theta):
            w, b = theta[:S], np.r_[0.0, theta[S:]]
            p = _softmax(self._scores(X, w, b))
            loss = -np.mean(np.log(np.clip(p[np.arange(n), y], 1e-12, 1)))
            return loss + self.l2 * np.sum((w - self._prior()) ** 2)

        theta0 = np.r_[self._prior(), 0.0, 0.0]
        res = minimize(f, theta0, method="L-BFGS-B")
        self.poids = res.x[:S]
        self.biais = np.r_[0.0, res.x[S:]]
        return self

    def _prior(self):
        # par défaut : confiance totale dans la 1re source (le marché), 0 dans les autres
        return np.r_[1.0, np.zeros(len(self.sources) - 1)]

    def predire(self, sources_probas: dict) -> np.ndarray:
        X = np.stack([np.log(np.clip(sources_probas[s], 1e-6, 1)) for s in self.sources], axis=1)
        return _softmax(self._scores(X, self.poids, self.biais))

    def resume(self) -> dict:
        return {s: round(float(w), 3) for s, w in zip(self.sources, self.poids)}
