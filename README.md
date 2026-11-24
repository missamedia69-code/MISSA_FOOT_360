# MISSA FOOT 360

Moteur de pronostic de matchs de football fondé sur la recherche (voir `docs/recherche/`).

## Principe

1. **Marché** : les cotes, une fois la marge retirée (méthodes puissance / Shin / proportionnelle /
   odds ratio ; Abrams pour 2 issues), sont la meilleure estimation disponible.
2. **Modèles** : Dixon-Coles (buts attendus, scores, plus/moins 2,5, BTTS) et Elo.
3. **Pronostiqueurs** : notés uniquement sur la valeur obtenue contre la cote de clôture (CLV),
   jamais sur le profit ou les séries.
4. **Combinaison** : pool logarithmique dont les poids sont appris sur des saisons passées et
   testés sur des saisons jamais vues. Une source inutile reçoit un poids nul.
5. **Décision** : valeur attendue avec la meilleure cote, corrigée selon le délai avant le match ;
   mise par Kelly fractionnaire plafonné.

Les principes, les bases mathématiques et l'agencement en couches de ces briques (marge,
Dixon-Coles, Elo, pool logarithmique, raking, jumeau numérique, calibration, décision,
validation) sont détaillés dans `docs/recherche/07_principes_et_agencement_misa_tv.md`
et dans sa version texte brut `MISA-TV_principes_et_agencement.txt`.

## Structure

| Fichier | Rôle |
|---|---|
| `missa/donnees.py` | Chargement des CSV football-data.co.uk (usage privé) |
| `missa/marge.py` | Retrait de la marge du bookmaker |
| `missa/dixon_coles.py` | Modèle Dixon-Coles avec pondération temporelle + marchés dérivés |
| `missa/elo.py` | Classement Elo avec multiplicateur d'écart de buts |
| `missa/combinaison.py` | Combinaison des sources (poids appris) |
| `missa/pronostiqueurs.py` | Notation des pronostiqueurs par le CLV |
| `missa/valeur.py` | Valeur attendue, rétention selon le délai, Kelly, CLV |
| `missa/evaluation.py` | RPS, log-loss, Brier |
| `missa/backtest.py` | Préparation sans fuite d'information |
| `missa/jumeau.py` | **Jumeau numérique du match** : loi jointe mi-temps/score final, corners, cartons ; toute sélection ou combinaison (ET / OU), modulations |
| `missa/comptages.py` | Modèles par équipe pour les corners et les cartons |
| `scripts/valider_jumeau.py` | Validation de ~170 marchés et de 20 000 combinés sur saisons jamais vues → `docs/validation_jumeau.md` |
| `missa/selections.py` | Sélections (1X2, double chance, buts, BTTS, score exact) et probabilité des combinés |
| `missa/confiance.py` | Mode haute confiance : taux de réussite réel mesuré par niveau de probabilité |
| `missa/stockage.py` | Base SQLite des pronostiqueurs (pronostics non modifiables, refusés après le coup d'envoi) |
| `missa/pipeline.py` | Pronostics des prochains matchs (marché + modèles + pronostiqueurs) |
| `api/main.py` | API FastAPI consommée par les applications Android et web |
| `web/js/jumeau.js` | **Jumeau numérique en JavaScript** (port sans dépendance de `missa/jumeau.py`, parité < 1e-13) |
| `web/js/app.js`, `web/index.html`, `web/css/styles.css` | Application web en 5 modules : Accueil, Analyses, Ticket, Stats, Profil |
| `web/serveur.py` | Serveur statique (stdlib) + relais `/api/*` vers l'API FastAPI |
| `web/scripts/preparer_donnees.py` | Prépare `web/data/donnees.json` depuis les pronostics ou la démo |
| `android/` | Application Android (Kotlin, Jetpack Compose) |
| `scripts/lancer_backtest.py` | Backtest complet → `docs/resultats_backtest.md`, `data/modele.json`, `data/calibration.json` |
| `scripts/generer_pronostics.py` | Pronostics des prochains matchs → `data/pronostics.json` |

## Utilisation

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/pip install fastapi uvicorn httpx
.venv/bin/python scripts/lancer_backtest.py      # entraîne et calibre (≈ 1 min)
.venv/bin/python scripts/valider_jumeau.py       # valide le jumeau et ses paramètres (≈ 4 min)
.venv/bin/python scripts/generer_pronostics.py   # pronostics des prochains matchs
MISSA_CLE_ADMIN=un-secret .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000

# Application web (aucune dépendance npm)
python3 web/scripts/preparer_donnees.py
python3 web/serveur.py                       # http://0.0.0.0:8080
```

### Ajouter un pronostic d'expert (avant le coup d'envoi uniquement)

```bash
curl -X POST http://localhost:8000/pronostics -H "x-cle-admin: un-secret" \
  -H "Content-Type: application/json" \
  -d '{"pronostiqueur": "Nom", "match_id": "E0-20261122-arsenal-chelsea", "selection": "1", "cote": 2.10}'
```

Après le match, `Stockage().cloturer_match(match_id, {"1x2": [H, N, A]})` enregistre les cotes de
clôture : le CLV et la note du pronostiqueur sont alors recalculés. Un pronostiqueur n'influence
les probabilités qu'après 50 pronostics et un t-score de CLV ≥ 2.

## Publication automatique (GitHub Actions)

Le fichier `.github/workflows/pronostics.yml` lance `scripts/publier.py` toutes les 3 heures
(et à la demande depuis l'onglet « Actions » du dépôt) :

1. import des pronostics d'experts de `data/experts/pronostics.csv` et clôture automatique
   des matchs joués (CLV) ;
2. calcul des pronostics des prochains matchs ;
3. publication sur la branche `pronostics` :
   `https://raw.githubusercontent.com/missamedia69-code/MISSA_FOOT_360/pronostics/pronostics.json`

L'application lit cette adresse par défaut. Coût : 0 € (quelques minutes d'exécution par jour).

Un second workflow, `.github/workflows/web.yml`, vérifie à chaque `push` la version web :
syntaxe JavaScript, génération des données hors ligne, parité des 409 probabilités
entre `web/js/jumeau.js` et `missa/jumeau.py`, puis la suite `pytest`.

### Cotes en continu : The Odds API (facultatif)

1. Créer une clé gratuite sur https://the-odds-api.com (500 crédits/mois).
2. Sur GitHub : *Settings → Secrets and variables → Actions → New repository secret*,
   nom `ODDS_API_KEY`, valeur = la clé.
3. Facultatif, onglet *Variables* : `ODDS_API_SPORTS` (`auto` par défaut, ou une liste comme
   `soccer_epl,soccer_france_ligue_one`), `ODDS_API_MAX_SPORTS` (défaut 8) et
   `ODDS_API_FREQUENCE_HEURES` (défaut 24).

En mode `auto`, le moteur interroge gratuitement la liste des compétitions en cours et des matchs
des 48 prochaines heures, puis ne dépense des crédits que pour les compétitions qui jouent
(par ordre de priorité : Ligue des champions, 5 grands championnats, Brésil, Argentine, Mexique…).
Les championnats sud-américains, mexicain, MLS, etc. utilisent l'historique « extra » de
football-data ; les coupes et sélections sans historique sont calculées à partir du marché seul.

Chaque appel coûte 2 crédits par championnat (1X2 + plus/moins). Par défaut : 8 championnats une
fois par jour ≈ 480 crédits/mois, dans l'offre gratuite. Avec une offre payante, mettre par
exemple `ODDS_API_FREQUENCE_HEURES = 3`. Les matchs de The Odds API remplacent ceux de
football-data quand les deux existent ; les noms d'équipes non reconnus sont listés dans
`etat.json` (champ `the_odds_api.noms_non_reconnus`).

## Application web (5 modules, aperçu en direct)

`web/` propose la même expérience que l'application Android dans le navigateur :
**Accueil** (recommandations, valeurs, calibration), **Analyses** (113 matchs par
date et championnat), **Détail** (193 marchés, modulation en direct, forme,
matrice des scores), **Ticket** (probabilité exacte du combiné, valeur, Kelly,
assistant de combiné), **Stats** (validation sur saisons jamais vues) et
**Profil** (réglages, experts CLV, historique des tickets).

Le moteur de probabilités tourne **dans le navigateur** : `web/js/jumeau.js` est
un port de `missa/jumeau.py` (loi jointe mi-temps/score final, corners, cartons,
expressions ET/OU, modulations). La parité est vérifiée sur 409 probabilités
(`web/tests/parite.py`, écart maximal ≈ 1,3 × 10⁻¹⁴). Aucune dépendance npm ni
compilation ; les données viennent de `data/pronostics.json` s'il existe, sinon
de la démonstration hors ligne.

```bash
python3 web/scripts/preparer_donnees.py
python3 web/serveur.py --port 8080
```

Pour brancher les pronostics en direct, lancer l'API sur le port 8000 puis
indiquer `/api` dans « Profil → Réglages » : `web/serveur.py` relaie `/api/*`
vers FastAPI depuis la même origine (pas de CORS). Captures : `docs/captures_web/`.
Voir `web/README.md`.

## Application Android

```bash
cd android && ./gradlew testDebugUnitTest assembleDebug   # APK : app/build/outputs/apk/debug/
```

- Liste des matchs par jour et par championnat, pronostic 1X2 de chaque match.
- Détail : tous les marchés avec probabilité, cote juste, meilleure cote, value, niveau de confiance.
- Détail d'un match : ~170 sélections réparties en onglets (résultat, buts, équipes, mi-temps,
  combinés officiels, corners, cartons), avec cote juste et taux de réussite réel mesuré.
- Modulation : curseurs (attaque, corners, cartons) pour intégrer une information (absence, arbitre…) ;
  toutes les probabilités se recalculent instantanément.
- Combiné : probabilité calculée en temps réel sur le téléphone par le même jumeau que le serveur
  (parité vérifiée sur 1 062 cas, écart < 1e-13) ; sélections d'un même match combinées exactement ;
  bonus de gains du bookmaker pris en compte dans la valeur attendue.
- Assistant : construit le combiné le plus probable selon le nombre de matchs, la cote minimale par
  sélection et les types de paris autorisés.
- Mode haute confiance, classement des pronostiqueurs, réglage de l'adresse du serveur.
- Sans serveur, l'application affiche des données de démonstration (`assets/demo.json`).
- Captures d'écran : `docs/captures/` (générées par `CapturesEcransTest`).

## Données

Les fichiers de football-data.co.uk sont réservés à un **usage privé**. Pour une application
publique ou commerciale, voir `docs/recherche/03_sources-de-donnees.md`.

## Avertissement

Aucun modèle ne garantit de gain. L'application présente des probabilités, jamais des « pronos sûrs ».
Jouer comporte des risques : endettement, dépendance. Aide : Joueurs Info Service 09 74 75 13 13.
