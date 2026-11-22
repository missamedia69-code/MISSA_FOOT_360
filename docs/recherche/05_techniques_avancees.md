# Techniques mathématiques avancées pour le pronostic — synthèse (novembre 2026)

Deux sources : (A) la littérature, lue dans les publications d'origine quand elles étaient
accessibles ; (B) nos propres expériences sur 12 712 matchs (5 grands championnats), avec un test sur
5 661 matchs jamais vus (`scripts/experiences.py`, résultats détaillés dans `04_experiences.md`).

## A. Ce que dit la littérature

| Technique | Principe | Résultats publiés | Fiabilité de l'info |
|---|---|---|---|
| **Forces dynamiques** (Koopman & Lit 2015, Owen 2011, Rue & Salvesen 2000) | attaque/défense évoluent dans le temps (marche aléatoire, ou variance accrue après l'été) | Implémentées dans le package R `footBayes` (2026). Convergence difficile en version hebdomadaire. Pas de score hors échantillon trouvé | Partielle |
| **Poisson bivarié / à diagonale gonflée** (Karlis & Ntzoufras 2003) | covariance entre les buts des deux équipes ; masse supplémentaire sur les nuls | Serie A 2000/01, en échantillon : AIC 1791,6 (bivarié) vs 1796,3 (Dixon-Coles) vs 1797,5 (Poisson). Aucun gain hors échantillon publié trouvé | Vérifié (vignette footBayes) |
| **Binomiale négative / Skellam / Weibull + copule** (Boshnakov et al. 2017) | lois de comptage plus souples | Binomiale négative : la dispersion estimée retombe sur Poisson (Serie A). Article Weibull non accessible | Partielle |
| **Bayésien hiérarchique** (Baio & Blangiardo 2010) | forces « rétrécies » vers la moyenne (utile en début de saison) | Pas de comparaison hors échantillon trouvée | Partielle |
| **Notes fondées sur les tirs** (Wheatcroft, « GAP ratings », arXiv 2001.09097) | notes d'attaque/défense mises à jour avec les tirs cadrés, non cadrés et les corners | 143 672 matchs, 22 championnats. Paris (Kelly, meilleures cotes) : +3,58 % sans cotes en entrée, +5,01 % avec (chiffres d'un résumé, optimistes : meilleures cotes de tous les bookmakers) | Partielle |
| **Pi-ratings** (Constantinou & Fenton 2013) | notes domicile/extérieur mises à jour par l'erreur d'écart de buts, rendements décroissants (log10) | Équations vérifiées dans l'implémentation R de référence (λ = 0,035, γ = 0,7, c = 3 ; λ = 0,06, γ = 0,6 optimisés sur la Premier League 2008–2015) | Vérifié (code) |
| **Gradient boosting sur des notes** (Soccer Prediction Challenges 2017 et 2023) | XGBoost/CatBoost sur pi-ratings, notes de Berrar et forme récente | 2017 : RPS 0,2054 (Berrar, XGBoost), 0,2063 (Hubáček). CatBoost + pi-ratings : 0,1925 à 0,2085 selon l'étude. Le modèle de 2023 reste **6,4 % moins bon que le consensus des bookmakers** | Chiffres de seconde main |
| **Apprentissage profond** (Yeung et al. 2023 ; Fischer & Heuer 2024) | réseaux sur séquences de matchs | Ne bat pas CatBoost + pi-ratings (0,2098 vs 0,2085). « Le choix du modèle n'a qu'une influence mineure » | Partielle |
| **Exploiter le marché** (Kaunitz, Zhong & Kreiner 2017) | parier quand la meilleure cote dépasse la probabilité du consensus (+ marge α) | **+3,5 %** sur 56 435 paris (10 ans, cotes de clôture) ; **+9,9 %** sur 6 994 paris (cotes 1 à 5 h avant) ; **+8,5 %** sur 265 paris en argent réel ; ~30 % des cotes avaient déjà bougé ; comptes restreints par les bookmakers | **Vérifié (PDF)** |
| **Mises sur paris simultanés** (Long 2026 ; Tepelyan & Lam 2026) | Kelly pour plusieurs paris et combinés | Pour des matchs indépendants, le Kelly optimal se décompose match par match ; un combiné n'est utile que si chacune de ses sélections a de la valeur seule | Résumés |

## B. Nos expériences (test sur 5 661 matchs jamais vus)

| Modèle (résultat 1X2) | RPS | Log-loss |
|---|---|---|
| Marché avant clôture (référence) | 0,19332 | 0,96281 |
| Marché à la clôture (plafond) | 0,19268 | 0,96054 |
| Pi-ratings seuls | 0,19988 | 0,98479 |
| Gradient boosting sans cotes (pi, Elo, Dixon-Coles, forme, tirs cadrés) | 0,19905 | 0,98350 |
| Gradient boosting avec cotes | 0,19468 | 0,97004 |
| **Pool actuel (marché + Dixon-Coles + Elo)** | **0,19318** | **0,96222** |
| **Pool + forme « tirs cadrés »** | — | **0,96201** |

Gains par rapport au marché (log-loss, intervalle de confiance à 95 %) :
- Pool actuel : −0,00059 [−0,00111 ; −0,00012] → **gain petit mais prouvé** ;
- Pool + forme tirs cadrés : −0,00080 [−0,00154 ; −0,00004] → **meilleur, gain prouvé** ;
- Pool + pi-ratings + forme : −0,00064 [−0,00144 ; +0,00018] → non prouvé ;
- Marché + boosting : −0,00026 [−0,00072 ; +0,00018] → non prouvé ;
- Boosting avec cotes : +0,00723 → **pire que le marché** (il dégrade les cotes).

Scores exacts (après calage sur le marché) : Dixon-Coles 2,90071 vs Poisson indépendant 2,89959
(différence +0,0011, IC [−0,00001 ; +0,0023]) → la correction ρ n'apporte rien une fois la matrice
calée sur le marché ; à reconfirmer.

Erreur de méthode évitée : combiner des modèles flexibles avec leurs propres prédictions
d'entraînement les fait surestimer (poids 1,4 au lieu de 0,1). Il faut des prédictions hors
échantillon (validation croisée par saison) — c'est désormais la règle dans nos tests.

## Conclusions

1. **Pour le 1X2 des grands championnats, aucune technique ne bat nettement le marché**, ni dans
   la littérature (le meilleur modèle de 2023 est 6,4 % moins bon que les bookmakers) ni chez nous.
   Les techniques les plus sophistiquées (boosting, deep learning) atteignent RPS ≈ 0,199, contre
   0,193 pour le marché.
2. **Ce qui aide vraiment, modestement :** ajouter au marché des informations qu'il n'intègre pas
   parfaitement — la forme récente en **tirs cadrés** est la seule source qui garde un poids positif
   (≈ 0,12) et améliore la précision de façon prouvée.
3. **Là où il reste de la marge :** la *valeur* (meilleure cote vs probabilité du consensus,
   Kaunitz/Buchdahl : +3,5 % à +9,9 % prouvés, mais limitation des comptes), le **timing**
   (parier 1 à 5 h avant le match), et les **marchés secondaires** (corners, cartons, mi-temps),
   moins travaillés par les bookmakers — à condition d'avoir leurs cotes pour mesurer la valeur.
4. **Pas prioritaire :** forces dynamiques, Poisson bivarié, Weibull, deep learning — complexité
   élevée, aucun gain démontré une fois le modèle ancré sur les cotes.

## Feuille de route proposée

| Priorité | Action | Gain attendu | Effort |
|---|---|---|---|
| 1 | Ajouter la forme « tirs cadrés » (moyennes exponentielles) au pool | petit, prouvé (−0,0002 de log-loss en plus) | faible |
| 2 | Passer la matrice des scores en Poisson indépendant (ρ = 0) après confirmation sur plus de données | scores exacts un peu meilleurs | faible |
| 3 | Mode « value » façon Kaunitz : signaler les meilleures cotes > consensus + marge, avec historique de CLV | le seul avantage financier prouvé | moyen |
| 4 | Récupérer les cotes corners/cartons/mi-temps (offre payante The Odds API) pour mesurer la valeur du jumeau sur ces marchés | potentiel, à mesurer | moyen |
| 5 | Mises : Kelly fractionnaire par sélection ; combinés seulement si chaque sélection a de la valeur | gestion du risque | faible |
