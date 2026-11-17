"""Classement Elo pour clubs, avec multiplicateur d'écart de buts (World Football Elo)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Elo:
    k: float = 20.0
    avantage_domicile: float = 70.0
    note_initiale: float = 1500.0
    notes: dict = field(default_factory=dict)

    def note(self, equipe: str) -> float:
        return self.notes.get(equipe, self.note_initiale)

    def ecart(self, dom: str, ext: str) -> float:
        """Écart de notes du point de vue du domicile (avantage domicile inclus)."""
        return self.note(dom) + self.avantage_domicile - self.note(ext)

    def attendu(self, dom: str, ext: str) -> float:
        return 1.0 / (10 ** (-self.ecart(dom, ext) / 400) + 1)

    @staticmethod
    def multiplicateur(ecart_buts: int) -> float:
        n = abs(ecart_buts)
        return 1.0 if n <= 1 else 1.5 if n == 2 else (11 + n) / 8

    def mettre_a_jour(self, dom: str, ext: str, buts_dom: int, buts_ext: int) -> None:
        w = 1.0 if buts_dom > buts_ext else 0.5 if buts_dom == buts_ext else 0.0
        d = self.k * self.multiplicateur(buts_dom - buts_ext) * (w - self.attendu(dom, ext))
        self.notes[dom] = self.note(dom) + d
        self.notes[ext] = self.note(ext) - d

    def nouvelle_saison(self, equipes_presentes: set, regression: float = 0.2) -> None:
        """Régression partielle vers la moyenne ; promus = moyenne des notes basses."""
        if not self.notes:
            return
        moy = sum(self.notes.values()) / len(self.notes)
        for e in list(self.notes):
            self.notes[e] = moy + (1 - regression) * (self.notes[e] - moy)
        connues = sorted(self.notes[e] for e in equipes_presentes if e in self.notes)
        base = (sum(connues[:3]) / 3) if len(connues) >= 3 else moy - 100
        for e in equipes_presentes:
            self.notes.setdefault(e, base)
