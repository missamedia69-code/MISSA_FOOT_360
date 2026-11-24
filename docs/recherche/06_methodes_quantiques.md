# Notes de recherche — Méthodes « quantiques » / « surnaturelles » (24/11/2026)

> Pour les **principes, les bases mathématiques et l'agencement en couches** de toutes
> ces briques dans l'application, voir `07_principes_et_agencement_misa_tv.md`.

Question posée : existe-t-il des méthodes de prédiction de matchs « surnaturelles »,
issues des mathématiques quantiques ? Réponse courte : **oui, il existe des méthodes
quantiques (réelles, publiées), mais aucune n'est surnaturelle et aucune n'a fait la
preuve d'un avantage sur un marché de cotes efficient.** Le quantique est ici de
l'algèbre linéaire dans des espaces de Hilbert complexes — superposition,
interférence, intrication, non-commutativité — pas un accès au futur.

À ne pas confondre avec trois registres distincts, détaillés ci-dessous :

| Registre | Ce que c'est | Statut pour MISSA FOOT 360 |
|---|---|---|
| **A. Quantique / inspiré quantique** | circuits à qubits, recuit, noyaux, réseaux tensoriels | Recherche, aucun gain démontré sur données tabulaires de football |
| **B. Mathématiques classiques très avancées** | états dynamiques, copules, processus ponctuels, information, calibration | C'est le socle actuel du moteur (`missa/`, `web/js/jumeau.js`) |
| **C. Pseudo-quantique / marketing** | « IA quantique », conscience quantique, 98 % de réussite | À écarter : pas de protocole, pas de hors échantillon, pas de CLV |

---

## A. Les méthodes réellement quantiques (ou inspirées du quantique)

### 1. Réseaux de neurones quantiques variationnels (QNN / VQC)
On encode chaque variable du match (buts récents, forme, H2H) dans l'angle de rotation
d'un qubit, on applique un circuit paramétré (portes + intrication), on mesure et on
lit une probabilité de 1/N/2. L'article le plus cité est Sun & Chu, *Scientific
Reports* 15:19875 (2025), entraîné sur les championnats européens 2008–2022 via
PennyLane, qui annonce +22 % d'accuracy face à CNN/LSTM/Transformer/BPNN et des
probabilités de victoire à l'Euro (Espagne 31,7 %, France 27,6 %…).
→ https://www.nature.com/articles/s41598-025-91870-8
→ https://pubmed.ncbi.nlm.nih.gov/40481179/

**Réserve majeure** : une accuracy de ~98 % (ou +22 points) sur du 1X2 est
incompatible avec la prévisibilité connue du football (le consensus des bookmakers
plafonne autour de 50–55 % de bons pronostics 1X2). De tels chiffres signalent
généralement une fuite d'information, un déséquilibre de classes, un test en
échantillon ou une métrique mal définie. L'article reconnaît lui-même les limites
matérielles (bruit des qubits, coût) et des biais de données. À reproduire avec nos
métriques avant d'y croire.

### 2. Noyaux quantiques / SVM quantique (QSVM, QVK-SVM)
Une « feature map » quantique projette les données dans un espace de Hilbert ; le
noyau (produit scalaire d'états) alimente un SVM classique. Variante variationnelle
(QV-SVM) et hybride (QVK-SVM).
→ https://arxiv.org/pdf/2305.06063

**Contrôle empirique** : benchmark 2026, 970 expériences, 9 jeux de données
tabulaires, 4 cartes quantiques, 3 noyaux classiques, validation croisée imbriquée
et matériel IBM Heron : **aucune des 29 comparaisons quantique/classique n'est
statistiquement significative**, et le choix du jeu de données explique 73 % de la
variance contre 9 % pour le noyau.
→ https://arxiv.org/html/2604.18837v1
→ https://pith.science/paper/2604.18837

### 3. Recuit quantique et optimisation QUBO / Ising
On formule un problème combinatoire en `min xᵀQx` (QUBO), équivalent à un
Hamiltonien d'Ising, résolu par recuit quantique (D-Wave) ou recuit simulé
« quantum-assisted ». Applications transposables au football : sélection d'un
sous-ensemble de variables non redondantes, pondération d'un pool de modèles,
composition d'un combiné sous contraintes (budget, exposition, corrélation).
→ https://www.nature.com/articles/s41598-026-71141-w
→ https://link.springer.com/chapter/10.1007/978-981-15-5616-6_10
→ https://www.nature.com/articles/s41598-025-14611-x

C'est la piste **la plus facile à tester sans machine quantique** : le même QUBO se
résout avec `simulated annealing` (D-Wave Ocean SDK) sur CPU. Attention : certains
articles « sports portfolio / quantum hedging » relèvent du marketing, pas de la
preuve.

### 4. Estimation d'amplitude quantique (QAE) pour Monte-Carlo
Nos simulations de scores et de tickets sont du Monte-Carlo (erreur ~`1/√N`). QAE
donne théoriquement `1/N` (accélération quadratique) pour estimer une probabilité
de queue, une espérance ou une VaR de bankroll.
→ https://ar5iv.labs.arxiv.org/html/1907.03044
→ https://qiskit-community.github.io/qiskit-finance/tutorials/09_credit_risk_analysis.html

Limite : nécessite des qubits corrigés d'erreurs ; sur le matériel actuel, les
démonstrations restent des jouets (5 actifs, quelques qubits) et le gain ne se
matérialise pas à petite échelle.
→ https://entangledfuture.com/learn/quantum-risk-analysis/

### 5. Marches quantiques / PageRank quantique
Classer des équipes = classer les nœuds d'un graphe de résultats. Les marches
quantiques (discrètes, continues, ouvertes) produisent un « qPageRank » où
l'interférence modifie la hiérarchie des nœuds périphériques et lève certaines
dégénérescences.
→ https://arxiv.org/abs/1905.06575
→ https://arxiv.org/html/2404.14770v1

Transposition : remplacer Elo/pi-ratings par une centralité quantique sur le graphe
des confrontations. Aucun résultat hors échantillon publié sur le football.

### 6. Réseaux tensoriels / Matrix Product States (MPS), « quantum-inspired »
Les MPS (états de produit matriciel / tensor trains) viennent de la physique
quantique à N corps, mais s'exécutent **classiquement** : ils compressent un
tenseur de poids exponentiel en un nombre polynomial de paramètres. L'entropie
d'intrication sert à interpréter et élaguer les variables. Applications possibles :
séquences de matchs, réservoir quantique (QRC/QELM), génération d'embeddings.
→ https://arxiv.org/html/1605.05775v2
→ https://arxiv.org/html/2106.08334v2
→ https://arxiv.org/html/2503.05535v1

### 7. Probabilité quantique / cognition « quantum-like »
Ici on ne modélise **pas le match mais le parieur** : états mentaux dans un espace
de Hilbert, superposition avant décision, interférence, effets d'ordre,
contextualité, logique non distributive (loi de probabilité totale violée).
Utile pour comprendre les biais de perception des cotes, le « tilt », l'ordre dans
lequel on consulte les marchés — pas pour deviner un score.
→ https://www.cambridge.org/core/books/quantum-models-of-cognition-and-decision/75909428F710F7C6AF7D580CB83443AC
→ https://link.springer.com/article/10.1007/s44163-026-00909-w
→ https://www.emergentmind.com/topics/quantum-like-modelling-of-cognition

Autres variantes citées en littérature : machines de Boltzmann quantiques, circuits
génératifs (QCBM/QGAN) pour données synthétiques, réseaux bayésiens quantiques,
marches quantiques en temps continu, algorithmes de Grover pour la recherche de
paramètres. Aucune n'a été validée sur des saisons jamais vues avec cotes de clôture.

---

## B. Les mathématiques « surnaturelles »… mais classiques

Ce sont elles qui donnent l'illusion de la magie, et elles sont déjà en grande
partie dans le projet :

| Famille | Ce que ça fait | Où dans MISSA FOOT 360 |
|---|---|---|
| Dixon-Coles / Poisson bivarié, correction des petits scores | dépendance entre les deux scores | `missa/dixon_coles.py`, `docs/recherche/02` |
| Loi jointe 1re MT / score final, grilles 10×10 | 193 marchés dérivés d'**une seule** matrice | `missa/jumeau.py`, `web/js/jumeau.js` |
| Binomiale négative + bêta-binomiale (corners), Poisson bivariée (cartons) | dispersion et corrélation | `jumeau.py`, validation dans `docs/validation_jumeau.md` |
| Modèles à espace d'états / score-driven (GAS), forces d'attaque qui évoluent | forme dynamique au fil des journées | littérature : `https://academic.oup.com/jrsssc/article/74/3/717/7929974`, `https://research.vu.nl/ws/portalfiles/portal/151597369/Forecasting_football_match_results_in_national_league_competitions_using_scoredriven_time_series_models.pdf` |
| Skellam, Weibull bivarié + copule, diagonale gonflée | lois de comptage plus souples | `https://www.researchgate.net/publication/338028907_An_exploration_of_predictive_football_modelling` |
| Elo, Glicko, pi-ratings, GAP ratings (tirs), PageRank classique | notes et classements | `missa/elo.py`, `docs/recherche/05` |
| Processus de Hawkes / chaînes de Markov / Monte-Carlo | buts en direct, scénarios | à explorer |
| Bayésien hiérarchique, shrinkage, stacking, boosting | rétrécissement vers la moyenne, pooling | `scripts/experiences.py`, `docs/recherche/04` |
| Calibration, RPS / log-loss / Brier, bootstrap | honnêteté des probabilités et intervalles | `missa/confiance.py`, `missa/evaluation.py`, `data/calibration.json`, `docs/resultats_backtest.md` |
| Théorie de l'information, matrices aléatoires / spectral, homologie persistante (TDA), GNN / transformers | structure des réseaux de passes et des séquences | non implémenté |

---

## C. Ce qu'il faut écarter

- « IA quantique » sans article, sans code, sans jeu de test ;
- conscience quantique, « champ de probabilité », astrologie, numérologie,
  « vibrations » du calendrier ;
- tout vendeur annonçant 90–98 % de réussite ou un « pronostic sûr » ;
- les métriques trompeuses : accuracy sur classes déséquilibrées, test en
  échantillon, absence de référence au marché, absence de cote de clôture / CLV ;
- confusion entre « quantique » (= complexe) et « meilleur ».

À titre de repère, un comparatif commercial récent cite des accuracy de 88–98 % pour
des LSTM/CNN sur le football : c'est exactement le type de chiffre à reproduire
avant de l'accepter. → https://www.golsinyali.com/en/blog/best-football-prediction-algorithms-2026

---

## Verdict chiffré (nos propres expériences)

`docs/recherche/04_experiences.md` et `05_techniques_avancees.md` (test sur 5 661
matchs jamais vus, référence = marché avant clôture) :

| Modèle | RPS | Log-loss |
|---|---|---|
| Marché à la clôture (plafond) | 0,19268 | 0,96054 |
| Marché avant clôture | 0,19332 | 0,96281 |
| Pool marché + DC + Elo + forme (E4d) | 0,19316 | 0,96201 |
| Gradient boosting avec cotes | 0,19468 | 0,97004 |
| Dixon-Coles seul | 0,20005 | 0,98690 |

Le modèle du challenge 2023 reste 6,4 % moins bon que le consensus des bookmakers ;
le seul gain publié robuste (+3,5 % sur 56 435 paris, Kaunitz et al.) vient de
**l'exploitation d'un écart de cote**, pas d'un modèle exotique. Le jumeau
numérique, lui, est validé marché par marché sur 5 727 matchs de test
(`docs/validation_jumeau.md`) et sa parité navigateur ↔ Python est à 1,3 × 10⁻¹⁴
(`web/tests/parite.py`).

**Conclusion** : ce qui paraît « surnaturel » est la combinaison d'une loi jointe
élevée, d'une calibration honnête et d'un backtest hors échantillon. Le quantique
apporte aujourd'hui un vocabulaire et des outils d'optimisation, pas un avantage
prédictif mesuré.

## Si on veut expérimenter (ordre de faisabilité)

1. **QUBO + recuit simulé** pour sélectionner les variables du pool (CPU, une
   journée) — réutiliser `scripts/experiences.py`.
2. **Modèle quantum-like du parieur** (ordre de consultation des marchés, biais) —
   recherche produit, sans toucher aux probabilités.
3. **MPS / tensor train** sur les séquences de matchs — classique, interprétable.
4. **VQC / QSVM 4–8 qubits** via simulateur PennyLane/Qiskit — comparer à un RBF
   classique avec le même protocole.
5. **QAE** — théorique seulement, à documenter, pas à coder.

Protocole obligatoire pour toute piste : entraînement 2019/20–2022/23, test
2023/24–2026/27 jamais vu, RPS + log-loss + Brier contre le marché avant clôture,
intervalle de confiance par bootstrap, CLV sur cotes de clôture, graines fixées,
et parité `web/js/jumeau.js` ↔ `missa/jumeau.py` préservée.
