"""Jumeau numérique d'un match : un seul modèle de probabilité pour TOUT ce qui peut se passer.

Composantes (indépendantes entre elles, cohérentes à l'intérieur) :
- BUTS     : loi jointe (score 1re mi-temps, score final). Le score final vient de la matrice
             calibrée du moteur (marché + Dixon-Coles). Sachant le score final (i, j), les buts de
             1re mi-temps suivent une loi binomiale ; la part de 1re mi-temps augmente avec le
             nombre de buts (41,8 % pour 1 but, 45,5 % pour 6 buts, mesuré sur 22 832 matchs).
- CORNERS  : total des corners ~ binomiale négative, réparti entre les équipes par une
             bêta-binomiale (les corners des deux équipes sont négativement corrélés : −0,2).
- CARTONS  : cartons des deux équipes ~ Poisson bivariée (les deux sont corrélés : intensité du match).

Une SÉLECTION est une expression sur un match :
    terme       = « marché[@période]:options »        ex. « 1X2:1 », « OU@MT1:1.5:plus », « CS:2-1 »
    disjonction = termes séparés par « | »             ex. « 1X2:1 | OU:2.5:plus »  (1 OU plus de 2,5)
    sélection   = disjonctions séparées par « & »      ex. « 1X2:1 & BTTS:oui »
Plusieurs sélections sur un même match sont combinées par « & » (corrélations exactes).
Sur des matchs différents, les probabilités se multiplient.

MODULATION : l'utilisateur peut corriger le modèle (ex. attaquant vedette absent : attaque × 0,85)
par basculement exponentiel exact de la loi des buts (λ → λ·f), et ajuster corners et cartons.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
from scipy.stats import betabinom, binom, nbinom, poisson

PART_1MT = (0.413, 0.0072)   # part des buts en 1re MT = a + b × (buts du match), mesurée sur données
MAX_CORNERS = 25
MAX_CARTONS = 14


# ----------------------------------------------------------------------------- catalogue
def _ou(total, ligne, sens):
    return total > ligne if sens == "plus" else total < ligne


def _res(x, y, opt):
    return {"1": x > y, "N": x == y, "2": x < y, "1N": x >= y, "12": x != y, "N2": x <= y}[opt]


def _bornes(txt):
    """« 2-4 » -> (2, 4) ; « 6+ » -> (6, inf) ; « 3 » -> (3, 3)."""
    if txt.endswith("+"):
        return int(txt[:-1]), np.inf
    if "-" in txt:
        a, b = txt.split("-")
        return int(a), int(b)
    return int(txt), int(txt)


def terme_buts(code: str, a, b, i, j):
    """Masque booléen d'un terme « buts » sur la grille (a, b, i, j) = (MT1 dom, MT1 ext, FT dom, FT ext)."""
    nom, *opts = code.split(":")
    periode = "FT"
    if "@" in nom:
        nom, periode = nom.split("@")
    x, y = {"FT": (i, j), "MT1": (a, b), "MT2": (i - a, j - b)}[periode]
    e = {"dom": x, "ext": y}
    if nom in ("1X2", "DC"):
        return _res(x, y, opts[0])
    if nom == "OU":
        return _ou(x + y, float(opts[0]), opts[1])
    if nom == "BTTS":
        m = (x > 0) & (y > 0)
        return m if opts[0] == "oui" else ~m
    if nom == "CS":
        s, t = (int(v) for v in opts[0].split("-"))
        return (x == s) & (y == t)
    if nom == "TG":                       # nombre exact (ou intervalle « 2-3 », « 6+ ») de buts
        lo, hi = _bornes(opts[0])
        return (x + y >= lo) & (x + y <= hi)
    if nom == "MG":                       # multibuts « 2-4 »
        lo, hi = _bornes(opts[0])
        return (x + y >= lo) & (x + y <= hi)
    if nom == "PI":
        return (x + y) % 2 == (0 if opts[0] == "pair" else 1)
    if nom == "MARGE":                    # dom1, dom2, dom3+, ext1, ext2, ext3+, nul
        o = opts[0]
        if o == "nul":
            return x == y
        d = (x - y) if o.startswith("dom") else (y - x)
        lo, hi = _bornes(o[3:])
        return (d >= lo) & (d <= hi)
    if nom == "EQ_OU":                    # total d'une équipe : EQ_OU:dom:1.5:plus
        return _ou(e[opts[0]], float(opts[1]), opts[2])
    if nom == "EQ_TG":                    # buts exacts d'une équipe : EQ_TG:dom:2 ou 3+
        lo, hi = _bornes(opts[1])
        return (e[opts[0]] >= lo) & (e[opts[0]] <= hi)
    if nom == "EQ_PI":
        return e[opts[0]] % 2 == (0 if opts[1] == "pair" else 1)
    if nom == "MARQUE":                   # MARQUE:dom:oui
        m = e[opts[0]] > 0
        return m if opts[1] == "oui" else ~m
    if nom == "CLEAN":                    # CLEAN:dom:oui -> le domicile n'encaisse pas
        adv = y if opts[0] == "dom" else x
        m = adv == 0
        return m if opts[1] == "oui" else ~m
    if nom == "SANS_ENC":                 # gagne sans encaisser
        return (x > y) & (y == 0) if opts[0] == "dom" else (y > x) & (x == 0)
    if nom == "HCP3":                     # handicap européen 3 issues : HCP3:-1:1  (sur le domicile)
        h = float(opts[0])
        return _res(x + h, y, opts[1])
    if nom == "HCP2":                     # handicap 2 issues, ligne non entière : HCP2:-1.5:1
        h = float(opts[0])
        return (x + h > y) if opts[1] == "1" else (x + h < y)
    # --- marchés à deux périodes (ignorent @période) ---
    a2, b2 = i - a, j - b
    if nom == "MTFT":                     # MTFT:1/N
        o1, o2 = opts[0].split("/")
        return _res(a, b, o1) & _res(i, j, o2)
    if nom == "MT_PLUS":                  # mi-temps la plus prolifique : MT1, MT2, egal
        return {"MT1": a + b > a2 + b2, "MT2": a2 + b2 > a + b, "egal": a + b == a2 + b2}[opts[0]]
    if nom == "GAGNE_2MT":
        return (a > b) & (a2 > b2) if opts[0] == "dom" else (b > a) & (b2 > a2)
    if nom == "GAGNE_1MT":
        return (a > b) | (a2 > b2) if opts[0] == "dom" else (b > a) | (b2 > a2)
    if nom == "MARQUE_2MT":
        return (a > 0) & (a2 > 0) if opts[0] == "dom" else (b > 0) & (b2 > 0)
    if nom == "OU_2MT":                   # les deux mi-temps plus/moins de X
        return _ou(a + b, float(opts[0]), opts[1]) & _ou(a2 + b2, float(opts[0]), opts[1])
    raise KeyError(code)


def terme_comptage(nom: str, opts: list, x, y):
    """Corners ou cartons : x = domicile, y = extérieur."""
    if nom == "OU":
        return _ou(x + y, float(opts[0]), opts[1])
    if nom == "1X2":
        return _res(x, y, opts[0])
    if nom == "EQ_OU":
        return _ou(x if opts[0] == "dom" else y, float(opts[1]), opts[2])
    if nom == "HCP2":
        h = float(opts[0])
        return (x + h > y) if opts[1] == "1" else (x + h < y)
    if nom == "PI":
        return (x + y) % 2 == (0 if opts[0] == "pair" else 1)
    if nom == "TOTAL":
        lo, hi = _bornes(opts[0])
        return (x + y >= lo) & (x + y <= hi)
    raise KeyError(nom)


def composante(code: str) -> str:
    return "corners" if code.startswith("CORNERS_") else "cartons" if code.startswith("CARTONS_") else "buts"


# ----------------------------------------------------------------------------- lois
def loi_nb(moyenne: float, k: float, n: int) -> np.ndarray:
    """Binomiale négative de moyenne m et dispersion k (variance = m + m²/k)."""
    x = np.arange(n + 1)
    p = nbinom.pmf(x, k, k / (k + moyenne)) if np.isfinite(k) else poisson.pmf(x, moyenne)
    return p / p.sum()


def loi_poisson_bivariee(m1: float, m2: float, cov: float, n: int) -> np.ndarray:
    """X = U + W, Y = V + W avec U, V, W de Poisson ; cov(X, Y) = λ_W."""
    w = max(0.0, min(cov, 0.95 * min(m1, m2)))
    u, v = m1 - w, m2 - w
    x = np.arange(n + 1)
    P = np.zeros((n + 1, n + 1))
    pw = poisson.pmf(x, w)
    pu, pv = poisson.pmf(x, u), poisson.pmf(x, v)
    for k in range(n + 1):
        P[k:, k:] += pw[k] * np.outer(pu[: n + 1 - k], pv[: n + 1 - k])
    return P / P.sum()


def loi_corners(m_dom: float, m_ext: float, k_total: float, rho: float, n: int = MAX_CORNERS) -> np.ndarray:
    """Total ~ binomiale négative ; répartition domicile/extérieur ~ bêta-binomiale.
    P[x, y] = P(corners dom = x, corners ext = y)."""
    mt = m_dom + m_ext
    t = np.arange(2 * n + 1)
    pt = nbinom.pmf(t, k_total, k_total / (k_total + mt))
    p = m_dom / mt
    P = np.zeros((n + 1, n + 1))
    for tot in range(2 * n + 1):
        if pt[tot] < 1e-12:
            continue
        x = np.arange(tot + 1)
        if rho > 0:
            c = 1 / rho - 1
            px = betabinom.pmf(x, tot, p * c, (1 - p) * c)
        else:
            px = binom.pmf(x, tot, p)
        ok = (x <= n) & (tot - x <= n)
        P[x[ok], tot - x[ok]] += pt[tot] * px[ok]
    return P / P.sum()


# ----------------------------------------------------------------------------- jumeau
@dataclass
class JumeauMatch:
    matrice: np.ndarray                     # P(score final = i-j), calibrée
    part_1mt: tuple = PART_1MT              # (a, b) : part 1re MT = a + b × total de buts
    corners: tuple = (5.3, 4.4, 56.0, 0.09) # (moy. dom, moy. ext, dispersion du total, corrélation de répartition)
    cartons: tuple = (1.9, 2.1, 0.38)       # (moyenne dom, moyenne ext, covariance)
    _cache: dict = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self):
        M = np.asarray(self.matrice, float)
        self.matrice = M / M.sum()

    # --- grilles -------------------------------------------------------------------
    def grille_buts(self):
        if "buts" not in self._cache:
            n = self.matrice.shape[0]
            k = np.arange(n)
            a0, b0 = self.part_1mt
            G = np.zeros((n, n, n, n))
            for i in range(n):
                for j in range(n):
                    s = min(max(a0 + b0 * (i + j), 0.05), 0.95)
                    G[:, :, i, j] = self.matrice[i, j] * np.outer(binom.pmf(k, i, s), binom.pmf(k, j, s))
            self._cache["buts"] = (G, np.indices(G.shape))
        return self._cache["buts"]

    def grille(self, comp: str):
        if comp == "buts":
            return self.grille_buts()
        if comp not in self._cache:
            if comp == "corners":
                P = loi_corners(*self.corners)
            else:
                md, me, c = self.cartons
                P = loi_poisson_bivariee(md, me, c, MAX_CARTONS)
            self._cache[comp] = (P, np.indices(P.shape))
        return self._cache[comp]

    def _masque(self, terme: str, idx) -> np.ndarray:
        comp = composante(terme)
        if comp == "buts":
            return terme_buts(terme, *idx)
        nom, *opts = terme.split(":")
        return terme_comptage(nom.split("_", 1)[1], opts, *idx)

    # --- probabilité d'une sélection ------------------------------------------------
    def proba(self, selection: str | list[str]) -> float:
        """Probabilité d'une sélection (ou d'une liste de sélections sur ce match, combinées)."""
        expr = " & ".join(selection) if isinstance(selection, list) else selection
        par_comp: dict[str, np.ndarray] = {}
        for disj in expr.split("&"):
            termes = [t.strip() for t in disj.split("|") if t.strip()]
            comps = {composante(t) for t in termes}
            if len(comps) != 1:
                raise ValueError("Un « ou » doit porter sur une seule famille (buts, corners ou cartons)")
            comp = comps.pop()
            P, idx = self.grille(comp)
            m = np.zeros(P.shape, bool)
            for t in termes:
                m |= self._masque(t, idx)
            par_comp[comp] = par_comp.get(comp, np.ones(P.shape, bool)) & m
        p = 1.0
        for comp, m in par_comp.items():
            p *= float(self.grille(comp)[0][m].sum())
        return p

    # --- modulation par l'utilisateur ----------------------------------------------
    def moduler(self, attaque_dom: float = 1.0, attaque_ext: float = 1.0,
                corners_dom: float = 1.0, corners_ext: float = 1.0,
                cartons: float = 1.0) -> "JumeauMatch":
        """Ex. attaque_dom = 0,85 : le domicile marquera 15 % de buts en moins (attaquant absent).
        Basculement exponentiel : P'(i, j) ∝ P(i, j) · f_dom^i · f_ext^j  (exact pour Poisson)."""
        n = self.matrice.shape[0]
        k = np.arange(n)
        M = self.matrice * np.outer(attaque_dom ** k, attaque_ext ** k)
        md, me, kc, rc = self.corners
        cd, ce, cc = self.cartons
        return replace(self, matrice=M / M.sum(), corners=(md * corners_dom, me * corners_ext, kc, rc),
                       cartons=(cd * cartons, ce * cartons, cc * cartons), _cache={})

    def vers_json(self) -> dict:
        return {"matrice": np.round(self.matrice, 6).tolist(),
                "part_1mt": [round(float(v), 5) for v in self.part_1mt],
                "corners": [round(float(v), 4) for v in self.corners],
                "cartons": [round(float(v), 4) for v in self.cartons]}


def proba_combine(legs: list[tuple[str, str]], jumeaux: dict[str, JumeauMatch]) -> dict:
    """legs = [(match_id, sélection), ...] -> probabilité du combiné et détail par match."""
    par_match: dict[str, list[str]] = {}
    for mid, sel in legs:
        par_match.setdefault(mid, []).append(sel)
    detail = {mid: jumeaux[mid].proba(sels) for mid, sels in par_match.items()}
    p = float(np.prod(list(detail.values()))) if detail else 0.0
    return {"proba": p, "cote_juste": 1 / p if p > 0 else None, "par_match": detail,
            "meme_match": any(len(v) > 1 for v in par_match.values())}


# ----------------------------------------------------------------------------- catalogue affiché
def catalogue() -> list[tuple[str, str, list[tuple[str, str]]]]:
    """(groupe, titre du marché, [(code, libellé)]) — tous les marchés proposés à l'utilisateur."""
    def res(prefixe, suffixe=""):
        return [(f"{prefixe}:1", f"1{suffixe}"), (f"{prefixe}:N", f"N{suffixe}"), (f"{prefixe}:2", f"2{suffixe}")]

    def dc(p):
        return [(f"{p}:1N", "1N"), (f"{p}:12", "12"), (f"{p}:N2", "N2")]

    def ou(p, lignes):
        return [(f"{p}:{l}:{s}", f"{'Plus' if s == 'plus' else 'Moins'} de {str(l).replace('.', ',')}")
                for l in lignes for s in ("plus", "moins")]

    cat = [
        ("Résultat", "1X2", res("1X2")),
        ("Résultat", "Double chance", dc("DC")),
        ("Résultat", "Écart de victoire", [(f"MARGE:{m}", t) for m, t in
            (("dom1", "Dom. par 1"), ("dom2", "Dom. par 2"), ("dom3+", "Dom. par 3+"), ("nul", "Nul"),
             ("ext1", "Ext. par 1"), ("ext2", "Ext. par 2"), ("ext3+", "Ext. par 3+"))]),
        ("Résultat", "Handicap 3 issues (-1 domicile)", res("HCP3:-1")),
        ("Résultat", "Handicap 3 issues (+1 domicile)", res("HCP3:1")),
        ("Résultat", "Handicap -1,5 domicile", [("HCP2:-1.5:1", "Domicile -1,5"), ("HCP2:-1.5:2", "Extérieur +1,5")]),
        ("Buts", "Plus / moins (match)", ou("OU", [0.5, 1.5, 2.5, 3.5, 4.5, 5.5])),
        ("Buts", "Les deux équipes marquent", [("BTTS:oui", "Oui"), ("BTTS:non", "Non")]),
        ("Buts", "Nombre exact de buts", [(f"TG:{n}", t) for n, t in
            (("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6+", "6+"))]),
        ("Buts", "Multibuts", [(f"MG:{r}", r) for r in ("1-2", "1-3", "2-3", "2-4", "3-4", "3-5", "4-6")]),
        ("Buts", "Pair / impair", [("PI:pair", "Pair"), ("PI:impair", "Impair")]),
        ("Équipes", "Buts du domicile", ou("EQ_OU:dom", [0.5, 1.5, 2.5])),
        ("Équipes", "Buts de l'extérieur", ou("EQ_OU:ext", [0.5, 1.5, 2.5])),
        ("Équipes", "Cage inviolée", [("CLEAN:dom:oui", "Domicile n'encaisse pas"), ("CLEAN:ext:oui", "Extérieur n'encaisse pas")]),
        ("Équipes", "Gagne sans encaisser", [("SANS_ENC:dom", "Domicile"), ("SANS_ENC:ext", "Extérieur")]),
        ("Équipes", "Marque dans les 2 mi-temps", [("MARQUE_2MT:dom", "Domicile"), ("MARQUE_2MT:ext", "Extérieur")]),
        ("Équipes", "Gagne les 2 mi-temps", [("GAGNE_2MT:dom", "Domicile"), ("GAGNE_2MT:ext", "Extérieur")]),
        ("Équipes", "Gagne au moins une mi-temps", [("GAGNE_1MT:dom", "Domicile"), ("GAGNE_1MT:ext", "Extérieur")]),
        ("Mi-temps", "1X2 1re mi-temps", res("1X2@MT1")),
        ("Mi-temps", "Double chance 1re mi-temps", dc("DC@MT1")),
        ("Mi-temps", "Plus / moins 1re mi-temps", ou("OU@MT1", [0.5, 1.5, 2.5])),
        ("Mi-temps", "Les deux marquent 1re mi-temps", [("BTTS@MT1:oui", "Oui"), ("BTTS@MT1:non", "Non")]),
        ("Mi-temps", "1X2 2e mi-temps", res("1X2@MT2")),
        ("Mi-temps", "Plus / moins 2e mi-temps", ou("OU@MT2", [0.5, 1.5, 2.5])),
        ("Mi-temps", "Mi-temps / fin de match", [(f"MTFT:{a}/{b}", f"{a}/{b}") for a in "1N2" for b in "1N2"]),
        ("Mi-temps", "Mi-temps la plus prolifique", [("MT_PLUS:MT1", "1re"), ("MT_PLUS:MT2", "2e"), ("MT_PLUS:egal", "Égalité")]),
        ("Combinés officiels", "1X2 + les deux marquent", [(f"1X2:{r} & BTTS:{b}", f"{r} & {'Oui' if b == 'oui' else 'Non'}")
            for r in "1N2" for b in ("oui", "non")]),
        ("Combinés officiels", "1X2 + plus/moins 2,5", [(f"1X2:{r} & OU:2.5:{s}", f"{r} & {'+' if s == 'plus' else '-'}2,5")
            for r in "1N2" for s in ("plus", "moins")]),
        ("Combinés officiels", "Double chance + plus/moins 2,5", [(f"DC:{r} & OU:2.5:{s}", f"{r} & {'+' if s == 'plus' else '-'}2,5")
            for r in ("1N", "12", "N2") for s in ("plus", "moins")]),
        ("Combinés officiels", "Plus/moins 2,5 + les deux marquent", [(f"OU:2.5:{s} & BTTS:{b}", f"{'+' if s == 'plus' else '-'}2,5 & {'Oui' if b == 'oui' else 'Non'}")
            for s in ("plus", "moins") for b in ("oui", "non")]),
        ("Corners", "Total corners", ou("CORNERS_OU", [7.5, 8.5, 9.5, 10.5, 11.5])),
        ("Corners", "Plus de corners", res("CORNERS_1X2")),
        ("Corners", "Tranche de corners", [("CORNERS_TOTAL:0-8", "0-8"), ("CORNERS_TOTAL:9-11", "9-11"), ("CORNERS_TOTAL:12+", "12+")]),
        ("Corners", "Corners du domicile", ou("CORNERS_EQ_OU:dom", [3.5, 4.5, 5.5])),
        ("Corners", "Corners de l'extérieur", ou("CORNERS_EQ_OU:ext", [3.5, 4.5, 5.5])),
        ("Cartons", "Total cartons jaunes", ou("CARTONS_OU", [2.5, 3.5, 4.5, 5.5])),
        ("Cartons", "Plus de cartons", res("CARTONS_1X2")),
    ]
    return cat
