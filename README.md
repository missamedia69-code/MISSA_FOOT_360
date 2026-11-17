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
| `scripts/lancer_backtest.py` | Backtest complet → `docs/resultats_backtest.md` |

## Utilisation

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/lancer_backtest.py
```

## Données

Les fichiers de football-data.co.uk sont réservés à un **usage privé**. Pour une application
publique ou commerciale, voir `docs/recherche/03_sources-de-donnees.md`.

## Avertissement

Aucun modèle ne garantit de gain. L'application présente des probabilités, jamais des « pronos sûrs ».
Jouer comporte des risques : endettement, dépendance. Aide : Joueurs Info Service 09 74 75 13 13.
