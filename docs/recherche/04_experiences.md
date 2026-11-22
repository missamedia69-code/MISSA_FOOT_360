# Expériences : techniques avancées testées sur nos données

Entraînement : 7051 matchs (2019/20–2022/23) — test : 5661 matchs (2023/24–2026/27, jamais vus).

Plus bas = mieux pour RPS, log-loss et Brier. La référence à battre est le **marché avant clôture**.


## 1. Résultat 1X2

| Modèle | RPS | Log-loss | Brier |
|---|---|---|---|
| Marché avant clôture (référence) | 0.19332 | 0.96281 | 0.57217 |
| Marché à la clôture (plafond) | 0.19268 | 0.96054 | 0.57070 |
| Dixon-Coles | 0.20005 | 0.98690 | 0.58713 |
| Elo | 0.19961 | 0.98393 | 0.58618 |
| E1 Pi-ratings | 0.19988 | 0.98479 | 0.58660 |
| E3a Boosting sans cotes (pi, Elo, DC, forme, tirs cadrés) | 0.19905 | 0.98350 | 0.58521 |
| E3b Boosting avec cotes | 0.19468 | 0.97004 | 0.57550 |
| E2 Forme seule (buts + tirs cadrés, moyennes exponentielles) | 0.20116 | 0.98895 | 0.58899 |
| E6 Marché recalibré | 0.19330 | 0.96261 | 0.57205 |
| E4a Pool actuel (marché + DC + Elo) | 0.19318 | 0.96222 | 0.57178 |
| E4b Pool + pi-ratings + forme | 0.19321 | 0.96217 | 0.57174 |
| E4c Pool marché + boosting sans cotes | 0.19329 | 0.96255 | 0.57201 |
| E4d Pool marché + DC + Elo + forme (tirs cadrés) | 0.19316 | 0.96201 | 0.57164 |

Poids appris dans les combinaisons : E4a Pool actuel (marché + DC + Elo) → {'marche': 1.055, 'dc': -0.043, 'elo': -0.03}; E4b Pool + pi-ratings + forme → {'marche': 1.017, 'dc': -0.028, 'elo': -0.04, 'pi': -0.077, 'forme': 0.128}; E4c Pool marché + boosting sans cotes → {'marche': 1.018, 'gb_sans': -0.032}; E4d Pool marché + DC + Elo + forme (tirs cadrés) → {'marche': 1.013, 'dc': -0.049, 'elo': -0.08, 'forme': 0.121}

## 2. Gain par rapport au marché (log-loss, intervalle de confiance 95 % par bootstrap)

Négatif = meilleur que le marché. Si l'intervalle contient 0, le gain n'est pas prouvé.

| Modèle | Différence | IC 95 % |
|---|---|---|
| E3b Boosting avec cotes | +0.00723 | [+0.00453 ; +0.01014] |
| E6 Marché recalibré | -0.00020 | [-0.00064 ; +0.00021] |
| E4a Pool actuel (marché + DC + Elo) | -0.00059 | [-0.00111 ; -0.00012] |
| E4b Pool + pi-ratings + forme | -0.00064 | [-0.00144 ; +0.00018] |
| E4c Pool marché + boosting sans cotes | -0.00026 | [-0.00072 ; +0.00018] |
| E4d Pool marché + DC + Elo + forme (tirs cadrés) | -0.00080 | [-0.00154 ; -0.00004] |

## 3. Scores exacts (log-loss du score final, après calage sur le marché)

- Dixon-Coles (ρ estimé) : 2.90071
- Poisson indépendant (ρ = 0) : 2.89959
- Différence Dixon-Coles − Poisson : +0.00113 (IC 95 % [-0.00001 ; +0.00226])
