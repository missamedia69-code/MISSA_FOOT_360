# Notes de recherche — Sources de données et licences (vérifié le 17/11/2026)

| Source | Contenu | Prix | Usage commercial |
|---|---|---|---|
| **football-data.co.uk** | Résultats, stats, cotes ouverture/clôture (CSV) depuis 1993 | Gratuit | **Non** : usage privé uniquement |
| **football-data.org** (API) | Calendrier, résultats, classements ; compos (+29 €) ; cotes 1X2 (+15 €) ; stats (+15 €) | Gratuit (12 compétitions, 10 appels/min) → 49–199 €/mois | Conditions non publiées → demander une licence écrite |
| **The Odds API** | Cotes de 100+ bookmakers (dont Pinnacle, Betfair), 1X2, handicaps, totaux ; historique depuis juin 2020 (instantanés toutes les 5 min) | Gratuit 500 crédits/mois ; 30–249 $/mois | **Oui**, affichage et calculs dérivés autorisés ; revente des données brutes interdite |
| **Sportmonks** | Calendrier, compos, blessures/suspensions, stats, **xG** (+29 €), cotes 50+ bookmakers | Gratuit 2 ligues ; 29–249 €/mois | Conditions à lire avant achat |
| **StatsBomb open data** | Événements détaillés, compétitions sélectionnées | Gratuit | Recherche seulement (logo + citation) |
| **Pinnacle API** | Cotes Pinnacle | Sur demande, coût variable | Cotes propriétaires, accord écrit obligatoire |
| **Bet2Invest** | Pronostiqueurs certifiés sur cotes Pinnacle, CLV suivi | — | Reproduction interdite sans accord |

Non vérifiables (sites inaccessibles) : API-Football, Understat, ClubElo API, Betfair historique,
Pyckio/Tipstrr, Blogabet.

## Recommandation

1. **Développement privé (gratuit)** : football-data.co.uk pour l'historique (cotes de clôture,
   indispensables au backtest) + The Odds API gratuit pour quelques cotes en direct.
2. **Application publique / commerciale** :
   - cotes : **The Odds API** (payant) — on enregistre nous-mêmes les cotes à intervalles réguliers
     → on obtient ouverture, mouvements et **clôture** (= ce qu'il faut pour le CLV) ;
   - matchs, compos, blessures, xG : **Sportmonks** ou football-data.org payant, après lecture/obtention
     d'une licence commerciale ;
   - pronostiqueurs : on enregistre **nos propres** pronostiqueurs dans l'appli (pronostic horodaté +
     cote au moment du pronostic), et on calcule le CLV avec nos instantanés de cotes.
     Pas de copie de données d'autres plateformes sans accord.
