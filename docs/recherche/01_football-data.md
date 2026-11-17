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

---

## Synthèse pour la conception

1. **Référence de vérité** = la cote de clôture du marché, sans marge. On mesure tout contre elle.
2. **Moteur** = probabilités du modèle (à définir avec les autres documentations) → comparaison
   avec les probabilités du marché → EV, corrigée par le délai avant match.
3. **Pronostiqueurs** = historique horodaté, notés par CLV + test statistique ; poids proportionnel
   à la preuve de talent ; détection des historiques suspects.
4. **Validation** = backtest saison par saison sans fuite d'information, suivi du CLV en réel,
   alertes de sur-apprentissage.
5. **À ignorer** : tendances de séries, avis majoritaire du public, rendements sur petits échantillons.
