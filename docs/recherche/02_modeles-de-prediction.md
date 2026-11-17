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

## 4. Classements Elo et pi-ratings (paramètres à calibrer)

- Elo : `E = 1 / (1 + 10^(−(R_dom + HFA − R_ext)/400))` ;
  `R' = R + K·G·(résultat − E)` avec un multiplicateur G selon l'écart de buts.
  K, HFA et G seront optimisés par backtest (RPS minimal).
- Pi-ratings (Constantinou & Fenton) : note domicile et extérieur séparées pour chaque équipe,
  mises à jour selon l'erreur entre écart de buts attendu et observé (taux d'apprentissage λ, γ) ;
  paramètres à calibrer par backtest.
- Usage : variables d'entrée pour le modèle de combinaison (pas de modèle autonome).

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
