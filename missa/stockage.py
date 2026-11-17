"""Base de données SQLite : pronostiqueurs et leurs pronostics.

Règles d'intégrité (indispensables pour un historique honnête) :
- un pronostic n'est accepté qu'AVANT le coup d'envoi ;
- il ne peut être ni modifié ni supprimé ;
- après le match, on enregistre la cote de clôture pour calculer le CLV.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import marge
from .pronostiqueurs import Pronostic, evaluer
from .selections import SELECTIONS

BASE = Path(__file__).resolve().parent.parent / "data" / "missa.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS pronostiqueurs (
    nom TEXT PRIMARY KEY,
    source TEXT,
    cree_le TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pronostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pronostiqueur TEXT NOT NULL REFERENCES pronostiqueurs(nom),
    match_id TEXT NOT NULL,
    selection TEXT NOT NULL,
    cote REAL NOT NULL,
    coup_envoi TEXT NOT NULL,
    enregistre_le TEXT NOT NULL,
    proba_juste_cloture REAL,
    UNIQUE (pronostiqueur, match_id, selection)
);
CREATE TRIGGER IF NOT EXISTS pas_de_modification BEFORE UPDATE OF selection, cote, coup_envoi,
    enregistre_le, pronostiqueur, match_id ON pronostics
BEGIN SELECT RAISE(ABORT, 'Un pronostic ne peut pas être modifié'); END;
CREATE TRIGGER IF NOT EXISTS pas_de_suppression BEFORE DELETE ON pronostics
BEGIN SELECT RAISE(ABORT, 'Un pronostic ne peut pas être supprimé'); END;
"""


def _maintenant() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Stockage:
    def __init__(self, chemin: Path | str = BASE):
        Path(chemin).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(chemin), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def ajouter_pronostiqueur(self, nom: str, source: str = "") -> None:
        self.db.execute("INSERT OR IGNORE INTO pronostiqueurs VALUES (?, ?, ?)",
                        (nom, source, _maintenant().isoformat()))
        self.db.commit()

    def ajouter_pronostic(self, pronostiqueur: str, match_id: str, selection: str, cote: float,
                          coup_envoi: datetime, maintenant: datetime | None = None) -> int:
        maintenant = maintenant or _maintenant()
        if selection not in SELECTIONS:
            raise ValueError(f"Sélection inconnue : {selection}")
        if cote <= 1.0:
            raise ValueError("La cote doit être supérieure à 1")
        if maintenant >= coup_envoi:
            raise ValueError("Refusé : le match a déjà commencé (pronostic après coup)")
        self.ajouter_pronostiqueur(pronostiqueur)
        cur = self.db.execute(
            "INSERT INTO pronostics (pronostiqueur, match_id, selection, cote, coup_envoi, "
            "enregistre_le) VALUES (?, ?, ?, ?, ?, ?)",
            (pronostiqueur, match_id, selection, cote, coup_envoi.isoformat(),
             maintenant.isoformat()))
        self.db.commit()
        return cur.lastrowid

    def cloturer_match(self, match_id: str, cotes_cloture: dict[str, list[float]]) -> int:
        """Enregistre la probabilité juste de clôture des sélections d'un match.

        cotes_cloture : {"1x2": [H, N, A], "ou25": [plus, moins]} (cotes de clôture brutes)."""
        probas = {}
        if "1x2" in cotes_cloture:
            p = marge.probabilites(cotes_cloture["1x2"], "puissance")
            probas |= {"1": p[0], "N": p[1], "2": p[2], "1N": p[0] + p[1],
                       "12": p[0] + p[2], "N2": p[1] + p[2]}
        if "ou25" in cotes_cloture:
            p = marge.probabilites(cotes_cloture["ou25"], "abrams")
            probas |= {"plus_2.5": p[0], "moins_2.5": p[1]}
        n = 0
        for sel, pr in probas.items():
            n += self.db.execute(
                "UPDATE pronostics SET proba_juste_cloture = ? WHERE match_id = ? AND selection = ?"
                " AND proba_juste_cloture IS NULL", (float(pr), match_id, sel)).rowcount
        self.db.commit()
        return n

    def importer_csv(self, chemin) -> dict:
        """Importe des pronostics d'experts depuis un CSV (colonnes : pronostiqueur, match_id,
        selection, cote, enregistre_le, coup_envoi — dates ISO). Les lignes enregistrées après
        le coup d'envoi sont refusées. L'historique Git du fichier sert de preuve d'horodatage."""
        import csv
        ok, refus = 0, []
        with open(chemin, encoding="utf-8") as f:
            for n, r in enumerate(csv.DictReader(f), start=2):
                try:
                    self.ajouter_pronostic(
                        r["pronostiqueur"].strip(), r["match_id"].strip(), r["selection"].strip(),
                        float(r["cote"]), datetime.fromisoformat(r["coup_envoi"].strip()),
                        maintenant=datetime.fromisoformat(r["enregistre_le"].strip()))
                    ok += 1
                except Exception as e:  # ligne invalide ou doublon
                    refus.append(f"ligne {n} : {e}")
        return {"importes": ok, "refuses": refus}

    def pronostics(self, pronostiqueur: str | None = None, match_id: str | None = None) -> list:
        q, args = "SELECT * FROM pronostics WHERE 1=1", []
        if pronostiqueur:
            q, args = q + " AND pronostiqueur = ?", args + [pronostiqueur]
        if match_id:
            q, args = q + " AND match_id = ?", args + [match_id]
        return [dict(r) for r in self.db.execute(q + " ORDER BY coup_envoi", args)]

    def _objets(self, lignes) -> list[Pronostic]:
        return [Pronostic(r["pronostiqueur"], r["match_id"], r["selection"], r["cote"],
                          r["proba_juste_cloture"],
                          r["enregistre_le"] < r["coup_envoi"]) for r in lignes]

    def classement(self) -> list[dict]:
        noms = [r["nom"] for r in self.db.execute("SELECT nom FROM pronostiqueurs")]
        notes = [{"nom": n, **evaluer(self._objets(self.pronostics(n)))} for n in noms]
        return sorted(notes, key=lambda d: d["t_score"], reverse=True)

    def avis_match(self, match_id: str) -> list[dict]:
        """Pronostics d'un match avec l'ajustement de leur auteur."""
        notes = {d["nom"]: d for d in self.classement()}
        return [{"pronostiqueur": r["pronostiqueur"], "selection": r["selection"],
                 "cote": r["cote"], "ajustement": notes[r["pronostiqueur"]]["ajustement"],
                 "statut": notes[r["pronostiqueur"]]["statut"]}
                for r in self.pronostics(match_id=match_id)]
