/* =============================================================================
 * MISSA FOOT 360 — Jumeau numérique (version navigateur, sans dépendance)
 * -----------------------------------------------------------------------------
 * Port fidèle de missa/jumeau.py : une seule loi jointe par match sert à toutes
 * les sélections (résultat, buts, mi-temps, corners, cartons, combinés officiels).
 *
 *  - BUTS     : score final (matrice calibrée) × loi binomiale des buts de 1re MT.
 *  - CORNERS  : binomiale négative du total + répartition bêta-binomiale.
 *  - CARTONS  : Poisson bivariée (intensité commune du match).
 *  - Les composantes sont indépendantes entre elles ; à l'intérieur d'un match,
 *    les corrélations sont exactes. Sur des matchs différents : produit.
 *
 * Une sélection :  termes « | » (OU), facteurs « & » (ET), ex.
 *   "1X2:1 & BTTS:oui", "DC:1N & OU:2.5:plus", "CORNERS_OU:9.5:plus".
 *
 * Parité vérifiée avec le moteur Python (numpy/scipy) : voir web/tests/parite.py.
 * ===========================================================================*/

const MAX_CORNERS = 25;
const MAX_CARTONS = 14;

/* ------------------------------------------------------------------ lois ---- */
const LANCZOS = [
  0.99999999999980993, 676.5203681218851, -1259.1392167224028,
  771.32342877765313, -176.61502916214059, 12.507343278686905,
  -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
];

function logGamma(z) {
  if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - logGamma(1 - z);
  z -= 1;
  let x = LANCZOS[0];
  for (let i = 1; i < LANCZOS.length; i++) x += LANCZOS[i] / (z + i);
  const t = z + 7.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

const logBeta = (a, b) => logGamma(a) + logGamma(b) - logGamma(a + b);
const logChoose = (n, k) => logGamma(n + 1) - logGamma(k + 1) - logGamma(n - k + 1);

function poissonPmf(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  return Math.exp(-lambda + k * Math.log(lambda) - logGamma(k + 1));
}

function binomPmf(k, n, p) {
  if (k < 0 || k > n) return 0;
  if (p <= 0) return k === 0 ? 1 : 0;
  if (p >= 1) return k === n ? 1 : 0;
  return Math.exp(logChoose(n, k) + k * Math.log(p) + (n - k) * Math.log1p(-p));
}

function nbinomPmf(k, r, p) {
  if (p <= 0) return 0;
  if (p >= 1) return k === 0 ? 1 : 0;
  return Math.exp(logGamma(k + r) - logGamma(r) - logGamma(k + 1)
    + r * Math.log(p) + k * Math.log1p(-p));
}

function betabinomPmf(k, n, a, b) {
  if (n === 0) return k === 0 ? 1 : 0;
  return Math.exp(logChoose(n, k) + logBeta(k + a, n - k + b) - logBeta(a, b));
}

/** P(score final = i-j), normalisée comme dans JumeauMatch.__post_init__. */
function normaliser(M) {
  let s = 0;
  for (const ligne of M) for (const v of ligne) s += v;
  return M.map((ligne) => ligne.map((v) => v / s));
}

/** Loi jointe des corners du domicile et de l'extérieur. */
export function loiCorners(mDom, mExt, kTotal, rho, n = MAX_CORNERS) {
  const mt = mDom + mExt;
  const p = mDom / mt;
  const pTot = kTotal / (kTotal + mt);
  const c = rho > 0 ? 1 / rho - 1 : 0;
  const P = Array.from({ length: n + 1 }, () => new Array(n + 1).fill(0));
  for (let tot = 0; tot <= 2 * n; tot++) {
    const pt = nbinomPmf(tot, kTotal, pTot);
    if (pt < 1e-12) continue;
    for (let x = 0; x <= tot; x++) {
      const y = tot - x;
      if (x > n || y > n) continue;
      const px = rho > 0
        ? betabinomPmf(x, tot, p * c, (1 - p) * c)
        : binomPmf(x, tot, p);
      P[x][y] += pt * px;
    }
  }
  let s = 0;
  for (const ligne of P) for (const v of ligne) s += v;
  for (const ligne of P) for (let i = 0; i < ligne.length; i++) ligne[i] /= s;
  return P;
}

/** Poisson bivariée : X = U + W, Y = V + W, cov(X,Y) = λ_W. */
export function loiPoissonBivariee(m1, m2, cov, n = MAX_CARTONS) {
  const w = Math.max(0, Math.min(cov, 0.95 * Math.min(m1, m2)));
  const u = m1 - w, v = m2 - w;
  const pw = Array.from({ length: n + 1 }, (_, k) => poissonPmf(k, w));
  const pu = Array.from({ length: n + 1 }, (_, k) => poissonPmf(k, u));
  const pv = Array.from({ length: n + 1 }, (_, k) => poissonPmf(k, v));
  const P = Array.from({ length: n + 1 }, () => new Array(n + 1).fill(0));
  for (let k = 0; k <= n; k++) {
    if (pw[k] === 0) continue;
    for (let i = 0; i + k <= n; i++) {
      for (let j = 0; j + k <= n; j++) P[k + i][k + j] += pw[k] * pu[i] * pv[j];
    }
  }
  let s = 0;
  for (const ligne of P) for (const x of ligne) s += x;
  for (const ligne of P) for (let i = 0; i < ligne.length; i++) ligne[i] /= s;
  return P;
}

/* -------------------------------------------------------------- expressions -- */
const OU = (total, ligne, sens) => (sens === "plus" ? total > ligne : total < ligne);

function res(x, y, opt) {
  switch (opt) {
    case "1": return x > y;
    case "N": return x === y;
    case "2": return x < y;
    case "1N": return x >= y;
    case "12": return x !== y;
    case "N2": return x <= y;
    default: throw new Error(`Option de résultat inconnue : ${opt}`);
  }
}

/** « 2-4 » -> [2,4] ; « 6+ » -> [6,Infinity] ; « 3 » -> [3,3]. */
function bornes(txt) {
  if (txt.endsWith("+")) return [parseInt(txt.slice(0, -1), 10), Infinity];
  if (txt.includes("-")) {
    const [a, b] = txt.split("-").map((v) => parseInt(v, 10));
    return [a, b];
  }
  const v = parseInt(txt, 10);
  return [v, v];
}

function composante(terme) {
  if (terme.startsWith("CORNERS_")) return "corners";
  if (terme.startsWith("CARTONS_")) return "cartons";
  return "buts";
}

function parseTerme(t) {
  const parts = t.split(":");
  let nom = parts[0];
  let periode = "FT";
  if (nom.includes("@")) [nom, periode] = nom.split("@");
  return { nom, periode, opts: parts.slice(1), prefixe: parts[0] };
}

/** Masque d'un terme « buts » sur (a,b,i,j) = (MT1 dom, MT1 ext, FT dom, FT ext). */
export function termeButs(t, a, b, i, j) {
  const { nom, periode, opts } = t;
  const [x, y] = periode === "FT" ? [i, j]
    : periode === "MT1" ? [a, b] : [i - a, j - b];
  if (periode !== "FT" && periode !== "MT1" && periode !== "MT2")
    throw new Error(`Période inconnue : ${periode}`);
  const e = { dom: x, ext: y };
  switch (nom) {
    case "1X2": case "DC": return res(x, y, opts[0]);
    case "OU": return OU(x + y, parseFloat(opts[0]), opts[1]);
    case "BTTS": {
      const m = x > 0 && y > 0;
      return opts[0] === "oui" ? m : !m;
    }
    case "CS": {
      const [s, u] = opts[0].split("-").map((v) => parseInt(v, 10));
      return x === s && y === u;
    }
    case "TG": case "MG": {
      const [lo, hi] = bornes(opts[0]);
      return x + y >= lo && x + y <= hi;
    }
    case "PI": return (x + y) % 2 === (opts[0] === "pair" ? 0 : 1);
    case "MARGE": {
      if (opts[0] === "nul") return x === y;
      const d = opts[0].startsWith("dom") ? x - y : y - x;
      const [lo, hi] = bornes(opts[0].slice(3));
      return d >= lo && d <= hi;
    }
    case "EQ_OU": return OU(e[opts[0]], parseFloat(opts[1]), opts[2]);
    case "EQ_TG": {
      const [lo, hi] = bornes(opts[1]);
      return e[opts[0]] >= lo && e[opts[0]] <= hi;
    }
    case "EQ_PI": return e[opts[0]] % 2 === (opts[1] === "pair" ? 0 : 1);
    case "MARQUE": {
      const m = e[opts[0]] > 0;
      return opts[1] === "oui" ? m : !m;
    }
    case "CLEAN": {
      const adv = opts[0] === "dom" ? y : x;
      const m = adv === 0;
      return opts[1] === "oui" ? m : !m;
    }
    case "SANS_ENC": return opts[0] === "dom" ? (x > y && y === 0) : (y > x && x === 0);
    case "HCP3": return res(x + parseFloat(opts[0]), y, opts[1]);
    case "HCP2": return opts[1] === "1"
      ? x + parseFloat(opts[0]) > y : x + parseFloat(opts[0]) < y;
    default: break;
  }
  // marchés à deux périodes
  const a2 = i - a, b2 = j - b;
  switch (nom) {
    case "MTFT": {
      const [o1, o2] = opts[0].split("/");
      return res(a, b, o1) && res(i, j, o2);
    }
    case "MT_PLUS": {
      if (opts[0] === "MT1") return a + b > a2 + b2;
      if (opts[0] === "MT2") return a2 + b2 > a + b;
      return a + b === a2 + b2;
    }
    case "GAGNE_2MT": return opts[0] === "dom" ? (a > b && a2 > b2) : (b > a && b2 > a2);
    case "GAGNE_1MT": return opts[0] === "dom" ? (a > b || a2 > b2) : (b > a || b2 > a2);
    case "MARQUE_2MT": return opts[0] === "dom" ? (a > 0 && a2 > 0) : (b > 0 && b2 > 0);
    case "OU_2MT": return OU(a + b, parseFloat(opts[0]), opts[1])
      && OU(a2 + b2, parseFloat(opts[0]), opts[1]);
    default: throw new Error(`Marché inconnu : ${nom}`);
  }
}

/** Masque d'un terme « corners » ou « cartons » sur (x,y). */
export function termeComptage(nom, opts, x, y) {
  switch (nom) {
    case "OU": return OU(x + y, parseFloat(opts[0]), opts[1]);
    case "1X2": return res(x, y, opts[0]);
    case "EQ_OU": return OU(opts[0] === "dom" ? x : y, parseFloat(opts[1]), opts[2]);
    case "HCP2": return opts[1] === "1"
      ? x + parseFloat(opts[0]) > y : x + parseFloat(opts[0]) < y;
    case "PI": return (x + y) % 2 === (opts[0] === "pair" ? 0 : 1);
    case "TOTAL": {
      const [lo, hi] = bornes(opts[0]);
      return x + y >= lo && x + y <= hi;
    }
    default: throw new Error(`Marché de comptage inconnu : ${nom}`);
  }
}

/* ------------------------------------------------------------------ jumeau -- */
export class JumeauMatch {
  constructor({ matrice, part_1mt = [0.413, 0.0072], corners = [5.3, 4.4, 56.0, 0.09],
    cartons = [1.9, 2.1, 0.38] }) {
    this.matrice = normaliser(matrice);
    this.part_1mt = part_1mt;
    this.corners = corners;
    this.cartons = cartons;
    this.n = this.matrice.length;
    this._cache = {};
  }

  /** Basculement exponentiel λ → λ·f (exact pour une loi de Poisson). */
  moduler({ attaque_dom = 1, attaque_ext = 1, corners_dom = 1, corners_ext = 1, cartons: f = 1 } = {}) {
    const M = this.matrice.map((ligne, i) => ligne.map((v, j) =>
      v * attaque_dom ** i * attaque_ext ** j));
    const [md, me, kc, rc] = this.corners;
    const [cd, ce, cc] = this.cartons;
    return new JumeauMatch({
      matrice: M,
      part_1mt: this.part_1mt,
      corners: [md * corners_dom, me * corners_ext, kc, rc],
      cartons: [cd * f, ce * f, cc * f],
    });
  }

  grille(comp) {
    if (this._cache[comp]) return this._cache[comp];
    let g;
    if (comp === "buts") {
      const [a0, b0] = this.part_1mt;
      const cells = [];
      for (let i = 0; i < this.n; i++) {
        for (let j = 0; j < this.n; j++) {
          const p = this.matrice[i][j];
          if (p === 0) continue;
          const s = Math.min(Math.max(a0 + b0 * (i + j), 0.05), 0.95);
          const pa = Array.from({ length: i + 1 }, (_, a) => binomPmf(a, i, s));
          const pb = Array.from({ length: j + 1 }, (_, b) => binomPmf(b, j, s));
          cells.push({ i, j, p, pa, pb });
        }
      }
      g = { cells };
    } else if (comp === "corners") {
      g = { P: loiCorners(...this.corners) };
    } else {
      g = { P: loiPoissonBivariee(...this.cartons, MAX_CARTONS) };
    }
    this._cache[comp] = g;
    return g;
  }

  _evaluer(comp, t, c) {
    if (comp === "buts") return termeButs(t, c.a, c.b, c.i, c.j);
    return termeComptage(t.prefixe.split("_").slice(1).join("_"), t.opts, c.x, c.y);
  }

  _somme(comp, predicate) {
    const g = this.grille(comp);
    let s = 0;
    if (comp === "buts") {
      for (const cell of g.cells) {
        for (let a = 0; a <= cell.i; a++) {
          for (let b = 0; b <= cell.j; b++) {
            if (predicate(a, b, cell.i, cell.j)) s += cell.p * cell.pa[a] * cell.pb[b];
          }
        }
      }
    } else {
      const P = g.P;
      for (let x = 0; x < P.length; x++) {
        for (let y = 0; y < P.length; y++) {
          if (P[x][y] > 0 && predicate(x, y)) s += P[x][y];
        }
      }
    }
    return s;
  }

  /** Probabilité d'une sélection ou d'une liste de sélections sur CE match. */
  proba(selection) {
    const expr = Array.isArray(selection) ? selection.join(" & ") : selection;
    const parComp = new Map();
    for (const disj of expr.split("&")) {
      const termes = disj.split("|").map((t) => t.trim()).filter(Boolean)
        .map(parseTerme);
      if (!termes.length) continue;
      const comps = new Set(termes.map((t) => composante(t.prefixe)));
      if (comps.size !== 1) throw new Error("Un « ou » doit porter sur une seule famille");
      const comp = [...comps][0];
      if (!parComp.has(comp)) parComp.set(comp, []);
      parComp.get(comp).push(termes);
    }
    let p = 1;
    for (const [comp, disjs] of parComp) {
      const test = comp === "buts"
        ? (a, b, i, j) => disjs.every((d) => d.some((t) => this._evaluer(comp, t, { a, b, i, j })))
        : (x, y) => disjs.every((d) => d.some((t) => this._evaluer(comp, t, { x, y })));
      p *= this._somme(comp, test);
    }
    return p;
  }

  /** Matrice des scores exacts (pour la carte de chaleur). */
  scores() { return this.matrice; }
}

/** Construit le jumeau d'un match à partir des données JSON du pipeline. */
export function jumeauDepuisMatch(m) { return new JumeauMatch(m.jumeau); }

/** Probabilité d'un combiné : corrélation exacte dans un match, produit entre matchs. */
export function probaCombine(legs, jumeaux, unParMatch = false) {
  const parMatch = new Map();
  for (const { matchId, code } of legs) {
    if (!parMatch.has(matchId)) parMatch.set(matchId, []);
    parMatch.get(matchId).push(code);
  }
  if (unParMatch && [...parMatch.values()].some((v) => v.length > 1))
    throw new Error("Une seule sélection par match sur un ticket (règle des bookmakers)");
  const par_match = {};
  let proba = 1;
  for (const [mid, sels] of parMatch) {
    const p = jumeaux[mid].proba(sels);
    par_match[mid] = p;
    proba *= p;
  }
  return {
    proba,
    cote_juste: proba > 0 ? 1 / proba : null,
    par_match,
    meme_match: [...parMatch.values()].some((v) => v.length > 1),
  };
}

/** Niveau de risque, comme dans l'application Android. */
export function risque(p) {
  if (p >= 0.75) return { label: "Faible", couleur: "vert" };
  if (p >= 0.5) return { label: "Modéré", couleur: "jaune" };
  if (p >= 0.3) return { label: "Élevé", couleur: "orange" };
  return { label: "Très élevé", couleur: "rouge" };
}
