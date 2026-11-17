# Validation du jumeau numérique (saisons de test jamais vues)

Matchs de test : 5727. Paramètres estimés sur l'entraînement : part des buts en 1re mi-temps = 0.418 + 0.0086 × buts du match ; corners : dispersion du total k = 56.0, corrélation de répartition = 0.087 ; covariance des cartons = 0.33.

Gain de précision = réduction de l'erreur (score de Brier) par rapport à une prédiction naïve qui annoncerait toujours la fréquence moyenne. Plus c'est haut, mieux c'est.


## 1. Marché par marché

| Groupe | Marché | Sélection | Annoncé (moy.) | Réel | Gain de précision |
|---|---|---|---|---|---|
| Résultat | 1X2 | 1 | 43.9% | 43.2% | +16.7% |
| Résultat | 1X2 | N | 24.7% | 25.3% | +1.8% |
| Résultat | 1X2 | 2 | 31.5% | 31.5% | +15.8% |
| Résultat | Double chance | 1N | 68.5% | 68.5% | +15.8% |
| Résultat | Double chance | 12 | 75.3% | 74.7% | +1.8% |
| Résultat | Double chance | N2 | 56.1% | 56.8% | +16.7% |
| Résultat | Écart de victoire | Dom. par 1 | 20.0% | 21.0% | +2.5% |
| Résultat | Écart de victoire | Dom. par 2 | 12.6% | 12.4% | +3.3% |
| Résultat | Écart de victoire | Dom. par 3+ | 11.2% | 9.9% | +8.6% |
| Résultat | Écart de victoire | Nul | 24.7% | 25.3% | +1.8% |
| Résultat | Écart de victoire | Ext. par 1 | 16.3% | 16.9% | +3.4% |
| Résultat | Écart de victoire | Ext. par 2 | 8.9% | 8.7% | +3.6% |
| Résultat | Écart de victoire | Ext. par 3+ | 6.3% | 5.8% | +7.9% |
| Résultat | Handicap 3 issues (-1 domicile) | 1 | 23.9% | 22.3% | +12.7% |
| Résultat | Handicap 3 issues (-1 domicile) | N | 20.0% | 21.0% | +2.5% |
| Résultat | Handicap 3 issues (-1 domicile) | 2 | 56.1% | 56.8% | +16.7% |
| Résultat | Handicap 3 issues (+1 domicile) | 1 | 68.5% | 68.5% | +15.8% |
| Résultat | Handicap 3 issues (+1 domicile) | N | 16.3% | 16.9% | +3.4% |
| Résultat | Handicap 3 issues (+1 domicile) | 2 | 15.1% | 14.5% | +11.0% |
| Résultat | Handicap -1,5 domicile | Domicile -1,5 | 23.9% | 22.3% | +12.7% |
| Résultat | Handicap -1,5 domicile | Extérieur +1,5 | 76.1% | 77.7% | +12.7% |
| Buts | Plus / moins (match) | Plus de 0,5 | 92.6% | 93.8% | +0.7% |
| Buts | Plus / moins (match) | Moins de 0,5 | 7.4% | 6.2% | +0.7% |
| Buts | Plus / moins (match) | Plus de 1,5 | 76.8% | 77.7% | +2.8% |
| Buts | Plus / moins (match) | Moins de 1,5 | 23.2% | 22.3% | +2.8% |
| Buts | Plus / moins (match) | Plus de 2,5 | 53.6% | 54.1% | +4.7% |
| Buts | Plus / moins (match) | Moins de 2,5 | 46.4% | 45.9% | +4.7% |
| Buts | Plus / moins (match) | Plus de 3,5 | 31.4% | 32.0% | +4.7% |
| Buts | Plus / moins (match) | Moins de 3,5 | 68.6% | 68.0% | +4.7% |
| Buts | Plus / moins (match) | Plus de 4,5 | 16.1% | 16.0% | +3.0% |
| Buts | Plus / moins (match) | Moins de 4,5 | 83.9% | 84.0% | +3.0% |
| Buts | Plus / moins (match) | Plus de 5,5 | 7.4% | 7.1% | +2.5% |
| Buts | Plus / moins (match) | Moins de 5,5 | 92.6% | 92.9% | +2.5% |
| Buts | Les deux équipes marquent | Oui | 53.0% | 55.1% | +1.5% |
| Buts | Les deux équipes marquent | Non | 47.0% | 44.9% | +1.5% |
| Buts | Nombre exact de buts | 0 | 7.4% | 6.2% | +0.7% |
| Buts | Nombre exact de buts | 1 | 15.8% | 16.0% | +1.5% |
| Buts | Nombre exact de buts | 2 | 23.2% | 23.6% | +0.4% |
| Buts | Nombre exact de buts | 3 | 22.2% | 22.2% | -0.5% |
| Buts | Nombre exact de buts | 4 | 15.3% | 16.0% | +0.9% |
| Buts | Nombre exact de buts | 5 | 8.7% | 8.9% | +0.7% |
| Buts | Nombre exact de buts | 6+ | 7.4% | 7.1% | +2.5% |
| Buts | Multibuts | 1-2 | 39.0% | 39.6% | +2.6% |
| Buts | Multibuts | 1-3 | 61.2% | 61.8% | +2.5% |
| Buts | Multibuts | 2-3 | 45.4% | 45.8% | +0.4% |
| Buts | Multibuts | 2-4 | 60.7% | 61.8% | +0.2% |
| Buts | Multibuts | 3-4 | 37.5% | 38.2% | +0.4% |
| Buts | Multibuts | 3-5 | 46.2% | 47.1% | +1.6% |
| Buts | Multibuts | 4-6 | 28.4% | 29.2% | +3.5% |
| Buts | Pair / impair | Pair | 51.1% | 50.7% | -0.1% |
| Buts | Pair / impair | Impair | 48.9% | 49.3% | -0.1% |
| Équipes | Buts du domicile | Plus de 0,5 | 76.4% | 77.5% | +7.9% |
| Équipes | Buts du domicile | Moins de 0,5 | 23.6% | 22.5% | +7.9% |
| Équipes | Buts du domicile | Plus de 1,5 | 44.9% | 45.4% | +10.6% |
| Équipes | Buts du domicile | Moins de 1,5 | 55.1% | 54.6% | +10.6% |
| Équipes | Buts du domicile | Plus de 2,5 | 21.4% | 21.0% | +10.7% |
| Équipes | Buts du domicile | Moins de 2,5 | 78.6% | 79.0% | +10.7% |
| Équipes | Buts de l'extérieur | Plus de 0,5 | 69.2% | 71.3% | +6.3% |
| Équipes | Buts de l'extérieur | Moins de 0,5 | 30.8% | 28.7% | +6.3% |
| Équipes | Buts de l'extérieur | Plus de 1,5 | 35.3% | 36.8% | +9.2% |
| Équipes | Buts de l'extérieur | Moins de 1,5 | 64.7% | 63.2% | +9.2% |
| Équipes | Buts de l'extérieur | Plus de 2,5 | 14.5% | 14.4% | +8.4% |
| Équipes | Buts de l'extérieur | Moins de 2,5 | 85.5% | 85.6% | +8.4% |
| Équipes | Cage inviolée | Domicile n'encaisse pas | 30.8% | 28.7% | +6.3% |
| Équipes | Cage inviolée | Extérieur n'encaisse pas | 23.6% | 22.5% | +7.9% |
| Équipes | Gagne sans encaisser | Domicile | 23.4% | 22.4% | +8.2% |
| Équipes | Gagne sans encaisser | Extérieur | 16.2% | 16.3% | +8.6% |
| Équipes | Marque dans les 2 mi-temps | Domicile | 28.9% | 29.5% | +8.3% |
| Équipes | Marque dans les 2 mi-temps | Extérieur | 21.8% | 22.6% | +6.4% |
| Équipes | Gagne les 2 mi-temps | Domicile | 14.1% | 13.5% | +7.9% |
| Équipes | Gagne les 2 mi-temps | Extérieur | 8.6% | 8.1% | +6.5% |
| Équipes | Gagne au moins une mi-temps | Domicile | 56.6% | 57.9% | +13.1% |
| Équipes | Gagne au moins une mi-temps | Extérieur | 45.1% | 46.8% | +11.5% |
| Mi-temps | 1X2 1re mi-temps | 1 | 33.6% | 34.0% | +7.5% |
| Mi-temps | 1X2 1re mi-temps | N | 40.7% | 40.1% | +1.4% |
| Mi-temps | 1X2 1re mi-temps | 2 | 25.7% | 25.9% | +7.0% |
| Mi-temps | Double chance 1re mi-temps | 1N | 74.3% | 74.1% | +7.0% |
| Mi-temps | Double chance 1re mi-temps | 12 | 59.3% | 59.9% | +1.4% |
| Mi-temps | Double chance 1re mi-temps | N2 | 66.4% | 66.0% | +7.5% |
| Mi-temps | Plus / moins 1re mi-temps | Plus de 0,5 | 70.4% | 71.5% | +1.9% |
| Mi-temps | Plus / moins 1re mi-temps | Moins de 0,5 | 29.6% | 28.5% | +1.9% |
| Mi-temps | Plus / moins 1re mi-temps | Plus de 1,5 | 36.2% | 35.7% | +2.7% |
| Mi-temps | Plus / moins 1re mi-temps | Moins de 1,5 | 63.8% | 64.3% | +2.7% |
| Mi-temps | Plus / moins 1re mi-temps | Plus de 2,5 | 14.4% | 13.0% | +1.9% |
| Mi-temps | Plus / moins 1re mi-temps | Moins de 2,5 | 85.6% | 87.0% | +1.9% |
| Mi-temps | Les deux marquent 1re mi-temps | Oui | 20.4% | 20.3% | +0.9% |
| Mi-temps | Les deux marquent 1re mi-temps | Non | 79.6% | 79.7% | +0.9% |
| Mi-temps | 1X2 2e mi-temps | 1 | 37.0% | 37.5% | +8.8% |
| Mi-temps | 1X2 2e mi-temps | N | 35.0% | 33.5% | +0.8% |
| Mi-temps | 1X2 2e mi-temps | 2 | 28.0% | 29.0% | +7.1% |
| Mi-temps | Plus / moins 2e mi-temps | Plus de 0,5 | 78.7% | 80.9% | +1.3% |
| Mi-temps | Plus / moins 2e mi-temps | Moins de 0,5 | 21.3% | 19.1% | +1.3% |
| Mi-temps | Plus / moins 2e mi-temps | Plus de 1,5 | 46.3% | 47.8% | +2.4% |
| Mi-temps | Plus / moins 2e mi-temps | Moins de 1,5 | 53.7% | 52.2% | +2.4% |
| Mi-temps | Plus / moins 2e mi-temps | Plus de 2,5 | 20.4% | 21.3% | +1.9% |
| Mi-temps | Plus / moins 2e mi-temps | Moins de 2,5 | 79.6% | 78.7% | +1.9% |
| Mi-temps | Mi-temps / fin de match | 1/1 | 27.1% | 26.0% | +10.0% |
| Mi-temps | Mi-temps / fin de match | 1/N | 4.7% | 5.3% | -0.1% |
| Mi-temps | Mi-temps / fin de match | 1/2 | 1.8% | 2.7% | +0.1% |
| Mi-temps | Mi-temps / fin de match | N/1 | 14.4% | 14.4% | +2.6% |
| Mi-temps | Mi-temps / fin de match | N/N | 15.3% | 14.7% | +1.5% |
| Mi-temps | Mi-temps / fin de match | N/2 | 11.0% | 11.1% | +3.2% |
| Mi-temps | Mi-temps / fin de match | 2/1 | 2.3% | 2.8% | +0.4% |
| Mi-temps | Mi-temps / fin de match | 2/N | 4.7% | 5.3% | +0.3% |
| Mi-temps | Mi-temps / fin de match | 2/2 | 18.6% | 17.7% | +9.9% |
| Mi-temps | Mi-temps la plus prolifique | 1re | 30.4% | 28.5% | +0.2% |
| Mi-temps | Mi-temps la plus prolifique | 2e | 43.6% | 45.6% | -0.0% |
| Mi-temps | Mi-temps la plus prolifique | Égalité | 26.0% | 25.9% | +0.2% |
| Combinés officiels | 1X2 + les deux marquent | 1 & Oui | 20.4% | 20.8% | +5.2% |
| Combinés officiels | 1X2 + les deux marquent | 1 & Non | 23.4% | 22.4% | +8.2% |
| Combinés officiels | 1X2 + les deux marquent | N & Oui | 17.3% | 19.1% | +0.6% |
| Combinés officiels | 1X2 + les deux marquent | N & Non | 7.4% | 6.2% | +0.7% |
| Combinés officiels | 1X2 + les deux marquent | 2 & Oui | 15.3% | 15.2% | +5.4% |
| Combinés officiels | 1X2 + les deux marquent | 2 & Non | 16.2% | 16.3% | +8.6% |
| Combinés officiels | 1X2 + plus/moins 2,5 | 1 & +2,5 | 28.0% | 27.5% | +11.3% |
| Combinés officiels | 1X2 + plus/moins 2,5 | 1 & -2,5 | 15.8% | 15.7% | +4.1% |
| Combinés officiels | 1X2 + plus/moins 2,5 | N & +2,5 | 6.1% | 7.3% | +0.3% |
| Combinés officiels | 1X2 + plus/moins 2,5 | N & -2,5 | 18.6% | 18.0% | +2.3% |
| Combinés officiels | 1X2 + plus/moins 2,5 | 2 & +2,5 | 19.5% | 19.3% | +10.0% |
| Combinés officiels | 1X2 + plus/moins 2,5 | 2 & -2,5 | 12.0% | 12.1% | +4.6% |
| Combinés officiels | Double chance + plus/moins 2,5 | 1N & +2,5 | 34.1% | 34.8% | +9.7% |
| Combinés officiels | Double chance + plus/moins 2,5 | 1N & -2,5 | 34.4% | 33.7% | +4.7% |
| Combinés officiels | Double chance + plus/moins 2,5 | 12 & +2,5 | 47.5% | 46.8% | +3.8% |
| Combinés officiels | Double chance + plus/moins 2,5 | 12 & -2,5 | 27.8% | 27.9% | +1.7% |
| Combinés officiels | Double chance + plus/moins 2,5 | N2 & +2,5 | 25.6% | 26.7% | +9.4% |
| Combinés officiels | Double chance + plus/moins 2,5 | N2 & -2,5 | 30.6% | 30.1% | +5.4% |
| Combinés officiels | Plus/moins 2,5 + les deux marquent | +2,5 & Oui | 41.9% | 43.3% | +2.4% |
| Combinés officiels | Plus/moins 2,5 + les deux marquent | +2,5 & Non | 11.7% | 10.8% | +1.2% |
| Combinés officiels | Plus/moins 2,5 + les deux marquent | -2,5 & Oui | 11.2% | 11.8% | +0.8% |
| Combinés officiels | Plus/moins 2,5 + les deux marquent | -2,5 & Non | 35.2% | 34.1% | +2.9% |
| Corners | Total corners | Plus de 7,5 | 71.4% | 72.2% | +1.3% |
| Corners | Total corners | Moins de 7,5 | 28.6% | 27.8% | +1.3% |
| Corners | Total corners | Plus de 8,5 | 60.2% | 61.0% | +1.3% |
| Corners | Total corners | Moins de 8,5 | 39.8% | 39.0% | +1.3% |
| Corners | Total corners | Plus de 9,5 | 48.7% | 49.7% | +1.3% |
| Corners | Total corners | Moins de 9,5 | 51.3% | 50.3% | +1.3% |
| Corners | Total corners | Plus de 10,5 | 37.8% | 38.6% | +0.9% |
| Corners | Total corners | Moins de 10,5 | 62.2% | 61.4% | +0.9% |
| Corners | Total corners | Plus de 11,5 | 28.1% | 27.8% | +0.7% |
| Corners | Total corners | Moins de 11,5 | 71.9% | 72.2% | +0.7% |
| Corners | Plus de corners | 1 | 54.6% | 54.7% | +8.3% |
| Corners | Plus de corners | N | 8.5% | 9.8% | -0.2% |
| Corners | Plus de corners | 2 | 36.9% | 35.6% | +8.4% |
| Corners | Tranche de corners | 0-8 | 39.8% | 39.0% | +1.3% |
| Corners | Tranche de corners | 9-11 | 32.1% | 33.2% | +0.1% |
| Corners | Tranche de corners | 12+ | 28.1% | 27.8% | +0.7% |
| Corners | Corners du domicile | Plus de 3,5 | 69.6% | 71.1% | +5.4% |
| Corners | Corners du domicile | Moins de 3,5 | 30.4% | 28.9% | +5.4% |
| Corners | Corners du domicile | Plus de 4,5 | 56.2% | 56.5% | +5.7% |
| Corners | Corners du domicile | Moins de 4,5 | 43.8% | 43.5% | +5.7% |
| Corners | Corners du domicile | Plus de 5,5 | 43.2% | 43.2% | +5.8% |
| Corners | Corners du domicile | Moins de 5,5 | 56.8% | 56.8% | +5.8% |
| Corners | Corners de l'extérieur | Plus de 3,5 | 56.1% | 57.6% | +4.3% |
| Corners | Corners de l'extérieur | Moins de 3,5 | 43.9% | 42.4% | +4.3% |
| Corners | Corners de l'extérieur | Plus de 4,5 | 41.7% | 41.1% | +5.4% |
| Corners | Corners de l'extérieur | Moins de 4,5 | 58.3% | 58.9% | +5.4% |
| Corners | Corners de l'extérieur | Plus de 5,5 | 29.5% | 28.5% | +5.2% |
| Corners | Corners de l'extérieur | Moins de 5,5 | 70.5% | 71.5% | +5.2% |
| Cartons | Total cartons jaunes | Plus de 2,5 | 74.0% | 76.0% | -0.1% |
| Cartons | Total cartons jaunes | Moins de 2,5 | 26.0% | 24.0% | -0.1% |
| Cartons | Total cartons jaunes | Plus de 3,5 | 56.4% | 58.0% | +1.6% |
| Cartons | Total cartons jaunes | Moins de 3,5 | 43.6% | 42.0% | +1.6% |
| Cartons | Total cartons jaunes | Plus de 4,5 | 39.3% | 38.2% | +2.2% |
| Cartons | Total cartons jaunes | Moins de 4,5 | 60.7% | 61.8% | +2.2% |
| Cartons | Total cartons jaunes | Plus de 5,5 | 25.2% | 22.3% | +1.1% |
| Cartons | Total cartons jaunes | Moins de 5,5 | 74.8% | 77.7% | +1.1% |
| Cartons | Plus de cartons | 1 | 33.6% | 32.4% | +0.8% |
| Cartons | Plus de cartons | N | 22.0% | 23.4% | -0.0% |
| Cartons | Plus de cartons | 2 | 44.4% | 44.2% | +1.6% |

## 2. Fiabilité : probabilité annoncée vs fréquence réelle, par famille


### buts_match

| Annoncé | Sélections | Réel |
|---|---|---|
| 0%–10% | 53036 | 5.5% (annoncé 5.9%) |
| 10%–20% | 66333 | 14.7% (annoncé 15.1%) |
| 20%–30% | 60772 | 24.4% (annoncé 24.6%) |
| 30%–40% | 35622 | 35.1% (annoncé 34.9%) |
| 40%–50% | 42301 | 45.5% (annoncé 45.4%) |
| 50%–60% | 32837 | 54.4% (annoncé 54.5%) |
| 60%–70% | 28478 | 65.0% (annoncé 64.7%) |
| 70%–80% | 25551 | 75.7% (annoncé 74.9%) |
| 80%–85% | 11172 | 83.3% (annoncé 82.5%) |
| 85%–90% | 10669 | 88.8% (annoncé 87.5%) |
| 90%–95% | 11692 | 92.9% (annoncé 92.5%) |
| 95%–100% | 5246 | 96.3% (annoncé 96.5%) |

### cartons

| Annoncé | Sélections | Réel |
|---|---|---|
| 0%–10% | 542 | 16.4% (annoncé 7.5%) |
| 10%–20% | 5632 | 19.3% (annoncé 16.6%) |
| 20%–30% | 12619 | 25.5% (annoncé 24.5%) |
| 30%–40% | 9929 | 33.8% (annoncé 35.0%) |
| 40%–50% | 9177 | 44.6% (annoncé 44.9%) |
| 50%–60% | 7864 | 53.7% (annoncé 54.8%) |
| 60%–70% | 6783 | 66.0% (annoncé 64.9%) |
| 70%–80% | 6270 | 74.4% (annoncé 74.9%) |
| 80%–85% | 2263 | 80.2% (annoncé 82.3%) |
| 85%–90% | 1414 | 83.7% (annoncé 87.2%) |
| 90%–95% | 455 | 84.0% (annoncé 91.9%) |
| 95%–100% | 49 | 87.8% (annoncé 96.5%) |

### combines_officiels

| Annoncé | Sélections | Réel |
|---|---|---|
| 0%–10% | 25952 | 6.4% (annoncé 6.7%) |
| 10%–20% | 37811 | 14.9% (annoncé 14.9%) |
| 20%–30% | 26211 | 24.5% (annoncé 24.6%) |
| 30%–40% | 19241 | 34.9% (annoncé 34.7%) |
| 40%–50% | 11416 | 44.8% (annoncé 44.4%) |
| 50%–60% | 4018 | 54.9% (annoncé 53.9%) |
| 60%–70% | 1086 | 61.0% (annoncé 63.9%) |
| 70%–80% | 236 | 75.8% (annoncé 74.1%) |

### corners

| Annoncé | Sélections | Réel |
|---|---|---|
| 0%–10% | 6045 | 10.8% (annoncé 8.0%) |
| 10%–20% | 9792 | 19.4% (annoncé 15.5%) |
| 20%–30% | 20293 | 27.1% (annoncé 25.4%) |
| 30%–40% | 30047 | 35.9% (annoncé 34.7%) |
| 40%–50% | 25221 | 45.4% (annoncé 45.0%) |
| 50%–60% | 23898 | 53.9% (annoncé 54.9%) |
| 60%–70% | 21217 | 63.0% (annoncé 64.9%) |
| 70%–80% | 15838 | 72.6% (annoncé 74.6%) |
| 80%–85% | 4552 | 78.3% (annoncé 82.3%) |
| 85%–90% | 2472 | 81.5% (annoncé 87.1%) |
| 90%–95% | 809 | 85.2% (annoncé 91.9%) |
| 95%–100% | 172 | 86.0% (annoncé 97.0%) |

### mi_temps

| Annoncé | Sélections | Réel |
|---|---|---|
| 0%–10% | 37911 | 4.7% (annoncé 4.5%) |
| 10%–20% | 39056 | 15.1% (annoncé 15.3%) |
| 20%–30% | 38585 | 24.3% (annoncé 25.0%) |
| 30%–40% | 29772 | 34.4% (annoncé 34.4%) |
| 40%–50% | 24087 | 44.8% (annoncé 44.4%) |
| 50%–60% | 15581 | 55.9% (annoncé 55.2%) |
| 60%–70% | 15014 | 65.0% (annoncé 64.9%) |
| 70%–80% | 18018 | 76.7% (annoncé 75.3%) |
| 80%–85% | 9540 | 82.8% (annoncé 82.4%) |
| 85%–90% | 5612 | 87.4% (annoncé 87.2%) |
| 90%–95% | 1597 | 93.3% (annoncé 91.6%) |
| 95%–100% | 34 | 94.1% (annoncé 96.1%) |

## 3. Combinés de 2 à 6 matchs (20 000 combinés aléatoires)

| Probabilité annoncée | Combinés | Taux de réussite réel |
|---|---|---|
| 0%–5% (moy. 3.4%) | 2824 | **3.3%** |
| 5%–10% (moy. 7.4%) | 4314 | **7.6%** |
| 10%–20% (moy. 14.5%) | 5449 | **15.2%** |
| 20%–30% (moy. 24.6%) | 3266 | **24.3%** |
| 30%–40% (moy. 34.6%) | 2058 | **35.8%** |
| 40%–50% (moy. 44.5%) | 1086 | **42.8%** |
| 50%–60% (moy. 54.4%) | 559 | **56.0%** |
| 60%–70% (moy. 64.2%) | 289 | **66.1%** |
| 70%–100% (moy. 75.6%) | 155 | **72.9%** |
