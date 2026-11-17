# Résultats du backtest

Matchs d'entraînement : 7167 — matchs de test (jamais vus) : 5728


## 1. Retrait de marge (cotes de clôture, log-loss : plus bas = mieux)

| Méthode | log-loss | RPS |
|---|---|---|
| egale | 0.96739 | 0.19481 |
| proportionnelle | 0.96715 | 0.19473 |
| puissance | 0.96716 | 0.19473 |
| odds_ratio | 0.96720 | 0.19475 |
| shin | 0.96717 | 0.19474 |

## 2. Précision sur les saisons de test

| Source | RPS | log-loss | Brier |
|---|---|---|---|
| Fréquences moyennes (naïf) | 0.23056 | 1.07414 | 0.65010 |
| Elo | 0.19957 | 0.98418 | 0.58637 |
| Dixon-Coles | 0.20027 | 0.98926 | 0.58791 |
| Marché avant clôture | 0.19324 | 0.96297 | 0.57234 |
| **Combinaison MISSA** | 0.19315 | 0.96251 | 0.57204 |
| Marché à la clôture (référence) | 0.19261 | 0.96072 | 0.57089 |

Poids appris : {'marche_ouv': 1.055, 'dixon_coles': -0.061, 'elo': -0.016}


## 3. Paris simulés (meilleure cote avant clôture, mise de 1)

CLV = valeur obtenue par rapport à la cote juste de clôture (meilleur indicateur de rentabilité future).

| Probabilités utilisées | Seuil EV | Paris | CLV moyen | Rendement réel | Cote moy. |
|---|---|---|---|---|---|
| Marché avant clôture | 2% | 943 | +3.59% | -1.66% | 4.22 |
| Marché avant clôture | 5% | 179 | +7.05% | -13.57% | 6.60 |
| Combinaison MISSA | 2% | 2056 | +1.42% | -1.03% | 5.00 |
| Combinaison MISSA | 5% | 544 | +3.59% | -7.44% | 6.73 |
| Dixon-Coles seul | 2% | 7038 | -2.45% | -7.21% | 4.50 |
| Dixon-Coles seul | 5% | 5778 | -2.71% | -9.28% | 4.69 |
