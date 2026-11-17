# Pronostics d'experts

Ajoutez une ligne par pronostic dans `pronostics.csv`, **avant le coup d'envoi** :

```
pronostiqueur,match_id,selection,cote,enregistre_le,coup_envoi
Expert A,E0-20261122-arsenal-chelsea,1,2.10,2026-11-20T18:00:00,2026-11-22T16:30:00
```

- `match_id` : identifiant du match tel qu'il apparaît dans `pronostics.json` (champ `id`).
- `selection` : `1`, `N`, `2`, `1N`, `12`, `N2`, `plus_2.5`, `moins_2.5`, `btts_oui`, `btts_non`.
- `cote` : la cote conseillée par l'expert au moment du pronostic.
- `enregistre_le` doit être antérieur à `coup_envoi`, sinon la ligne est refusée.
- Ne modifiez ni ne supprimez jamais une ligne : l'historique Git du fichier prouve la date
  d'enregistrement de chaque pronostic.

Après chaque match, la publication automatique calcule la valeur obtenue contre la cote de clôture
(CLV). Un expert n'influence les probabilités qu'après 50 pronostics et une preuve statistique
(t-score ≥ 2).
