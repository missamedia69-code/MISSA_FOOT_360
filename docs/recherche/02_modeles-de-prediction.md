# Notes de recherche — Modèles de calcul de probabilité d'un match

Sources vérifiées : opisthokonta.net (implémentations de Dixon-Coles, pondération temporelle, RPS,
BTTS, Rue-Salvesen), document ratings.pdf de football-data.
Non vérifiés en ligne (sites indisponibles) : constantes Elo/ClubElo, pi-ratings, Poisson bivarié →
ces paramètres seront **calibrés par backtest** sur nos propres données plutôt que copiés.

---

## 1. Modèle de Poisson (Maher) et Dixon-Coles

- Buts attendus (log-linéaires) :
  `λ (domicile) = exp(attaque_dom + défense_ext + avantage_domicile)`
  `μ (extérieur) = exp(attaque_ext + défense_dom)`
  Contrainte d'identification : somme des attaques (ou défenses) = 0.
- Valeurs typiques (Premier League 2011/12) : avantage domicile ≈ 0,27 (échelle log), ρ ≈ −0,13.
- **Correction Dixon-Coles des petits scores** (x = buts domicile, y = buts extérieur) :
  - τ(0,0) = 1 − λμρ
  - τ(0,1) = 1 + λρ
  - τ(1,0) = 1 + μρ
  - τ(1,1) = 1 − ρ
  - τ = 1 sinon
  Avec ρ < 0 : 0-0 et 1-1 augmentent, 1-0 et 0-1 diminuent (le Poisson simple sous-estime les nuls).
- Vraisemblance : Σ poids_match × [log τ(x,y) + log Poisson(x; λ) + log Poisson(y; μ)], maximisée
  par optimisation numérique.
- **Pondération temporelle** : `poids = exp(−ξ·t)`, t en jours depuis le match ; matchs futurs = 0.
  ξ optimal par jour (2007–2014) : Angleterre 0,0018 ; Allemagne 0,0023 ; Pays-Bas 0,0019–0,0020 ;
  France 0,0019–0,0020 (Dixon-Coles : 0,0065 par demi-semaine ≈ 0,00186/jour).
  Réglage : recherche sur grille 0 → 0,003 (pas 0,0001), évaluée hors échantillon.

## 2. Marchés dérivés de la matrice des scores

- `P[i,j] = Poisson(i; λ)·Poisson(j; μ)` (× τ pour les 4 petits scores), tronquée à 10–15 buts.
- 1X2 : domicile = Σ(i > j), nul = Σ(i = j), extérieur = Σ(i < j).
- Over/Under 2,5 : Σ des cases avec i + j ≥ 3 (en indépendance : total ~ Poisson(λ+μ)).
- Les deux marquent (BTTS) : 1 − P(dom = 0) − P(ext = 0) + P(0-0) ; en indépendance
  `(1 − e^−λ)(1 − e^−μ)`.
- Score exact, handicap asiatique, double chance : lecture directe de la matrice.

## 3. Ajustement Rue-Salvesen (surestimation des écarts)

- `Δ = (att_A + déf_A − att_B − déf_B)/2` ; `log λ_A −= γΔ`, `log λ_B += γΔ`.
- γ optimal : ≈ 0–0,1 (Premier League), 0,15–0,3 (Bundesliga). Appliqué au moment de la prédiction.

## 4. Classements Elo et pi-ratings

**World Football Elo** (Wikipedia, vérifié) :
- `R' = R + K·G·(W − We)` ; W = 1 / 0,5 / 0 ; `We = 1 / (10^(−dr/400) + 1)`, dr = écart de notes
  **+100 pour l'équipe à domicile**.
- G (écart de buts N) : N ≤ 1 → 1 ; N = 2 → 1,5 ; N ≥ 3 → (11 + N)/8.
- K (sélections) : 60 Coupe du monde … 20 amicaux. Convergence après ~30 matchs.

**Wunderlich & Memmert 2018 — « Betting Odds Rating System »** (PLOS ONE, vérifié en partie) :
- ~15 000 matchs (PL, Bundesliga, Liga, Serie A, coupes d'Europe), 2007/08–2016/17.
- Note de départ 1000, promu = note du relégué remplacé, avantage domicile ω = 80.
- Probabilités 1X2 = **régression logit ordonnée** sur l'écart de notes (calée sur 3 saisons,
  testée sur les 5 suivantes).
- ELO-Résultat (k = 14) < ELO-Buts (k0 = 4, λ = 1,6) < **ELO-Cotes** (k = 175 ; on remplace le
  résultat par la probabilité implicite des cotes) < **cotes des bookmakers** (meilleures de toutes).
- Leçon : un Elo nourri par les cotes est plus prédictif qu'un Elo nourri par les résultats, mais
  ne bat toujours pas le marché.

**Hvattum & Arntzen 2010** (résumé indirect) : Elo + régression logit → meilleur que les modèles
probit classiques, moins bon que les cotes.

**Pi-ratings** (Constantinou & Fenton 2013) : sources inaccessibles ; à implémenter selon la
description publique (notes domicile/extérieur séparées, mise à jour selon l'erreur d'écart de buts
avec rendements décroissants) et **paramètres calibrés par backtest**.

Usage dans l'appli : variables d'entrée du modèle de combinaison, paramètres (K, avantage domicile,
multiplicateur de buts) optimisés par RPS/log-loss sur des saisons non vues.

## 5. Évaluation

- **RPS** (Ranked Probability Score, 1X2 ordonné domicile < nul < extérieur) :
  `RPS = 1/(r−1) · Σ_{i=1..r} (P_cum_i − O_cum_i)²`, r = 3 ; 0 = parfait.
  Ex. : (0,60 ; 0,30 ; 0,10) avec un nul → 0,185.
- Log-loss et Brier en complément.
- Règle d'or : comparer au RPS des cotes justes de clôture ; un modèle seul fait rarement mieux.

## 6. Combinaison avec le marché

- On peut extraire λ et μ **implicites** des cotes (1X2 + Over/Under) en inversant le modèle de Poisson.
- Combinaison modèle + marché : moyenne pondérée des buts attendus, ou empilement (régression
  logistique sur les log-cotes du marché, du modèle, des pronostiqueurs, du mouvement des cotes).
- Le marché doit avoir le poids principal ; les autres sources n'ajustent qu'à la marge,
  avec des poids appris sur des saisons passées puis validés sur des saisons non vues.

## 7. Ce que dit la littérature scientifique (synthèse des recherches)

- **Le marché gagne** : dans toutes les comparaisons propres trouvées, les probabilités issues des cotes
  battent les modèles (Egidi et al. 2018 : probabilité moyenne de la bonne issue, Premier League
  modèle 0,4349 vs cotes Shin 0,4516 ; Clegg et al. 2026 : RPS modèle 0,1325 vs Betfair 0,1281).
- **Meilleurs modèles sur les seuls résultats** : gradient boosting (CatBoost) sur des **pi-ratings**
  (revue Bunker et al. 2024 ; Soccer Prediction Challenge 2023).
- **Retrait de marge — méthode de Shin** (Štrumbelj 2014 : la meilleure globalement, selon Egidi) :
  `π_i(z) = [√(z² + 4(1−z)·o_i²/Σo_j) − z] / [2(1−z)]`, o_i = 1/cote_i ; z (part d'initiés)
  trouvé numériquement pour que Σπ_i = 1.
  Une étude 2026 (Goto et al., 90 014 matchs) propose une correction favori/outsider apprise sur
  l'historique, meilleure que Shin et puissance → à tester.
- **Combinaison modèle + marché** : Egidi et al. — taux de buts = combinaison convexe des paramètres
  historiques et des taux implicites des cotes (modèle de Poisson hiérarchique).
- **Décorrélation** (Hubáček & Šír 2020) : pour gagner de l'argent, il ne suffit pas d'être précis ;
  il faut que nos erreurs soient **différentes** de celles du marché. → Les ajustements doivent
  apporter de l'information que le marché n'a pas (pronostiqueurs à fort CLV, mouvements de cotes).
- **Évaluation** : Wheatcroft 2019 montre que le RPS peut mal classer les prévisions ; le score
  logarithmique (log-loss / « ignorance ») est plus discriminant → rapporter **log-loss + RPS + Brier**.
- **Prudence** sur les ROI annoncés dans les articles : échantillons petits, cotes parfois non
  réellement disponibles (Clegg : ROI +1 %, intervalle −3,8 % à +5,9 %).
- Les prédictions des foules sur réseaux sociaux s'approchent des cotes mais ne les battent pas.
