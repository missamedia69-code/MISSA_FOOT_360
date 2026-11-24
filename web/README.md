# Application web MISSA FOOT 360

Version navigateur des 5 modules de l'application Android : **Accueil, Analyses,
Ticket, Stats, Profil**. Elle reprend la charte (vert néon sur charbon, ambre pour
les compétitions) et, surtout, **le même moteur de probabilités** : `js/jumeau.js`
est un port sans dépendance de `missa/jumeau.py`. Toutes les probabilités sont
calculées dans le navigateur, y compris les 193 marchés d'un match et les
corrélations entre sélections d'un même match.

## Lancer

```bash
python3 web/scripts/preparer_donnees.py     # génère web/data/donnees.json (une seule fois)
python3 web/serveur.py                      # http://0.0.0.0:8080
```

Aucun `npm install`, aucune compilation : HTML + CSS + ES modules + un serveur
de fichiers de la bibliothèque standard Python. Le serveur écoute sur `0.0.0.0`
(aperçu distant compatible) et accepte `--host`, `--port` et `MISSA_PORT`.

### Données

`web/scripts/preparer_donnees.py` choisit, par ordre de priorité :

1. `data/pronostics.json` (fraîchement produit par `scripts/generer_pronostics.py`) ;
2. `android/app/src/main/assets/demo.json` (démonstration hors ligne : 113 matchs,
   14 championnats, 29 valeurs, tables de calibration, statistiques du moteur).

Il y ajoute `data/calibration.json`, `data/modele.json` et
`data/fiabilite_marches.json`. Relancez-le après chaque génération de pronostics.

### Connexion à l'API FastAPI (facultative)

```bash
MISSA_CLE_ADMIN=un-secret .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
python3 web/serveur.py --port 8080
```

Dans « Profil → Réglages », indiquez `/api` puis « Utiliser ». Le serveur web
relaye `/api/*` vers l'API (`MISSA_API`, `http://127.0.0.1:8000` par défaut), ce
qui évite les problèmes CORS puisque tout passe par la même origine. Sans API,
l'application reste entièrement fonctionnelle hors ligne ; le bouton « Local »
restaure les données de démonstration.

## Modules

| Module | Contenu |
|---|---|
| **Accueil** | Indicateurs (113 matchs, 62,3 % de réussite mesurée, sélections fiables), filtres de jour, matchs recommandés par probabilité, valeurs détectées (CLV), courbe de calibration. |
| **Analyses** | Matchs par date et championnat, recherche, mode haute confiance, 8 marchés rapides par match, ajout direct au ticket, accès au détail. |
| **Détail** | Aperçu (1X2, marchés clés, sources du pool, scores probables), **193 marchés** en 8 familles avec taux de réussite réel mesuré, modulation en direct (attaque, corners, cartons), forme des équipes, matrice 10×10 des scores, face-à-face. |
| **Ticket** | Probabilité exacte du combiné, cote totale / cote juste, mise, gain potentiel, espérance, valeur, Kelly indicatif, cotes éditables, assistant de combiné, enregistrement dans le profil. |
| **Stats** | Performance sur saisons jamais vues, réussite par type et par niveau de confiance, courbe de calibration 1X2, fiabilité par famille, combinés multi-matchs, paramètres appris. |
| **Profil** | Réglages (serveur, devise, mise, haute confiance), experts (CLV), conseils de modération, historique des tickets. |

Ticket, réglages et historique sont conservés dans `localStorage` du navigateur.

Captures d'écran (générées avec un navigateur headless) : `docs/captures_web/`.

## Moteur et parité

`js/jumeau.js` reproduit :

- la loi jointe (score de 1re mi-temps, score final) à partir de la matrice calibrée ;
- les corners (binomiale négative + répartition bêta-binomiale) ;
- les cartons (Poisson bivariée) ;
- les expressions de sélection `terme | terme` (OU), `facteur & facteur` (ET),
  les marchés `@MT1` / `@MT2`, handicaps, combinés officiels ;
- la modulation exponentielle λ → λ·f ;
- le produit entre matchs et les corrélations exactes dans un même match.

Les fonctions spéciales (log Γ, log β, binomiale négative, bêta-binomiale) sont
implémentées en JavaScript pur : aucun `node_modules`.

Vérification automatique (409 probabilités : catalogue complet sur 2 matchs,
modulations, combinés officiels, ticket multi-matchs) :

```bash
.venv/bin/pip install numpy scipy
.venv/bin/python web/tests/parite.py        # écart maximal ≈ 1,3 × 10⁻¹⁴
.venv/bin/python -m pytest tests/test_jumeau_web.py -q
```

Le harnais `web/tests/jumeau_node.mjs` exécute le moteur JS sous Node et
`web/tests/parite.py` compare ses résultats à `missa/jumeau.py`. Le test
`tests/test_jumeau_web.py` relance cette comparaison depuis `pytest` (ignoré si
NumPy, SciPy ou Node sont absents).

### Intégration continue

`.github/workflows/web.yml` rejoue à chaque `push` / pull request : syntaxe
JavaScript, génération des données hors ligne, parité des 409 probabilités et
suite `pytest`. C'est le garde-fou contre toute divergence entre
`missa/jumeau.py` et son port navigateur. Lancement manuel possible depuis
l'onglet « Actions ».

## Fichiers

```
web/
├── index.html                  structure, navigation, icônes SVG
├── css/styles.css              charte graphique, responsive (sidebar → nav basse)
├── js/jumeau.js                moteur de probabilités (port de missa/jumeau.py)
├── js/app.js                   état, 5 modules, ticket, graphiques, réglages
├── data/donnees.json           jeu de données généré
├── scripts/preparer_donnees.py génération du jeu de données
├── serveur.py                  serveur statique + proxy /api/*
├── tests/parite.py             comparaison Python ↔ navigateur
├── tests/jumeau_node.mjs       harnais Node
└── package.json                type: module (pour les tests Node uniquement)
```

## Avertissement

Aucun modèle ne garantit de gain. L'application présente des probabilités, jamais
des « pronos sûrs ». Jouer comporte des risques : endettement, dépendance.
Aide : Joueurs Info Service 09 74 75 13 13.
