# Notes de recherche — football-data.co.uk

Source : https://football-data.co.uk/ (articles « Betting Articles », auteur : Joseph Buchdahl).
Ces notes résument ce qui est utile pour construire le moteur de pronostic MISSA FOOT 360.

---

## 0. Les données du site

- Résultats et cotes historiques gratuits (CSV/Excel), 22 divisions européennes + 16 ligues « extra ».
- Cotes de jusqu'à 10 bookmakers depuis 2000/01 ; moyenne et maximum depuis 2005/06 ;
  cotes d'ouverture **et** de clôture depuis 2019/20 ; clôture Pinnacle depuis 2012/13.
- **Attention** : le site signale que les cotes Pinnacle sont **peu fiables depuis le 23/07/2025**
  (exclues de ses moyennes). Pour les saisons récentes, il faudra utiliser la cote moyenne de
  clôture du marché comme référence plutôt que Pinnacle seule.
- Légende des colonnes : https://football-data.co.uk/notes.txt (à lire).
- **Conditions d'utilisation** : usage privé uniquement ; pas d'usage commercial, de récupération
  automatisée ni d'entraînement d'IA. → À régler (autorisation ou autre source) avant toute
  mise en ligne publique/commerciale.

---

## 1. Testing your Betting Model (2018)

- Valeur attendue d'un pari : `EV = cote_jouée / cote_juste`, où la cote juste = cote Pinnacle
  **sans marge** (méthode « marge proportionnelle à la cote », qui tient compte du biais favori/outsider).
  Ex. : 2,10 / 2,00 = 1,05 → +5 % attendu.
- Valider un modèle : comparer le rendement réel au rendement attendu (t-test bilatéral à variances
  inégales, `TTEST(A,B,2,3)`), plus une simulation Monte-Carlo.
- Suivre des fenêtres glissantes de 1 000 paris : des écarts « 1 chance sur 40/60 » arrivent par
  hasard puis reviennent à la moyenne.

**Pour l'appli** : chaque pronostic doit stocker sa probabilité et l'EV attendue → on compare en continu
attendu vs réalisé.

## 2. Fiabilité du t-test pour un historique de paris (2018)

- `t = (moyenne_profit − 0) / (écart-type / √n)`, p-value unilatérale.
- Formule raccourcie de l'écart-type quand toutes les cotes sont proches (r = rendement, o = cote) :
  `s² = (r/o)(o−1)² + 1 − r/o − (r−1)²` (à cote 3,00 et r = 1 → s ≈ 1,414).
- Si les cotes sont très variées, utiliser l'écart-type réel de l'échantillon.

## 3. Quantifying Predictive Error in Football Models (2026)

- Le backtest sur données historiques est nécessaire mais pas suffisant.
- En réel : enregistrer la probabilité du modèle **et** la cote réellement disponible au moment du
  pronostic ; l'écart (latence, cotes qui bougent) est une erreur à surveiller.

## 4. Power Ratings (2015)

- Chaque équipe démarre à 10. Après un match :
  `Δ_domicile = [(écart de buts) − (écart de notes) − avantage_domicile] × 0,25`,
  avantage domicile = 0,5 ; `Δ_extérieur = −Δ_domicile`.
- Résultat : sur 9 316 paris « value », rendement +0,33 %, **aucun résultat significatif**.
  Les gros rendements sur les cotes longues = chance.

**Pour l'appli** : un modèle simple qui ne fait que retrouver les cotes du marché n'a pas d'avantage.
Toujours tester la significativité avant d'afficher un « rendement ».

## 5. Pinnacle's Limit as a Confidence Meter (oct. 2026)

61 979 paris « value » (ValueBetFactory). Rétention = CLV moyen / EV affichée moyenne.

| Limite Pinnacle | EV affichée | CLV | Rétention |
|---|---|---|---|
| < 250 $ | 9,2 % | 2,8 % | 30 % |
| 250–500 $ | 5,7 % | 1,6 % | 28 % |
| 500–1 000 $ | 5,3 % | 2,2 % | 42 % |
| 1 000–2 000 $ | 4,0 % | 2,5 % | 62 % |
| 2 000–5 000 $ | 3,2 % | 2,5 % | 78 % |
| > 5 000 $ | 3,0 % | 2,2 % | 73 % |

Rétention selon le délai avant le coup d'envoi : < 1 h ≈ 67–99 % ; 1–6 h ≈ 40–94 % ;
6–24 h ≈ 12–51 % ; **> 24 h ≈ 0–26 %** (presque toute la « value » disparaît).

- Explication : régression vers la moyenne ; une cote encore instable contient du bruit.
- Le temps est le facteur principal ; la limite ajoute de l'information à délai égal.

**Pour l'appli** :
- Afficher une **EV corrigée** = EV brute × rétention(délai, liquidité du marché).
- Se méfier des « value » trouvées plus de 24 h avant le match.
- Mesurer notre propre rétention (CLV obtenu / EV annoncée).
- Évaluer les performances par le **CLV**, pas par le profit (trop bruité).

## 6. Backtesting / Strategy Builder (Bet2Invest, 2026)

- Démarche : Hypothèse → Règles → Backtest → Analyse → Remise en question → Validation → Exécution.
- Détecter avec les cotes d'ouverture, calculer le résultat avec les cotes de clôture.
- **Sur-apprentissage** : tester des centaines de filtres finit toujours par trouver une combinaison
  « gagnante » par hasard.
- Juger une stratégie sur : taille d'échantillon, ROI, drawdown maximal, régularité par période,
  stabilité quand on modifie un peu les conditions. +3 % sur des milliers de paris > +15 % sur 200.

**Pour l'appli** : module de backtest avec séparation stricte entraînement/test par saison, et
indicateurs d'alerte (« trop beau pour être vrai », échantillon trop petit).

## 7. tipstrr (2018)

- La plupart des pronostiqueurs n'offrent que de la chance ; les profits à court terme ne durent pas.
- Une plateforme crédible : historiques non modifiables, cotes prises uniquement chez des bookmakers
  qui acceptent les gagnants (Pinnacle, SBObet), pas d'affiliation bookmaker, comparaison aux cotes
  de clôture.

**Pour l'appli** : n'enregistrer un pronostiqueur que si ses pronostics sont horodatés **avant** le match
avec la cote proposée, et ne jamais les modifier ensuite.

## 8. Betshare (paris Over/Under, 2017)

- Le public mise à 62 % sur le « Over » (plus de buts), dans tous les sports.
- Pourtant, sur 83 634 matchs, parier systématiquement Over ou Under rapporte pareil (97,2 % vs 96,4 %,
  différence non significative). Les mouvements de cotes sont quasi aléatoires.

**Pour l'appli** : l'opinion de la majorité du public n'est **pas** un signal exploitable.

## 9. Using the Closing Odds to test a Tipster's Skill (2016) — clé pour les pronostiqueurs

- Avantage attendu : `edge = cote_jouée / cote_clôture_Pinnacle / (1 + marge) − 1`.
  Ex. : 1,80 / 1,65 / 1,03 ≈ +5,9 %.
- Tests rapides (~20–30 pronostics suffisent) :
  1. proportion de pronostics dont la cote **baisse** avant le match vs 50 % (test du chi²) ;
  2. t-test entre cotes conseillées et cotes de clôture.
- Cas réels : un pronostiqueur avec 23 cotes sur 26 qui baissent → vrai talent ;
  un autre avec +25 % de rendement mais aucun avantage sur la clôture → probablement de la chance ;
  un autre à 78 % de réussite mais des cotes qui **montent** → fraude (paris perdants supprimés).

**Pour l'appli** : le poids d'un pronostiqueur = son CLV moyen mesuré (et sa significativité),
**pas** son taux de réussite ni son ROI affiché.

## 10. Asian Handicap — régularité des équipes (2016)

- « L'excès de buts » d'une équipe par rapport au handicap asiatique suit une loi normale et
  la 1re moitié de saison ne prédit pas la 2de (corrélation ≈ 0).

**Pour l'appli** : ne pas utiliser des tendances du type « telle équipe couvre souvent son handicap ».

## 11. Using Pinnacle's Closing Line to Predict Profits (2016)

- 87 960 paires (cote avant clôture, cote de clôture Pinnacle), 2012/13–2015/16.
- Rendement attendu = `cote_jouée / cote_clôture − 1`. Rendement réel vs attendu :
  **pente 1,0025, R² = 0,952** → relation quasi parfaite 1 pour 1.
- L'écart constant (~4 %) correspond à la marge du bookmaker (non retirée ici).

**Pour l'appli** : le CLV est un prédicteur fiable du rendement futur ; c'est notre indicateur n°1
(pour le modèle comme pour les pronostiqueurs).

## 12. How Unpredictable was the 2015/16 Premier League? (2016)

- **Score de Brier** (1X2) : `(p_dom − o_dom)² + (p_nul − o_nul)² + (p_ext − o_ext)²`, o = 1 si l'issue
  s'est produite, 0 sinon. Va de 0 (parfait) à 2. Pronostic au hasard (1/3 partout) = 0,667.
  Moyenne Premier League 2015/16 avec les cotes du marché : 0,620.
- Limite : le Brier moyen ne capte pas bien la « surprise » (tout prédire domicile donne 0,512).
- **Points attendus** d'un match : `3·p_victoire + 1·p_nul`. Somme sur la saison → classement attendu.
- **Score d'imprévisibilité** = écart-type de (points réels − points attendus) sur les 20 équipes ;
  ~4,5 à 8 en temps normal, 10,3 en 2015/16 (événement « 1 sur 200 ans », Monte-Carlo 100 000 tirages).

**Pour l'appli** :
- Métriques d'évaluation du modèle : Brier score (+ log-loss), comparés au Brier des cotes du marché.
  Notre modèle doit faire **au moins aussi bien que le marché** sinon il n'apporte rien.
- Fonction « classement projeté » : points attendus + simulation Monte-Carlo de fin de saison.

## 13. Betting Psychology & the Addictive Power of Maybe (2017)

- La plupart des parieurs perdent mais se croient meilleurs que la moyenne (excès de confiance).
- Illusion de causalité : on attribue un gain à son talent alors que c'est le hasard.
- La dopamine réagit à l'**incertitude** de la récompense → mécanisme d'addiction.

**Pour l'appli** : présenter des probabilités (jamais de « prono sûr »), afficher l'historique honnête
(gains **et** pertes), message de jeu responsable + liens d'aide.

## 14. Steamers and Drifters (2016) — le mouvement des cotes est un signal

- 10 180 matchs anglais, 30 540 cotes, 2010/11–2014/15 ; moyennes du marché (avant clôture vs clôture).
- Une cote qui baisse (steamer) ne baisse **pas assez** ; une cote qui monte (drifter) ne monte
  **pas assez**. Même à la clôture, le marché n'est pas totalement efficace.
- Rendement à la cote de clôture **sans marge** : steamers **+3,40 %**, drifters **−1,90 %**
  (p = 0,002). Effet stable sur 5 saisons.
- Parier toutes les cotes ayant baissé de plus de 10 % à la clôture moyenne : +7,5 % sur 597 paris
  (p ≈ 0,02) — échantillon trop petit pour conclure.

**Pour l'appli** : le **mouvement de cote** (ouverture → clôture, disponible dans football-data
depuis 2019/20) est une variable à intégrer : le sens et l'ampleur du mouvement ajustent la
probabilité dans le même sens.

## 15. Do Tipsters Beat the Odds in a Betting Market? (2016)

- 48 pronostiqueurs tennis, 7 170 paris : 59,1 % des cotes conseillées battent la clôture,
  79 % des pronostiqueurs la battent plus d'une fois sur deux.
- Mais contre la cote de clôture **sans marge** : seulement 44,7 % la battent, rendement attendu
  −0,90 % ≈ rendement réel −0,94 %. Aucun pronostiqueur significativement gagnant.
- Les distributions (cote conseillée / cote de clôture) sont plus resserrées et décalées au-dessus de 1
  que le hasard : ils apportent de l'information, mais pas assez pour battre la marge.

**Pour l'appli** : noter les pronostiqueurs contre la cote de clôture **sans marge** (cote juste),
pas contre la cote brute. Un pronostiqueur peut apporter de l'information utile (signal à combiner)
même s'il n'est pas rentable seul.

## 16. Do Bettors Create their own "Hot Hand" Winning Streaks? (2016)

- Une étude (Xu & Harvey, 565 915 paris) concluait que les parieurs prennent des cotes plus courtes
  après des gains. Buchdahl montre que c'est un **biais de survivance** : ceux qui parient des cotes
  courtes ont naturellement des séries plus longues ; et plus on parie, plus la série maximale est longue
  (Pyckio, ~1 million de pronostics : série max 10 ↔ 575 paris en moyenne, même cotes ~2,0).
- À l'intérieur d'une série de 6 gains, les cotes ne bougent pas (1,64 → 1,64).

**Pour l'appli** : ne **jamais** utiliser les séries de victoires d'un pronostiqueur comme indicateur
(« 8 pronos gagnants d'affilée » ne prouve rien). Toujours se demander quel biais de sélection peut
expliquer un résultat avant de l'utiliser.

## 17. The Favourite–Longshot Bias Revisited (2015)

- Le bookmaker ne répartit pas sa marge également : il la met surtout sur les **outsiders**.
  Ex. vraies cotes 1,25 / 5,00 → affichées ~1,21 / 4,44 (favori −3 %, outsider −12 %).
- Conséquence : parier au hasard les cotes < 1,50 rapporte presque l'équilibre ; les cotes > 5,00
  peuvent rapporter 80 % ou moins.
- Cause : effets de possibilité et de certitude (Kahneman & Tversky) — les gens surestiment les petites
  probabilités et sous-estiment les quasi-certitudes ; les bookmakers en profitent.
- Les **bourses de paris (Betfair)** n'ont presque pas ce biais : sur 52 411 cotes, probabilité implicite
  ≈ fréquence réelle (graphique quasi sur la diagonale).
- Ratio de tolérance (probabilité selon la meilleure cote / selon la cote moyenne) : ~0,97 pour un
  favori à 1,10, ~0,67 pour un outsider à 30. Plus la cote est longue, plus l'écart moyenne/meilleure
  cote est grand.

**Pour l'appli** :
- Pour retirer la marge, **ne pas** diviser uniformément : utiliser une méthode qui charge plus les
  outsiders (marge proportionnelle à la cote, méthode de Shin, ou méthode « puissance »).
- La **meilleure cote du marché** (colonnes Max de football-data) ou une cote de bourse est plus proche
  de la vraie probabilité que la cote moyenne, surtout pour les outsiders.
- Prudence sur les pronostics d'outsiders : c'est là que la marge est la plus forte.

---

## Synthèse pour la conception

1. **Référence de vérité** = la cote de clôture du marché, sans marge. On mesure tout contre elle.
2. **Moteur** = probabilités du modèle (à définir avec les autres documentations) → comparaison
   avec les probabilités du marché → EV, corrigée par le délai avant match.
3. **Pronostiqueurs** = historique horodaté, notés par CLV + test statistique ; poids proportionnel
   à la preuve de talent ; détection des historiques suspects.
4. **Validation** = backtest saison par saison sans fuite d'information, suivi du CLV en réel,
   alertes de sur-apprentissage.
5. **Signaux supplémentaires** : mouvement des cotes ouverture → clôture ; métriques Brier/log-loss
   comparées au marché ; projection de classement par Monte-Carlo.
6. **Retrait de marge** : méthode non uniforme (Shin / puissance / proportionnelle à la cote).
7. **À ignorer** : tendances de séries (y compris séries de victoires des pronostiqueurs), avis majoritaire du public, rendements sur petits échantillons.
