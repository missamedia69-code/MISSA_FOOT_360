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

## 4. Plus/moins 2,5 buts (log-loss, plus bas = mieux)

- Dixon-Coles : 0.68251
- Marché avant clôture : 0.66723
- Marché à la clôture : 0.66382

## 5. Mode haute confiance (sélection la plus probable, saisons de test)

Taux réel = part des sélections réellement gagnantes. Rendement = en pariant à la meilleure cote du marché (quand elle est connue).


### Résultat 1X2

| Probabilité annoncée | Part des matchs | Sélections | Taux réel | Cote moy. | Rendement |
|---|---|---|---|---|---|
| 50%–55% | 11.7% | 670 | **53.4%** | 1.88 | +0.3% |
| 55%–60% | 11.8% | 678 | **57.5%** | 1.73 | -0.4% |
| 60%–65% | 7.5% | 429 | **62.5%** | 1.59 | -0.9% |
| 65%–70% | 7.0% | 401 | **71.6%** | 1.47 | +5.4% |
| 70%–75% | 5.4% | 310 | **77.4%** | 1.38 | +6.8% |
| 75%–80% | 3.4% | 194 | **76.3%** | 1.29 | -1.8% |
| 80%–85% | 2.3% | 131 | **86.3%** | 1.22 | +4.9% |
| 85%–90% | 0.9% | 53 | **92.5%** | 1.15 | +6.5% |
| 90%–95% | 0.4% | 25 | **88.0%** | 1.10 | -3.1% |
| 95%–100% | 0.0% | 1 | **100.0%** | 1.06 | +6.0% |

### Double chance

| Probabilité annoncée | Part des matchs | Sélections | Taux réel | Cote moy. | Rendement |
|---|---|---|---|---|---|
| 65%–70% | 5.6% | 320 | **68.4%** | — | — |
| 70%–75% | 34.0% | 1947 | **71.9%** | — | — |
| 75%–80% | 22.2% | 1269 | **78.7%** | — | — |
| 80%–85% | 16.5% | 946 | **84.0%** | — | — |
| 85%–90% | 13.1% | 751 | **90.4%** | — | — |
| 90%–95% | 7.4% | 425 | **94.8%** | — | — |
| 95%–100% | 1.2% | 70 | **94.3%** | — | — |

### Plus/moins 2,5 buts

| Probabilité annoncée | Part des matchs | Sélections | Taux réel | Cote moy. | Rendement |
|---|---|---|---|---|---|
| 50%–55% | 35.0% | 2004 | **53.6%** | 1.87 | +0.3% |
| 55%–60% | 30.9% | 1769 | **59.5%** | 1.72 | +2.2% |
| 60%–65% | 18.4% | 1055 | **60.9%** | 1.58 | -4.0% |
| 65%–70% | 9.3% | 530 | **69.4%** | 1.46 | +1.6% |
| 70%–75% | 4.8% | 273 | **69.2%** | 1.36 | -5.9% |
| 75%–80% | 1.2% | 67 | **76.1%** | 1.27 | -3.1% |
| 80%–85% | 0.4% | 23 | **95.7%** | 1.21 | +16.0% |
| 85%–90% | 0.1% | 7 | **100.0%** | 1.14 | +13.7% |

### Les deux équipes marquent

| Probabilité annoncée | Part des matchs | Sélections | Taux réel | Cote moy. | Rendement |
|---|---|---|---|---|---|
| 50%–55% | 44.9% | 2574 | **52.0%** | — | — |
| 55%–60% | 32.2% | 1845 | **56.4%** | — | — |
| 60%–65% | 16.6% | 950 | **64.7%** | — | — |
| 65%–70% | 5.1% | 292 | **62.7%** | — | — |
| 70%–75% | 0.8% | 48 | **50.0%** | — | — |
| 75%–80% | 0.1% | 6 | **66.7%** | — | — |
| 80%–85% | 0.1% | 4 | **50.0%** | — | — |
| 85%–90% | 0.1% | 3 | **100.0%** | — | — |
| 90%–95% | 0.1% | 5 | **80.0%** | — | — |
| 95%–100% | 0.0% | 1 | **0.0%** | — | — |

## 6. Fiabilité des probabilités 1X2 (annoncé vs observé)

| Tranche | Sélections | Annoncé | Observé |
|---|---|---|---|
| 0%–10% | 581 | 7.3% | 5.2% |
| 10%–20% | 2624 | 15.8% | 14.1% |
| 20%–30% | 6230 | 25.5% | 25.5% |
| 30%–40% | 3031 | 34.1% | 33.5% |
| 40%–50% | 1826 | 44.7% | 46.4% |
| 50%–60% | 1348 | 55.0% | 55.5% |
| 60%–70% | 830 | 64.8% | 66.9% |
| 70%–80% | 504 | 74.3% | 77.0% |
| 80%–90% | 184 | 83.7% | 88.0% |
| 90%–100% | 26 | 91.6% | 88.5% |
