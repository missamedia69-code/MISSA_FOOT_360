/* =============================================================================
 * MISSA FOOT 360 — application web (5 modules : Accueil, Analyses, Ticket,
 * Stats, Profil). Aucune dépendance : les probabilités sont calculées dans le
 * navigateur par web/js/jumeau.js, port du moteur Python du dépôt.
 * ===========================================================================*/
import { jumeauDepuisMatch, probaCombine, risque } from "./jumeau.js";

/* ------------------------------------------------------------------ état ---- */
const CLE_STOCKAGE = "missa-foot-360:v1";
const etat = {
  onglet: "accueil",
  donnees: null,
  matchs: [],
  parId: new Map(),
  dates: [],
  filtreAccueil: "aujourdhui",
  filtreDate: null,
  recherche: "",
  liguesOuvertes: new Set(),
  groupeActif: "Résultat",
  groupesMarchesOuverts: new Set(),
  rechercheMarches: "",
  detail: null,                 // { matchId, tab }
  modulation: { attaque_dom: 1, attaque_ext: 1, corners_dom: 1, corners_ext: 1, cartons: 1 },
  ticket: [],
  mise: 1000,
  reglages: { serveur: "", confiance: false, devise: "XAF" },
  historique: [],
  profilTab: "reglages",
  generateur: { nb: 3, coteMin: 1.2, types: { "1X2": true, DC: true, OU: true, BTTS: true } },
  familleFiabilite: "buts_match",
  serveurActif: false,
};

const $ = (s) => document.querySelector(s);
const contenu = $("#contenu");
const cacheJumeaux = new Map();
const cacheProbas = new Map();

/* -------------------------------------------------------------- utilitaires - */
const echapper = (v) => String(v ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (v, d = 1) => v == null || !isFinite(v) ? "—" : `${(v * 100).toFixed(d).replace(".", ",")} %`;
const cote = (v) => v == null || !isFinite(v) ? "—" : Number(v).toFixed(2).replace(".", ",");
const nombre = (v, d = 0) => new Intl.NumberFormat("fr-FR", { maximumFractionDigits: d }).format(v || 0);
const devise = () => ({ XAF: "FCFA", EUR: "€", USD: "$", AUCUNE: "" }[etat.reglages.devise] ?? "");
const montant = (v) => `${nombre(v)}${devise() ? ` ${devise()}` : ""}`;
const icone = (nom, cls = "") => `<svg class="${cls}"><use href="#ic-${nom}"/></svg>`;
const dateFr = (iso) => new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC" }).format(new Date(iso));
const dateCourte = (iso) => new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "2-digit", timeZone: "UTC" }).format(new Date(iso));
const jourFr = (iso) => new Intl.DateTimeFormat("fr-FR", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(iso));
const heureFr = (iso) => new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(new Date(iso));
const horodatage = () => new Intl.DateTimeFormat("fr-FR", { dateStyle: "short", timeStyle: "short" }).format(new Date());

const CODE_DEPUIS_CLE = {
  "1": "1X2:1", N: "1X2:N", "2": "1X2:2",
  "1N": "DC:1N", "12": "DC:12", N2: "DC:N2",
  "plus_1.5": "OU:1.5:plus", "moins_1.5": "OU:1.5:moins",
  "plus_2.5": "OU:2.5:plus", "moins_2.5": "OU:2.5:moins",
  "plus_3.5": "OU:3.5:plus", "moins_3.5": "OU:3.5:moins",
  btts_oui: "BTTS:oui", btts_non: "BTTS:non",
  dom_marque: "MARQUE:dom:oui", ext_marque: "MARQUE:ext:oui",
};
const MARCHES_RAPIDES = [
  { cle: "1", code: "1X2:1", label: "1" },
  { cle: "N", code: "1X2:N", label: "N" },
  { cle: "2", code: "1X2:2", label: "2" },
  { cle: "1N", code: "DC:1N", label: "1N" },
  { cle: "12", code: "DC:12", label: "12" },
  { cle: "N2", code: "DC:N2", label: "N2" },
  { cle: "plus_1.5", code: "OU:1.5:plus", label: "+1,5" },
  { cle: "plus_2.5", code: "OU:2.5:plus", label: "+2,5" },
];
const FAMILLE_DU_GROUPE = {
  Résultat: "buts_match", Handicaps: "buts_match", Buts: "buts_match",
  Équipes: "buts_match", "Mi-temps": "mi_temps",
  "Combinés officiels": "combines_officiels", Corners: "corners", Cartons: "cartons",
};
const NOMS_FAMILLES = {
  buts_match: "Buts & résultat", mi_temps: "Mi-temps",
  combines_officiels: "Combinés officiels", corners: "Corners",
  cartons: "Cartons", combines_multi: "Combinés multi-matchs",
};
const COULEUR_RISQUE = { vert: "vert", jaune: "ambre", orange: "orange", rouge: "rouge" };

function toast(message, type = "ok") {
  const el = document.createElement("div");
  el.className = `toast ${type === "erreur" ? "erreur" : ""}`;
  el.innerHTML = `${icone(type === "erreur" ? "avertissement" : "verifie")}<span>${echapper(message)}</span>`;
  $("#toasts").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; setTimeout(() => el.remove(), 320); }, 2900);
}

/* --------------------------------------------------------------- stockage --- */
function sauvegarder() {
  try {
    localStorage.setItem(CLE_STOCKAGE, JSON.stringify({
      ticket: etat.ticket, mise: etat.mise, reglages: etat.reglages,
      historique: etat.historique, generateur: etat.generateur,
    }));
  } catch { /* stockage indisponible : mode dégradation silencieuse */ }
}
function chargerLocal() {
  try {
    const brut = localStorage.getItem(CLE_STOCKAGE);
    if (!brut) return;
    const d = JSON.parse(brut);
    if (Array.isArray(d.ticket)) etat.ticket = d.ticket.filter((s) => etat.parId.has(s.matchId));
    if (isFinite(d.mise)) etat.mise = Number(d.mise);
    if (d.reglages) etat.reglages = { ...etat.reglages, ...d.reglages };
    if (Array.isArray(d.historique)) etat.historique = d.historique;
    if (d.generateur) etat.generateur = { ...etat.generateur, ...d.generateur };
  } catch { /* ignore */ }
}

/* ------------------------------------------------------------------ moteur -- */
function jumeauBase(m) {
  if (!cacheJumeaux.has(m.id)) cacheJumeaux.set(m.id, jumeauDepuisMatch(m));
  return cacheJumeaux.get(m.id);
}
function probaBase(m, code) {
  const k = `${m.id}|base|${code}`;
  if (!cacheProbas.has(k)) cacheProbas.set(k, jumeauBase(m).proba(code));
  return cacheProbas.get(k);
}
function estModifie(m) {
  return etat.detail?.matchId === m.id && Object.values(etat.modulation).some((v) => Math.abs(v - 1) > 1e-9);
}
function jumeauAffiche(m) {
  if (!estModifie(m)) return jumeauBase(m);
  const k = `${m.id}|mod|${JSON.stringify(etat.modulation)}`;
  if (!cacheJumeaux.has(k)) cacheJumeaux.set(k, jumeauBase(m).moduler(etat.modulation));
  return cacheJumeaux.get(k);
}
function probaAffichee(m, code) {
  if (!estModifie(m)) return probaBase(m, code);
  const k = `${m.id}|mod|${JSON.stringify(etat.modulation)}|${code}`;
  if (!cacheProbas.has(k)) cacheProbas.set(k, jumeauAffiche(m).proba(code));
  return cacheProbas.get(k);
}

function indexer(d) {
  etat.matchs = [];
  etat.parId = new Map();
  for (const c of d.championnats) {
    for (const m of c.matchs) {
      m.nomChampionnat = c.nom;
      m.codeChampionnat = c.code;
      m.date = m.coup_envoi.slice(0, 10);
      etat.matchs.push(m);
      etat.parId.set(m.id, m);
    }
  }
  etat.dates = [...new Set(etat.matchs.map((m) => m.date))].sort();
  etat.liguesOuvertes = new Set(d.championnats.filter((c) => c.matchs.length).map((c) => c.code));
  cacheJumeaux.clear();
  cacheProbas.clear();
}
function matchDe(id) { return etat.parId.get(id); }

function recoDe(m) {
  const cle = m.selection_haute_confiance || m.pronostic_principal || "1";
  const mar = m.marches?.[cle] || {};
  const code = CODE_DEPUIS_CLE[cle] || (cle.startsWith("1X2:") ? cle : `1X2:${cle}`);
  const p = mar.proba ?? probaBase(m, code);
  return { code, libelle: mar.libelle || cle, proba: p,
    cote: mar.meilleure_cote || mar.cote_juste || 1 / Math.max(p, 1e-6), confiance: mar.confiance };
}

function boutonAjouter(m, code, libelle, c, { compact = false, ajoute = false } = {}) {
  return `<button class="${compact ? "bouton-mini" : "bouton-ajouter"}${ajoute ? " ajoute" : ""}"
    data-action="ajouter" data-mid="${echapper(m.id)}" data-code="${echapper(code)}"
    data-libelle="${echapper(libelle)}" data-cote="${Number(c) || ""}"
    title="Ajouter au ticket" aria-label="Ajouter ${echapper(libelle)} au ticket">${icone("plus")}${compact ? "" : "<span>Ajouter</span>"}</button>`;
}
function dejaAuTicket(m, code) {
  return etat.ticket.some((s) => s.matchId === m.id && s.code === code);
}

/* ------------------------------------------------------------------ ticket -- */
function ajouterSelection(m, code, libelle, coteBrute) {
  if (!m || !code) return;
  let p;
  try { p = probaBase(m, code); } catch (e) { toast(`Sélection invalide : ${e.message}`, "erreur"); return; }
  const c = Number(coteBrute) > 1 ? Number(coteBrute) : Math.max(1.01, 1 / Math.max(p, 1e-9));
  const sel = {
    matchId: m.id, code, libelle, cote: c, proba: p,
    equipes: `${m.domicile} – ${m.exterieur}`, ligue: m.nomChampionnat,
    date: m.coup_envoi,
  };
  const i = etat.ticket.findIndex((s) => s.matchId === m.id);
  if (i >= 0) {
    etat.ticket[i] = sel;
    toast("Une seule sélection par match : la précédente a été remplacée");
  } else {
    etat.ticket.push(sel);
    toast(`${libelle} ajouté au ticket`);
  }
  sauvegarder();
  rendre(true);
}

function calculerTicket() {
  if (!etat.ticket.length) return null;
  let r;
  try {
    const jumeaux = {};
    for (const s of etat.ticket) {
      const m = matchDe(s.matchId);
      if (m) jumeaux[s.matchId] = jumeauBase(m);
    }
    if (Object.keys(jumeaux).length === etat.ticket.length) {
      r = probaCombine(etat.ticket.map((s) => ({ matchId: s.matchId, code: s.code })), jumeaux, true);
    } else {
      r = { proba: etat.ticket.reduce((a, s) => a * s.proba, 1) };
      r.cote_juste = r.proba > 0 ? 1 / r.proba : null;
    }
  } catch (e) {
    r = { proba: etat.ticket.reduce((a, s) => a * s.proba, 1) };
    r.cote_juste = r.proba > 0 ? 1 / r.proba : null;
  }
  const coteTotale = etat.ticket.reduce((a, s) => a * Math.max(1, Number(s.cote) || 1), 1);
  return {
    ...r, coteTotale,
    mise: etat.mise,
    gain: etat.mise * coteTotale,
    esperance: etat.mise * (r.proba * coteTotale - 1),
    valeur: r.proba * coteTotale - 1,
    risque: risque(r.proba),
  };
}

function majResumeTicket() {
  const r = calculerTicket();
  if (!r) return;
  const poser = (id, v) => { const el = document.getElementById(id); if (el) el.innerHTML = v; };
  poser("r-proba", pct(r.proba));
  poser("r-cote", cote(r.coteTotale));
  poser("r-juste", cote(r.cote_juste));
  poser("r-gain", `<span class="texte-vert">${montant(r.gain)}</span>`);
  poser("r-esperance", `<span class="${r.esperance >= 0 ? "texte-vert" : "texte-rouge"}">${montant(r.esperance)}</span>`);
  poser("r-valeur", `<span class="${r.valeur >= 0 ? "texte-vert" : "texte-rouge"}">${pct(r.valeur)}</span>`);
  poser("r-risque", `<span class="etiquette ${COULEUR_RISQUE[r.risque.couleur]}">${r.risque.label}</span>`);
  poser("r-cent", `Sur 100 tickets identiques, environ <b>${nombre(r.proba * 100)}</b> seraient gagnants.`);
  const barre = document.getElementById("r-barre");
  if (barre) barre.style.width = `${Math.min(100, r.proba * 100)}%`;
  majBarreTicket();
}

function majBarreTicket() {
  const el = $("#barre-ticket");
  const r = calculerTicket();
  const nb = etat.ticket.length;
  for (const id of ["#badge-ticket", "#badge-ticket-mobile"]) {
    const b = $(id);
    if (b) { b.hidden = nb === 0; b.textContent = nb; }
  }
  if (!r) {
    el.classList.add("vide-barre");
    el.innerHTML = `<div class="texte">Aucune sélection — explorez les analyses pour construire un ticket.</div>
      <div class="spacer"></div><button class="voir" data-action="onglet" data-onglet="analyses">Voir les matchs →</button>`;
    return;
  }
  el.classList.remove("vide-barre");
  el.innerHTML = `<div class="mini-barre" style="width:${Math.min(100, r.proba * 100)}%"></div>
    <div class="texte">Ticket : ${nb} sélection${nb > 1 ? "s" : ""}<br>
      Réussite <b>${pct(r.proba)}</b> <span class="sep">·</span> cote <b>${cote(r.coteTotale)}</b>
      <span class="gain"><span class="sep">·</span>gain <b>${montant(r.gain)}</b></span></div>
    <div class="spacer"></div><button class="voir" data-action="onglet" data-onglet="ticket">Voir →</button>`;
}

/* -------------------------------------------------------------- graphiques -- */
function barresComparees(items, legende = "gris : annoncé · vert : mesuré") {
  return items.map((it) => `<div class="barre-comparee">
    <div class="libelle"><span>${echapper(it.label)}</span><b>annoncé ${pct(it.annonce)} → <span class="texte-vert">${pct(it.reel)}</span></b></div>
    <div class="piste"><i style="width:${Math.min(100, it.annonce * 100)}%"></i><b style="width:${Math.min(100, it.reel * 100)}%"></b></div>
    <div class="legende">${legende}${it.n ? ` · ${nombre(it.n)} cas` : ""}</div>
  </div>`).join("");
}

function svgCalibration(points, { w = 520, h = 260 } = {}) {
  const m = 36, pad = 14;
  const X = (v) => m + v * (w - m - pad);
  const Y = (v) => h - m - v * (h - m - pad);
  const axes = [0, .25, .5, .75, 1].map((v) => `
    <line x1="${X(v)}" y1="${Y(0)}" x2="${X(v)}" y2="${Y(1)}" stroke="rgba(255,255,255,.07)"/>
    <line x1="${X(0)}" y1="${Y(v)}" x2="${X(1)}" y2="${Y(v)}" stroke="rgba(255,255,255,.07)"/>
    <text x="${X(v) - 8}" y="${Y(0) + 15}">${Math.round(v * 100)}</text>
    <text x="${X(0) - 25}" y="${Y(v) + 3}">${Math.round(v * 100)}</text>`).join("");
  const ligne = points.map((p, i) => `${i ? "L" : "M"}${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`).join(" ");
  const maxN = Math.max(...points.map((p) => p.n || 1), 1);
  const ronds = points.map((p) => `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="${(3 + 5 * Math.sqrt((p.n || 1) / maxN)).toFixed(1)}"
    fill="rgba(44,224,131,.75)" stroke="#0b1a11" stroke-width="1.5"><title>${pct(p.x)} annoncé → ${pct(p.y)} mesuré (${nombre(p.n)} cas)</title></circle>`).join("");
  return `<svg class="svg-chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Courbe de calibration : probabilité annoncée contre fréquence réelle">
    ${axes}
    <line x1="${X(0)}" y1="${Y(0)}" x2="${X(1)}" y2="${Y(1)}" stroke="rgba(244,189,69,.55)" stroke-dasharray="5 5"/>
    <path d="${ligne}" fill="none" stroke="var(--vert)" stroke-width="2.5"/>
    ${ronds}
    <text x="${X(.5)}" y="${h - 4}" text-anchor="middle">Probabilité annoncée (%)</text>
    <text x="12" y="${Y(.5)}" transform="rotate(-90 12 ${Y(.5)})" text-anchor="middle">Fréquence réelle (%)</text>
  </svg>`;
}

function reelMesure(groupe, p) {
  const famille = etat.donnees.fiabilite?.[FAMILLE_DU_GROUPE[groupe] || "buts_match"] || [];
  const t = famille.find((b) => p >= b.de && p < b.a) || famille[famille.length - 1];
  return t ? { reel: t.reel, n: t.n } : null;
}

/* ------------------------------------------------------------------ ACCUEIL - */
function vueAccueil() {
  const d = etat.donnees;
  const st = d.stats_moteur || {};
  const demo = d.source_donnees !== "serveur";
  const jour1 = etat.dates[0], jour2 = etat.dates[1];
  let candidats = etat.matchs.slice();
  if (etat.filtreAccueil === "aujourdhui") candidats = candidats.filter((m) => m.date === jour1);
  else if (etat.filtreAccueil === "demain") candidats = candidats.filter((m) => m.date === jour2);
  const recos = candidats.map((m) => ({ m, ...recoDe(m) }))
    .sort((a, b) => b.proba - a.proba).slice(0, 6);
  const valeurs = (d.value || []).slice().sort((a, b) => (b.valeur_corrigee || 0) - (a.valeur_corrigee || 0)).slice(0, 5);
  const cal = (d.calibration?.["1X2"] || []).map((p) => ({ x: p.proba_moyenne, y: p.taux_reel, n: p.n }));
  const nbFiables = etat.matchs.filter((m) => {
    const c = m.marches?.[m.selection_haute_confiance]?.confiance;
    return c?.haute_confiance;
  }).length;

  return `
  <section class="hero">
    <div class="bandeau-demo">${icone("info")}${demo ? "Données de démonstration (hors ligne)" : "Connecté au serveur de pronostics"}</div>
    <h2>Analyse football intelligente</h2>
    <p class="intro">Marché, Dixon-Coles et Elo combinés par un pool appris sur des saisons passées. Chaque match possède son jumeau numérique : <b>193 marchés</b> calculés à partir d'une seule loi de probabilité.</p>
    <div class="kpis">
      <div class="kpi"><strong>${etat.matchs.length}</strong><span>Matchs analysés</span></div>
      <div class="kpi"><strong>${pct(st.reussite_globale || .6233)}</strong><span>Réussite mesurée</span></div>
      <div class="kpi"><strong>${nbFiables || (d.suivi_pronostics?.confiance?.publies ?? 23)}</strong><span>Sélections fiables</span></div>
    </div>
    <p class="hero-note">Réussite mesurée sur <b>${nombre(st.pronostics_evalues || 22912)} pronostics</b> de matchs jamais vus par le moteur ; <b>${pct((st.par_niveau?.[0]?.reussite) || .9202, 0)}</b> pour la confiance très haute. ${demo ? `Semaine de démonstration : ${dateCourte(jour1)} → ${dateCourte(etat.dates.at(-1))}.` : `Généré le ${dateFr(d.genere_le)}.`}</p>
  </section>

  <div class="section">
    <div class="puces">
      <button class="puce ${etat.filtreAccueil === "aujourdhui" ? "active" : ""}" data-action="filtre-accueil" data-val="aujourdhui">Aujourd'hui · ${dateCourte(jour1)}</button>
      <button class="puce ${etat.filtreAccueil === "demain" ? "active" : ""}" data-action="filtre-accueil" data-val="demain">Demain · ${dateCourte(jour2 || jour1)}</button>
      <button class="puce ${etat.filtreAccueil === "tous" ? "active" : ""}" data-action="filtre-accueil" data-val="tous">Tous les matchs</button>
    </div>
  </div>

  <div class="accueil-colonnes">
    <div class="section">
      <div class="titre-section"><h2>Matchs recommandés</h2><button class="lien" data-action="onglet" data-onglet="analyses">Voir tout →</button></div>
      <div class="liste-cartes">
        ${recos.length ? recos.map(({ m, code, libelle, proba: p, cote: c }) => `
          <article class="match-reco">
            <div>
              <div class="meta">${echapper(m.nomChampionnat)} · ${heureFr(m.coup_envoi)}</div>
              <div class="equipes">${echapper(m.domicile)} <span>–</span> ${echapper(m.exterieur)}</div>
              <div class="details"><b>${echapper(libelle)}</b> · Risque : ${risque(p).label} · <button class="lien" data-action="voir-detail" data-mid="${echapper(m.id)}">détail</button></div>
            </div>
            <div class="droite"><div class="proba">${pct(p, 0)}</div>
              ${boutonAjouter(m, code, libelle, c, { ajoute: dejaAuTicket(m, code) })}</div>
          </article>`).join("") : `<div class="vide">${icone("calendrier")}<h3>Aucun match pour ce jour</h3><p>Choisissez « Tous les matchs » pour voir l'ensemble des ${etat.matchs.length} rencontres.</p></div>`}
      </div>
    </div>

    <div>
      <div class="section carte carte-padding">
        <div class="mini-titre">${icone("eclair")} Valeurs détectées</div>
        ${valeurs.map((v) => {
          const m = matchDe(v.match_id);
          const code = CODE_DEPUIS_CLE[v.selection] || v.selection;
          return `<div class="value-ligne">
            <div><div class="value-ligue">${echapper(v.championnat)} · ${dateCourte(v.coup_envoi)}</div>
              <div class="value-match">${echapper(v.domicile)} – ${echapper(v.exterieur)}</div>
              <div class="value-sel">${echapper(v.libelle)} · ${pct(v.proba)} · cote ${cote(v.meilleure_cote)}</div></div>
            <div class="value-droite"><strong>+${pct(v.valeur_corrigee || v.valeur_brute)}</strong><small>${echapper(v.bookmaker || "")}</small>
              ${m ? boutonAjouter(m, code, v.libelle, v.meilleure_cote, { compact: true, ajoute: dejaAuTicket(m, code) }) : ""}</div>
          </div>`;
        }).join("") || `<p class="texte-mute">Aucune valeur positive détectée.</p>`}
        <p class="texte-mute" style="font-size:11px;margin-top:10px">Valeur corrigée selon le délai avant le coup d'envoi (CLV).</p>
      </div>

      <div class="section carte carte-padding">
        <div class="mini-titre">${icone("cible")} Le moteur est-il fiable ?</div>
        ${svgCalibration(cal, { w: 420, h: 210 })}
        <p class="texte-mute" style="font-size:11.5px">Les points suivent la diagonale : quand le moteur annonce 70 %, la fréquence observée est proche de 70 %. <button class="lien" data-action="onglet" data-onglet="stats">Voir les statistiques →</button></p>
      </div>
    </div>
  </div>`;
}

/* ----------------------------------------------------------------- ANALYSES - */
function matchsFiltres() {
  const q = etat.recherche.trim().toLocaleLowerCase("fr");
  return etat.matchs.filter((m) => {
    if (etat.filtreDate !== "toutes" && m.date !== etat.filtreDate) return false;
    if (etat.reglages.confiance) {
      const c = m.marches?.[m.selection_haute_confiance]?.confiance;
      if (!c?.haute_confiance) return false;
    }
    if (q && !`${m.domicile} ${m.exterieur} ${m.nomChampionnat} ${m.codeChampionnat}`.toLocaleLowerCase("fr").includes(q)) return false;
    return true;
  });
}

function carteMatch(m) {
  const reco = recoDe(m);
  const principal = m.pronostic_principal || "1";
  const marP = m.marches?.[principal] || {};
  const tuiles = MARCHES_RAPIDES.map((t) => {
    const p = probaBase(m, t.code);
    const mar = m.marches?.[t.cle] || {};
    const c = mar.meilleure_cote || mar.cote_juste || 1 / Math.max(p, 1e-6);
    const recommandee = reco.code === t.code;
    return `<button class="tuile ${recommandee ? "recommandee" : ""} ${dejaAuTicket(m, t.code) ? "choisie" : ""}"
      data-action="ajouter" data-mid="${echapper(m.id)}" data-code="${echapper(t.code)}"
      data-libelle="${echapper(mar.libelle || t.label)}" data-cote="${Number(c) || ""}"
      title="Ajouter ${echapper(mar.libelle || t.label)} (${pct(p)}) au ticket">${t.label}<b>${pct(p, 0)}</b></button>`;
  }).join("");
  const hc = m.marches?.[m.selection_haute_confiance]?.confiance;
  return `<article class="carte-match">
    <div class="match-ligne1"><span class="heure">${heureFr(m.coup_envoi)}</span>
      <span class="equipes-noms">${echapper(m.domicile)} <span>–</span> ${echapper(m.exterieur)}</span></div>
    <div class="match-ligne2">Pronostic : <b>${echapper(marP.libelle || reco.libelle)} · ${pct(marP.proba ?? reco.proba, 0)}</b> · score ${echapper(m.score_probable || "—")} · <button class="lien" data-action="voir-detail" data-mid="${echapper(m.id)}">détail du match</button></div>
    <div class="tuiles">${tuiles}</div>
    <div class="match-pied">
      ${hc?.haute_confiance ? `<span class="badge-hc">${icone("etoile")} ${echapper(reco.libelle)} · réel ${pct(hc.taux_historique, 0)} sur ${nombre(hc.n_historique)} matchs</span>` : `<span class="texte-mute" style="font-size:11.5px">${echapper(m.methode || "Marché + modèles")}</span>`}
      <button class="lien" data-action="voir-detail" data-mid="${echapper(m.id)}" data-tab="marches">Tous les paris (193) ›</button>
    </div>
  </article>`;
}

function vueAnalyses() {
  const sel = matchsFiltres();
  const groupes = new Map();
  for (const m of sel) {
    if (!groupes.has(m.codeChampionnat)) groupes.set(m.codeChampionnat, { nom: m.nomChampionnat, matchs: [] });
    groupes.get(m.codeChampionnat).matchs.push(m);
  }
  const puces = [`<button class="puce ${etat.filtreDate === "toutes" ? "active" : ""}" data-action="filtre-date" data-date="toutes">Toutes les dates</button>`]
    .concat(etat.dates.map((dt) => `<button class="puce ${etat.filtreDate === dt ? "active" : ""}" data-action="filtre-date" data-date="${dt}">${jourFr(dt + "T12:00:00Z")}</button>`)).join("");
  return `
  <div class="bandeau-demo" style="margin-bottom:14px">${icone("info")}${etat.serveurActif ? "Pronostics en direct depuis le serveur" : "Mode démonstration hors ligne (pronostics injoignables ? réglez le serveur dans « Profil »). Données d'exemple."}</div>
  <div class="outils">
    <div class="defilement-puces" style="flex:1 1 100%">${puces}</div>
    <label class="champ-recherche">${icone("recherche")}<input id="recherche-analyses" data-champ="recherche" type="search" placeholder="Filtrer une équipe ou un championnat" value="${echapper(etat.recherche)}" autocomplete="off"></label>
    <label class="interrupteur"><input type="checkbox" data-champ="confiance" ${etat.reglages.confiance ? "checked" : ""}> Mode haute confiance</label>
    <span class="texte-mute" style="font-size:12px">${sel.length} match${sel.length > 1 ? "s" : ""}</span>
  </div>
  <div>
    ${[...groupes.entries()].map(([code, g]) => `
      <section class="ligue ${etat.liguesOuvertes.has(code) ? "" : "fermee"}">
        <button class="ligue-tete" data-action="ligue" data-code="${echapper(code)}">
          ${icone("chevron")}<span>${echapper(g.nom)}</span><span class="compte">${g.matchs.length} match${g.matchs.length > 1 ? "s" : ""}</span>
        </button>
        <div class="ligue-corps">${g.matchs.sort((a, b) => a.coup_envoi.localeCompare(b.coup_envoi)).map(carteMatch).join("")}</div>
      </section>`).join("") || `<div class="vide carte">${icone("recherche")}<h3>Aucun match trouvé</h3><p>Modifiez la date, la recherche ou désactivez le mode haute confiance.</p><button class="bouton" data-action="recherche-effacer">Effacer les filtres</button></div>`}
  </div>`;
}

/* ------------------------------------------------------------------- DÉTAIL - */
const ONGLETS_DETAIL = [
  ["apercu", "Aperçu"], ["marches", "Tous les marchés"], ["moduler", "Moduler"],
  ["forme", "Forme"], ["scores", "Scores exacts"], ["h2h", "Face-à-face"],
];
const PARAMETRES_MODULATION = [
  { cle: "attaque_dom", titre: "Attaque domicile", aide: "Absence d'un buteur : baissez à 0,85", max: 2 },
  { cle: "attaque_ext", titre: "Attaque extérieur", aide: "Dynamique offensive de l'équipe en déplacement", max: 2 },
  { cle: "corners_dom", titre: "Corners domicile", aide: "Jeu de ailes, pression attendue", max: 2 },
  { cle: "corners_ext", titre: "Corners extérieur", aide: "Style de jeu de l'adversaire", max: 2 },
  { cle: "cartons", titre: "Cartons / arbitre", aide: "Arbitre sévère ou derby tendu : augmentez", max: 2.5 },
];

function enteteDetail(m) {
  return `<div class="carte detail-entete">
    <div class="detail-titre">
      <button class="bouton-retour" data-action="retour" aria-label="Retour">${icone("retour")}</button>
      <div><h2>${echapper(m.domicile)} – ${echapper(m.exterieur)}</h2>
        <div class="sous">${echapper(m.nomChampionnat)} · ${dateFr(m.coup_envoi)} à ${heureFr(m.coup_envoi)} UTC</div></div>
      <div style="margin-left:auto">${boutonAjouter(m, recoDe(m).code, recoDe(m).libelle, recoDe(m).cote)}</div>
    </div>
    <div class="detail-chiffres">
      <span>Buts attendus <b>${(m.buts_attendus?.[0] ?? 0).toFixed(2).replace(".", ",")} – ${(m.buts_attendus?.[1] ?? 0).toFixed(2).replace(".", ",")}</b></span>
      <span>Score probable <b>${echapper(m.score_probable || "—")}</b></span>
      <span>Corners <b>${(m.corners_attendus?.[0] ?? 0).toFixed(1).replace(".", ",")} – ${(m.corners_attendus?.[1] ?? 0).toFixed(1).replace(".", ",")}</b></span>
      <span>Cartons <b>${(m.cartons_attendus?.[0] ?? 0).toFixed(1).replace(".", ",")} – ${(m.cartons_attendus?.[1] ?? 0).toFixed(1).replace(".", ",")}</b></span>
      <span>Méthode <b>${echapper(m.methode || "Marché + modèles")}</b></span>
    </div>
  </div>`;
}

function apercuDetail(m) {
  const prob1 = probaAffichee(m, "1X2:1"), probN = probaAffichee(m, "1X2:N"), prob2 = probaAffichee(m, "1X2:2");
  const cles = ["1", "N", "2", "1N", "12", "N2", "plus_2.5", "btts_oui"];
  const lignes = cles.map((cle) => {
    const mar = m.marches?.[cle] || {};
    const code = CODE_DEPUIS_CLE[cle];
    const p = probaAffichee(m, code);
    const c = mar.meilleure_cote || mar.cote_juste || 1 / Math.max(p, 1e-6);
    const conf = mar.confiance;
    return `<div class="ligne-marche">
      <div><div class="nom">${echapper(mar.libelle || cle)}</div>
        <div class="sous-nom">${conf?.niveau ? `${echapper(conf.niveau)}${conf.taux_historique ? ` · réel ${pct(conf.taux_historique, 0)} sur ${nombre(conf.n_historique)} matchs` : ""}` : `cote juste ${cote(1 / Math.max(p, 1e-9))}`}</div></div>
      <div class="val">${pct(p)}</div>
      ${boutonAjouter(m, code, mar.libelle || cle, c, { compact: true, ajoute: dejaAuTicket(m, code) })}
    </div>`;
  }).join("");
  const sources = m.analyse?.sources || {};
  const src = [["Marché (ouverture)", sources.marche_ouv], ["Dixon-Coles", sources.dixon_coles],
    ["Elo", sources.elo], ["Combinaison finale", m.analyse?.final]].filter(([, v]) => Array.isArray(v));
  const matrice = jumeauAffiche(m).scores();
  const scores = [];
  for (let i = 0; i < matrice.length; i++) for (let j = 0; j < matrice.length; j++) scores.push({ i, j, p: matrice[i][j] });
  scores.sort((a, b) => b.p - a.p);
  return `<div class="deux-colonnes section">
    <div class="carte carte-padding">
      <div class="mini-titre">Probabilités des résultats</div>
      <div class="trois-colonnes">
        ${[[prob1, `Victoire ${m.domicile}`, "1X2:1"], [probN, "Match nul", "1X2:N"], [prob2, `Victoire ${m.exterieur}`, "1X2:2"]].map(([p, lib, code]) => `
          <div class="grande-proba"><div class="libelle">${echapper(lib)}</div>
            <div class="valeur ${p === Math.max(prob1, probN, prob2) ? "texte-vert" : ""}">${pct(p)}</div>
            <div class="barre-fond"><i style="width:${p * 100}%"></i></div>
            <div style="margin-top:10px">${boutonAjouter(m, code, lib, 1 / Math.max(probaBase(m, code), 1e-6), { compact: true, ajoute: dejaAuTicket(m, code) })}</div>
          </div>`).join("")}
      </div>
      <p class="texte-mute" style="font-size:11.5px;margin-top:14px">Touchez une option pour l'ajouter au ticket. Une seule sélection par match est autorisée par les bookmakers.</p>
    </div>
    <div class="carte carte-padding">
      <div class="mini-titre">Marchés clés</div>${lignes}
    </div>
  </div>
  <div class="deux-colonnes">
    <div class="carte carte-padding">
      <div class="mini-titre">D'où vient le pronostic ?</div>
      ${src.map(([nom, v]) => `<div class="sources-ligne">
        <div class="entete"><span>${echapper(nom)}</span><b>1 ${pct(v[0], 0)} · N ${pct(v[1], 0)} · 2 ${pct(v[2], 0)}</b></div>
        <div style="display:flex;gap:4px;height:7px">
          <div style="width:${v[0] * 100}%;background:var(--vert);border-radius:5px"></div>
          <div style="width:${v[1] * 100}%;background:var(--ambre);border-radius:5px"></div>
          <div style="width:${v[2] * 100}%;background:var(--rouge);border-radius:5px"></div>
        </div></div>`).join("") || `<p class="texte-mute">Sources non disponibles.</p>`}
      <p class="texte-mute" style="font-size:11px;margin-top:10px">Pool logarithmique dont les poids sont appris sur les saisons 1920 à 2223 et testés sur 2324 à 2627.</p>
    </div>
    <div class="carte carte-padding">
      <div class="mini-titre">Scores les plus probables</div>
      ${scores.slice(0, 7).map((s) => `<div class="ligne-marche">
        <div class="nom">Score exact <b>${s.i}-${s.j}</b></div>
        <div class="val">${pct(s.p)}</div>
        ${boutonAjouter(m, `CS:${s.i}-${s.j}`, `Score exact ${s.i}-${s.j}`, 1 / Math.max(probaBase(m, `CS:${s.i}-${s.j}`), 1e-6), { compact: true, ajoute: dejaAuTicket(m, `CS:${s.i}-${s.j}`) })}
      </div>`).join("")}
      <button class="lien" data-action="onglet-detail" data-tab="scores" style="margin-top:10px">Voir la matrice des scores →</button>
    </div>
  </div>`;
}

function tableauMarches(m, groupe, filtre = "") {
  const q = filtre.trim().toLocaleLowerCase("fr");
  const marches = etat.donnees.catalogue.filter((g) => (groupe === "TOUS" || g.groupe === groupe));
  return marches.map((g) => {
    const options = g.options.filter((o) => !q || `${o.libelle} ${o.code} ${g.titre}`.toLocaleLowerCase("fr").includes(q));
    if (!options.length) return "";
    return `<div class="groupe-marches"><div class="groupe-tete"><span>${echapper(g.titre)}</span><small>${options.length} options · ${echapper(g.groupe)}</small></div>
      <div class="tableau-scroll"><table class="tableau-marches"><thead><tr>
        <th>Sélection</th><th class="num">Probabilité</th><th class="num">Cote juste</th><th class="num">Réel (tranche)</th><th></th>
      </tr></thead><tbody>
      ${options.map((o) => {
        let p;
        try { p = probaAffichee(m, o.code); } catch { p = 0; }
        const reel = reelMesure(g.groupe, p);
        const c = 1 / Math.max(probaBase(m, o.code), 1e-9);
        return `<tr><td>${echapper(o.libelle)}<div class="sous-nom" style="font-size:10px;color:var(--mute-2)">${echapper(o.code)}</div></td>
          <td class="num p-verte">${pct(p)}</td><td class="num">${cote(c)}</td>
          <td class="num p-mute">${reel ? pct(reel.reel, 0) : "—"}</td>
          <td class="num">${boutonAjouter(m, o.code, `${g.titre} · ${o.libelle}`, c, { compact: true, ajoute: dejaAuTicket(m, o.code) })}</td></tr>`;
      }).join("")}
      </tbody></table></div></div>`;
  }).join("");
}

function marchesDetail(m) {
  const groupes = [...new Set(etat.donnees.catalogue.map((g) => g.groupe))];
  const total = etat.donnees.catalogue.reduce((a, g) => a + g.options.length, 0);
  return `<div class="section">
    <div class="carte carte-padding" style="margin-bottom:14px">
      <div class="mini-titre">${icone("cible")} Catalogue · ${total} sélections sur un seul jumeau numérique</div>
      <p class="texte-mute" style="font-size:12px">Toutes les probabilités sont calculées dans votre navigateur, avec les corrélations exactes entre marchés. Les cotes justes sont préremplies dans le ticket : remplacez-les par celles de votre bookmaker. « Réel (tranche) » est la fréquence observée pour la tranche de probabilité correspondante sur les saisons de test. Le ticket utilise le modèle de référence (sans modulation).</p>
    </div>
    <div class="outils">
      <div class="defilement-puces" style="flex:1 1 100%">
        <button class="puce ${etat.groupeActif === "TOUS" ? "active" : ""}" data-action="groupe" data-groupe="TOUS">Tous</button>
        ${groupes.map((g) => `<button class="puce ${etat.groupeActif === g ? "active" : ""}" data-action="groupe" data-groupe="${echapper(g)}">${echapper(g)}</button>`).join("")}
      </div>
      <label class="champ-recherche">${icone("recherche")}<input id="recherche-marches" data-champ="recherche-marches" type="search" placeholder="Filtrer un marché…" value="${echapper(etat.rechercheMarches)}"></label>
    </div>
    <div id="liste-marches">${tableauMarches(m, etat.rechercheMarches ? "TOUS" : etat.groupeActif, etat.rechercheMarches)}</div>
  </div>`;
}

function resultatsModulation(m) {
  const lignes = [
    ["Victoire domicile", "1X2:1"], ["Match nul", "1X2:N"], ["Victoire extérieur", "1X2:2"],
    ["Double chance 1N", "DC:1N"], ["Plus de 2,5 buts", "OU:2.5:plus"],
    ["Les deux marquent", "BTTS:oui"], ["1X2 1re mi-temps : 1", "1X2@MT1:1"],
    ["Plus de 9,5 corners", "CORNERS_OU:9.5:plus"], ["Plus de 3,5 cartons", "CARTONS_OU:3.5:plus"],
  ];
  return `<div class="carte carte-padding"><div class="mini-titre">Probabilités recalculées instantanément</div>
    ${lignes.map(([lib, code]) => {
      const p0 = probaBase(m, code), p1 = probaAffichee(m, code);
      const delta = p1 - p0;
      return `<div class="ligne-marche"><div class="nom">${echapper(lib)}</div>
        <div class="val">${pct(p1)} <span class="delta ${delta >= 0 ? "hausse" : "baisse"}">${delta >= 0 ? "+" : ""}${pct(delta)}</span></div>
        ${boutonAjouter(m, code, lib, 1 / Math.max(p0, 1e-6), { compact: true, ajoute: dejaAuTicket(m, code) })}</div>`;
    }).join("")}
  </div>`;
}

function modulerDetail(m) {
  return `<div class="section">
    <div class="carte carte-padding" style="margin-bottom:14px">
      <div class="mini-titre">${icone("reglages")} Intégrez une information que le marché ignore</div>
      <p class="texte-mute" style="font-size:12px">Absence, arbitre, météo, forme… Le jumeau décale la loi des buts par basculement exponentiel exact (λ → λ × f) et ajuste corners et cartons. Toutes les probabilités se recalculent sans recharger la page. Le ticket conserve les probabilités de référence.</p>
    </div>
    <div class="deux-colonnes">
      <div class="carte carte-padding"><div class="sliders">
        ${PARAMETRES_MODULATION.map((p) => `<div class="slider">
          <div class="entete"><span>${echapper(p.titre)}</span><b id="val-${p.cle}">×${etat.modulation[p.cle].toFixed(2).replace(".", ",")}</b></div>
          <input type="range" min="0.3" max="${p.max}" step="0.01" value="${etat.modulation[p.cle]}" data-champ="modulation" data-param="${p.cle}" aria-label="${echapper(p.titre)}">
          <div class="aide">${echapper(p.aide)}</div></div>`).join("")}
        <div style="grid-column:1/-1;display:flex;gap:10px;align-items:center;margin-top:4px">
          <button class="bouton" data-action="reset-modulation">${icone("actualiser")} Réinitialiser</button>
          <span class="texte-mute" style="font-size:11.5px">Les valeurs ×1,00 correspondent au modèle publié.</span>
        </div>
      </div></div>
      <div id="mod-resultats">${resultatsModulation(m)}</div>
    </div>
    <div class="alerte info" style="margin-top:16px">${icone("info")}<span>Ouvrez l'onglet « Tous les marchés » après une modulation : les 193 probabilités affichées tiennent compte de vos réglages.</span></div>
  </div>`;
}

function formeEquipe(m, coteEquipe) {
  const a = m.analyse || {};
  const forme = coteEquipe === "dom" ? a.forme_dom : a.forme_ext;
  const stats = coteEquipe === "dom" ? a.stats_dom : a.stats_ext;
  const nom = coteEquipe === "dom" ? m.domicile : m.exterieur;
  return `<div class="carte forme-equipe"><h3>${echapper(nom)}</h3>
    <div class="mini-titre" style="margin-bottom:9px">5 derniers matchs</div>
    <div class="forme-liste">${(forme || []).map((f) => `<div class="forme-match">
      <span class="resultat ${echapper(f.res)}">${echapper(f.res)}</span>
      <span>${dateCourte(f.date + "T12:00:00Z")}</span>
      <span>${f.lieu === "dom" ? "vs" : "@"} ${echapper(f.adversaire)}</span>
      <span class="score">${echapper(f.score)}</span></div>`).join("") || `<span class="texte-mute">Historique indisponible.</span>`}</div>
    ${stats ? `<div class="stats-grid">
      <div><strong>${(stats.buts_marques ?? 0).toFixed(1).replace(".", ",")}</strong><small>Buts marqués / match</small></div>
      <div><strong>${(stats.buts_encaisses ?? 0).toFixed(1).replace(".", ",")}</strong><small>Buts encaissés / match</small></div>
      <div><strong>${pct(stats.plus_2_5, 0)}</strong><small>Plus de 2,5 buts</small></div>
      <div><strong>${pct(stats.btts, 0)}</strong><small>Les deux marquent</small></div>
      <div><strong>${pct(stats.clean_sheets, 0)}</strong><small>Cage inviolée</small></div>
      <div><strong>${stats.lieu ? `${stats.lieu.v}V ${stats.lieu.n}N ${stats.lieu.d}D` : "—"}</strong><small>${echapper(stats.lieu?.type || "Bilan")}</small></div>
    </div>` : ""}
  </div>`;
}

function formeDetail(m) {
  return `<div class="deux-colonnes section">${formeEquipe(m, "dom")}${formeEquipe(m, "ext")}</div>
  <div class="alerte info">${icone("info")}<span>La forme et les statistiques sont descriptives : seules les cotes et les modèles calibrés entrent dans la probabilité finale. Un historique de 5 matchs ne permet pas, à lui seul, de battre le marché.</span></div>`;
}

function scoresDetail(m) {
  const M = jumeauAffiche(m).scores(), n = M.length;
  const max = Math.max(...M.flat());
  let grid = `<div class="heatmap" style="grid-template-columns:repeat(${n + 1},1fr)"><div class="axe"></div>`;
  for (let j = 0; j < n; j++) grid += `<div class="axe">${j}</div>`;
  for (let i = 0; i < n; i++) {
    grid += `<div class="axe">${i}</div>`;
    for (let j = 0; j < n; j++) {
      const p = M[i][j], alpha = .08 + .82 * (p / max);
      grid += `<div class="cellule" style="background:rgba(44,224,131,${alpha.toFixed(3)})" title="${i}-${j} : ${pct(p, 2)}">${p >= .01 ? pct(p, 0).replace(" %", "") : ""}</div>`;
    }
  }
  grid += "</div>";
  const scores = [];
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) scores.push({ i, j, p: M[i][j] });
  scores.sort((a, b) => b.p - a.p);
  return `<div class="deux-colonnes section">
    <div class="carte carte-padding"><div class="mini-titre">Matrice des scores (lignes : domicile)</div>${grid}
      <p class="texte-mute" style="font-size:11px;margin-top:12px">Loi jointe calibrée du moteur. La matrice sert de base à tous les marchés de buts et de mi-temps.</p></div>
    <div class="carte carte-padding"><div class="mini-titre">Scores exacts</div>
      ${scores.slice(0, 12).map((s) => `<div class="ligne-marche"><div class="nom">${s.i} – ${s.j}</div>
        <div class="val">${pct(s.p, 2)}</div>
        ${boutonAjouter(m, `CS:${s.i}-${s.j}`, `Score exact ${s.i}-${s.j}`, 1 / Math.max(probaBase(m, `CS:${s.i}-${s.j}`), 1e-6), { compact: true, ajoute: dejaAuTicket(m, `CS:${s.i}-${s.j}`) })}</div>`).join("")}
    </div></div>`;
}

function h2hDetail(m) {
  const h = m.analyse?.confrontations || [];
  return `<div class="carte carte-padding section">
    <div class="mini-titre">Confrontations directes</div>
    ${h.length ? h.map((c) => `<div class="ligne-marche"><div class="nom">${echapper(c.date || "")} · ${echapper(c.domicile || m.domicile)} – ${echapper(c.exterieur || m.exterieur)}</div><div class="val">${echapper(c.score || "")}</div></div>`).join("")
      : `<div class="vide">${icone("info")}<h3>Pas d'historique exploitable</h3><p>Ces deux équipes ne se sont pas rencontrées récemment dans les données disponibles. Le moteur ne surpondère pas un face-à-face de quelques matchs.</p></div>`}
  </div>`;
}

function vueDetail() {
  const m = matchDe(etat.detail?.matchId);
  if (!m) { etat.onglet = "analyses"; return vueAnalyses(); }
  const tab = etat.detail.tab;
  const corps = {
    apercu: () => apercuDetail(m), marches: () => marchesDetail(m),
    moduler: () => modulerDetail(m), forme: () => formeDetail(m),
    scores: () => scoresDetail(m), h2h: () => h2hDetail(m),
  }[tab] || (() => apercuDetail(m));
  return `${enteteDetail(m)}
    <div class="onglets">${ONGLETS_DETAIL.map(([id, lib]) => `<button class="onglet ${tab === id ? "active" : ""}" data-action="onglet-detail" data-tab="${id}">${lib}</button>`).join("")}</div>
    ${corps()}`;
}

/* ------------------------------------------------------------------- TICKET - */
function candidatsGenerateur() {
  const familles = {
    "1X2": ["1X2:1", "1X2:N", "1X2:2"],
    DC: ["DC:1N", "DC:12", "DC:N2"],
    OU: ["OU:1.5:plus", "OU:2.5:plus", "OU:2.5:moins"],
    BTTS: ["BTTS:oui", "BTTS:non"],
  };
  const libelles = {
    "1X2:1": "1", "1X2:N": "N", "1X2:2": "2", "DC:1N": "Double chance 1N",
    "DC:12": "Double chance 12", "DC:N2": "Double chance N2",
    "OU:1.5:plus": "Plus de 1,5 but", "OU:2.5:plus": "Plus de 2,5 buts",
    "OU:2.5:moins": "Moins de 2,5 buts", "BTTS:oui": "Les deux marquent : oui",
    "BTTS:non": "Les deux marquent : non",
  };
  const out = [];
  for (const m of etat.matchs) {
    for (const [fam, codes] of Object.entries(familles)) {
      if (!etat.generateur.types[fam]) continue;
      for (const code of codes) {
        const p = probaBase(m, code);
        const cle = Object.keys(CODE_DEPUIS_CLE).find((k) => CODE_DEPUIS_CLE[k] === code);
        const mar = cle ? m.marches?.[cle] : null;
        const c = mar?.meilleure_cote || mar?.cote_juste || 1 / Math.max(p, 1e-6);
        if (c < etat.generateur.coteMin) continue;
        out.push({ m, code, libelle: libelles[code] || code, proba: p, cote: c });
      }
    }
  }
  return out.sort((a, b) => b.proba - a.proba);
}

function genererTicket() {
  const cites = candidatsGenerateur();
  const pris = new Set(), choix = [];
  for (const c of cites) {
    if (choix.length >= etat.generateur.nb) break;
    if (pris.has(c.m.id)) continue;
    pris.add(c.m.id);
    choix.push(c);
  }
  if (!choix.length) { toast("Aucune sélection ne respecte ces critères", "erreur"); return; }
  etat.ticket = choix.map((c) => ({
    matchId: c.m.id, code: c.code, libelle: c.libelle, cote: c.cote, proba: c.proba,
    equipes: `${c.m.domicile} – ${c.m.exterieur}`, ligue: c.m.nomChampionnat, date: c.m.coup_envoi,
  }));
  sauvegarder();
  const r = calculerTicket();
  toast(`Combiné de ${choix.length} sélections généré`);
  rendre(true);
  const resultat = document.getElementById("resultat-generateur");
  if (resultat) resultat.innerHTML = `Combiné généré : ${choix.length} sélection${choix.length > 1 ? "s" : ""},
    réussite <b>${pct(r.proba)}</b>, cote <b>${cote(r.coteTotale)}</b>, risque ${r.risque.label}.`;
}

function vueTicket() {
  const r = calculerTicket();
  if (!r) return `<div class="vide carte">${icone("ticket")}<h3>Votre ticket est vide</h3>
    <p>Ajoutez une sélection depuis les analyses ou le détail d'un match. Chaque probabilité est calculée par le jumeau numérique ; les sélections d'un même match sont combinées exactement.</p>
    <button class="bouton bouton-plein" data-action="onglet" data-onglet="analyses">${icone("analyses")} Explorer les matchs</button></div>`;
  return `<div class="ticket-colonnes">
    <div>
      <div class="carte resume-ticket">
        <div class="resume-entete">
          <div><h2>Chances de réussite</h2><p>${etat.ticket.length} sélection${etat.ticket.length > 1 ? "s" : ""} · <span id="r-risque"><span class="etiquette ${COULEUR_RISQUE[r.risque.couleur]}">${r.risque.label}</span></span></p></div>
          <div class="gros ${r.proba >= .5 ? "texte-vert" : "texte-rouge"}" id="r-proba">${pct(r.proba)}</div>
        </div>
        <div class="barre-fond ${r.proba < .3 ? "rouge" : ""}" style="height:8px;margin-top:14px"><i id="r-barre" style="width:${Math.min(100, r.proba * 100)}%"></i></div>
        <p class="texte-mute" style="font-size:12px;margin-top:9px" id="r-cent">Sur 100 tickets identiques, environ <b>${nombre(r.proba * 100)}</b> seraient gagnants.</p>
        <div class="grille-chiffres">
          <div class="chiffre"><span>Cote totale du ticket</span><b id="r-cote">${cote(r.coteTotale)}</b></div>
          <div class="chiffre"><span>Cote juste (équitable)</span><b id="r-juste">${cote(r.cote_juste)}</b></div>
          <div class="chiffre"><span>Mise</span><label class="champ-mise"><input id="champ-mise" data-champ="mise" type="number" min="0" step="100" value="${etat.mise}"><small>${echapper(devise())}</small></label></div>
          <div class="chiffre"><span>Gain potentiel (si gagné)</span><b id="r-gain"><span class="texte-vert">${montant(r.gain)}</span></b></div>
          <div class="chiffre"><span>Gain moyen attendu</span><b id="r-esperance"><span class="${r.esperance >= 0 ? "texte-vert" : "texte-rouge"}">${montant(r.esperance)}</span></b></div>
          <div class="chiffre"><span>Valeur du ticket</span><b id="r-valeur"><span class="${r.valeur >= 0 ? "texte-vert" : "texte-rouge"}">${pct(r.valeur)}</span></b></div>
        </div>
        ${r.valeur < 0 ? `<div class="alerte negative">${icone("avertissement")}<span><b>Valeur négative</b> : à long terme, ce type de ticket fait perdre de l'argent. La cote proposée est inférieure à la cote juste estimée par le moteur.</span></div>`
          : `<div class="alerte positive">${icone("verifie")}<span><b>Valeur positive</b> : la cote proposée dépasse la cote juste estimée. Cela reste une probabilité, pas une certitude.</span></div>`}
        <div class="alerte info">${icone("info")}<span>Sur un même match, les sélections sont combinées avec leurs corrélations exactes ; d'un match à l'autre, les probabilités se multiplient. Une seule sélection par match est autorisée (règle des bookmakers).</span></div>
      </div>

      <div class="titre-section"><h2>Sélections (${etat.ticket.length})</h2>
        <div style="display:flex;gap:8px">
          <button class="bouton bouton-petit" data-action="enregistrer-ticket">${icone("verifie")} Enregistrer</button>
          <button class="bouton bouton-petit bouton-danger" data-action="vider-ticket">${icone("poubelle")} Vider</button>
        </div></div>
      <p class="texte-mute" style="font-size:11.5px;margin-bottom:12px">Cotes préremplies avec la meilleure cote du marché quand elle est connue, sinon la cote juste : remplacez-les par celles de votre bookmaker.</p>
      ${etat.ticket.map((s, i) => `<div class="selection-ticket">
        <div><div class="ligue">${echapper(s.ligue)} · ${dateCourte(s.date)} ${heureFr(s.date)}</div>
          <div class="equipes">${echapper(s.equipes)}</div>
          <div class="choix">${echapper(s.libelle)}</div>
          <div class="proba-seule">Probabilité seule : ${pct(s.proba)} · cote juste ${cote(1 / Math.max(s.proba, 1e-9))}</div></div>
        <div class="selection-actions">
          <label style="text-align:center"><small class="texte-mute" style="display:block;font-size:10px">Cote</small>
            <input class="cote-input" type="number" min="1.01" step="0.01" value="${Number(s.cote).toFixed(2)}" data-champ="cote" data-index="${i}" aria-label="Cote de la sélection"></label>
          <button class="bouton-retirer" data-action="retirer" data-index="${i}" aria-label="Retirer">${icone("croix")}</button>
        </div></div>`).join("")}
    </div>

    <div>
      <div class="carte generateur">
        <div class="mini-titre">${icone("eclair")} Assistant de combiné</div>
        <p class="texte-mute" style="font-size:11.5px">Construit le combiné le plus probable selon vos contraintes, en respectant la règle « une sélection par match ».</p>
        <div class="champs-generateur">
          <div class="champ-ligne"><span>Nombre de matchs</span><input type="number" min="1" max="10" value="${etat.generateur.nb}" data-champ="gen-nb"></div>
          <div class="champ-ligne"><span>Cote minimale par sélection</span><input type="number" min="1.01" max="10" step="0.05" value="${etat.generateur.coteMin}" data-champ="gen-cote"></div>
          <div><div style="font-size:11.5px;margin-bottom:7px">Types de paris autorisés</div><div class="checks">
            ${Object.entries(etat.generateur.types).map(([k, v]) => `<label class="check"><input type="checkbox" data-champ="gen-type" data-type="${k}" ${v ? "checked" : ""}>${k}</label>`).join("")}
          </div></div>
        </div>
        <button class="bouton bouton-plein bouton-large" data-action="generer-ticket">${icone("eclair")} Générer le combiné</button>
        <div class="resultat-generateur" id="resultat-generateur">Le combiné remplacera le ticket actuel.</div>
      </div>
      <div class="carte carte-padding" style="margin-top:16px">
        <div class="mini-titre">${icone("bouclier")} Mise recommandée (Kelly)</div>
        <p class="texte-mute" style="font-size:11.5px">Le moteur applique un Kelly fractionnaire plafonné à la valeur attendue corrigée du délai avant le coup d'envoi. Sur un ticket à valeur négative, la mise recommandée est <b>nulle</b>.</p>
        <div class="chiffre" style="margin-top:10px"><span>Valeur attendue</span><b class="${r.valeur >= 0 ? "texte-vert" : "texte-rouge"}">${pct(r.valeur)}</b></div>
        <div class="chiffre"><span>Mise conseillée</span><b>${r.valeur > 0 ? `${pct(Math.min(.02, r.valeur / Math.max(r.coteTotale - 1, 1)), 2)} de la bankroll` : "0 %"}</b></div>
      </div>
    </div>
  </div>`;
}

/* -------------------------------------------------------------------- STATS - */
function vueStats() {
  const d = etat.donnees, st = d.stats_moteur || {}, cal = d.calibration?.["1X2"] || [];
  const pointsCal = cal.map((p) => ({ x: p.proba_moyenne, y: p.taux_reel, n: p.n }));
  const familles = Object.keys(d.fiabilite || {});
  const fam = d.fiabilite?.[etat.familleFiabilite] || st.combines || [];
  const parType = (st.par_type || []).map((t) => ({ label: t.type, annonce: t.annonce, reel: t.reussite, n: t.n }));
  const parNiveau = (st.par_niveau || []).map((t) => ({ label: t.niveau, annonce: t.annonce, reel: t.reussite, n: t.n }));
  const parChamp = (st.par_championnat || []).map((t) => ({ label: t.championnat, annonce: .53, reel: t.reussite_1x2, n: t.n }));
  const combines = (st.combines || []).map((t) => ({ label: `${pct(t.de, 0)} – ${pct(t.a, 0)}`, annonce: t.annonce, reel: t.reel, n: t.n }));
  const modele = d.modele || {};
  return `
  <div class="carte stats-hero">
    <h2>Performance du moteur</h2>
    <p>Mesurée sur ${echapper(st.periode || "saisons jamais vues par le moteur")} · ${nombre(st.matchs || 0)} matchs · aucune fuite d'information.</p>
    <div class="kpi-large"><strong>${pct(st.reussite_globale, 1)}</strong><span>de réussite globale</span></div>
    <div class="barre-fond" style="height:9px"><i style="width:${(st.reussite_globale || 0) * 100}%"></i></div>
    <div class="trio">
      <div><strong>${nombre(st.pronostics_evalues)}</strong><small>évalués</small></div>
      <div><strong>${nombre(st.reussis)}</strong><small>corrects</small></div>
      <div><strong>${nombre((st.pronostics_evalues || 0) - (st.reussis || 0))}</strong><small>incorrects</small></div>
    </div>
    <p class="texte-mute" style="font-size:12.5px;margin-top:14px">Probabilité annoncée en moyenne : <b>${pct(st.annonce_moyenne)}</b> → réussite réelle : <b class="texte-vert">${pct(st.reussite_globale)}</b>. Quand les deux sont proches, les pourcentages de l'application sont fiables.</p>
  </div>

  <div class="deux-colonnes section">
    <div class="carte graphique"><h3>Réussite par type de pari</h3>${barresComparees(parType)}</div>
    <div class="carte graphique"><h3>Réussite par niveau de confiance</h3>${barresComparees(parNiveau)}</div>
  </div>

  <div class="deux-colonnes section">
    <div class="carte graphique">
      <h3>Calibration 1X2 · annonce contre réalité</h3>
      ${svgCalibration(pointsCal)}
      <p class="texte-mute" style="font-size:11.5px">Chaque point est un groupe de probabilités ; la taille reflète le nombre de matchs. La diagonale ambre = calibration parfaite.</p>
    </div>
    <div class="carte graphique">
      <h3>Fiabilité par famille de marchés</h3>
      <select data-champ="famille" style="margin-bottom:14px;padding:8px 10px;border-radius:9px;border:1px solid var(--bord-fort);background:rgba(0,0,0,.25);width:100%">
        ${familles.map((f) => `<option value="${f}" ${f === etat.familleFiabilite ? "selected" : ""}>${NOMS_FAMILLES[f] || f}</option>`).join("")}
      </select>
      <div id="fiabilite-chart">${barresComparees(fam.map((b) => ({ label: `${pct(b.de, 0)} – ${pct(b.a, 0)}`, annonce: b.annonce, reel: b.reel, n: b.n })), "annoncé → observé sur saisons de test")}</div>
    </div>
  </div>

  <div class="deux-colonnes section">
    <div class="carte graphique"><h3>Combinés multi-matchs</h3>${barresComparees(combines, "probabilité annoncée → fréquence réelle")}
      <p class="texte-mute" style="font-size:11.5px">Validation sur 20 000 combinés : le jumeau reproduit la fréquence réelle, y compris pour les tickets très peu probables.</p></div>
    <div class="carte graphique"><h3>Réussite 1X2 par championnat</h3>${barresComparees(parChamp, "référence 53 % (moyenne du marché) → mesuré")}</div>
  </div>

  <div class="deux-colonnes">
    <div class="carte carte-padding"><div class="mini-titre">Paramètres appris</div>
      <div class="param-liste">
        ${(modele.pool?.sources || []).map((s, i) => `<div><span>Poids · ${echapper(s)}</span><b>${(modele.pool?.poids?.[i] ?? 0).toFixed(3).replace(".", ",")}</b></div>`).join("")}
        <div><span>Dixon-Coles ξ</span><b>${(modele.dixon_coles_xi ?? 0).toFixed(4).replace(".", ",")}</b></div>
        <div><span>Elo · K</span><b>${modele.elo?.k ?? "—"}</b></div>
        <div><span>Elo · avantage domicile</span><b>${modele.elo?.avantage_domicile ?? "—"}</b></div>
        <div><span>Saisons d'entraînement</span><b>${(modele.entrainement || []).join(" · ")}</b></div>
        <div><span>Saisons de test</span><b>${(modele.test || []).join(" · ")}</b></div>
      </div>
    </div>
    <div class="carte carte-padding"><div class="mini-titre">Méthode</div>
      <div class="conseil">${icone("verifie")}<span><b>Marché d'abord.</b> Les cotes, une fois la marge retirée (puissance, Shin, proportionnelle, odds ratio), sont la meilleure estimation disponible.</span></div>
      <div class="conseil">${icone("verifie")}<span><b>Notation par le CLV.</b> Un pronostiqueur est jugé sur la valeur obtenue contre la cote de clôture, jamais sur son profit ou ses séries.</span></div>
      <div class="conseil">${icone("verifie")}<span><b>Pool logarithmique.</b> Les poids sont appris sur des saisons passées et testés sur des saisons jamais vues ; une source inutile reçoit un poids nul.</span></div>
      <div class="conseil">${icone("verifie")}<span><b>Jumeau numérique.</b> Loi jointe mi-temps / score final, corners et cartons ; toute sélection ou combinaison est calculée dans la même loi.</span></div>
    </div>
  </div>`;
}

/* ------------------------------------------------------------------- PROFIL - */
const ONGLETS_PROFIL = [["reglages", "Réglages"], ["experts", "Experts"], ["conseils", "Conseils"], ["historique", "Historique"]];

function expertsProfil() {
  const tous = new Map();
  for (const m of etat.matchs) for (const p of (m.pronostiqueurs || [])) {
    const nom = p.pronostiqueur || p.nom || "Expert";
    tous.set(nom, { nom, ...p });
  }
  const liste = [...tous.values()];
  return `<div class="carte carte-padding section">
    <div class="mini-titre">Classement des pronostiqueurs (CLV)</div>
    <p class="texte-mute" style="font-size:12.5px;margin-bottom:14px">Un expert n'influence les probabilités qu'après <b>50 pronostics</b> et un t-score de CLV ≥ 2. La note mesure l'écart entre la cote prise et la cote de clôture, jamais le résultat du match.</p>
    ${liste.length ? `<table class="tableau-simple"><thead><tr><th>Expert</th><th>Pronostics</th><th>CLV moyen</th><th>t-score</th></tr></thead><tbody>
      ${liste.map((p) => `<tr><td>${echapper(p.nom)}</td><td>${nombre(p.n || p.nb || 0)}</td><td>${pct(p.clv || 0, 2)}</td><td>${(p.t_score ?? 0).toFixed(2).replace(".", ",")}</td></tr>`).join("")}
    </tbody></table>` : `<div class="vide">${icone("profil")}<h3>Aucun expert qualifié</h3><p>Les pronostics d'experts sont enregistrés avant le coup d'envoi et vérifiés après le match. Aucun n'atteint encore le seuil de 50 pronostics dans ce jeu de données.</p><button class="bouton" data-action="onglet" data-onglet="stats">Voir la méthode →</button></div>`}
  </div>`;
}

function reglagesProfil() {
  return `<div class="carte carte-padding section">
    <div class="mini-titre">${icone("reglages")} Préférences</div>
    <div class="form-ligne"><div><div class="libelle">Adresse du serveur de pronostics</div>
        <div class="aide">Laissez vide pour les données locales. « /api » relaie l'API FastAPI du dépôt (uvicorn sur le port 8000) ; une URL externe nécessite CORS.</div></div>
      <input type="text" data-champ="serveur" value="${echapper(etat.reglages.serveur)}" placeholder="/api" style="min-width:210px"></div>
    <div class="form-ligne"><div><div class="libelle">Connexion au serveur</div><div class="aide">Teste la disponibilité puis remplace les matchs par les pronostics en direct.</div></div>
      <div style="display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end">
        <button class="bouton bouton-petit" data-action="tester-serveur">${icone("lien")} Tester</button>
        <button class="bouton bouton-petit" data-action="utiliser-serveur">Utiliser</button>
        <button class="bouton bouton-petit bouton-danger" data-action="serveur-local">Local</button>
      </div></div>
    <div class="form-ligne"><div><div class="libelle">Mode haute confiance</div><div class="aide">Ne montre que les sélections dont le taux de réussite historique a été validé.</div></div>
      <label class="interrupteur"><input type="checkbox" data-champ="confiance" ${etat.reglages.confiance ? "checked" : ""}> Activé</label></div>
    <div class="form-ligne"><div><div class="libelle">Mise par défaut</div><div class="aide">Utilisée dans le ticket et pour les tickets enregistrés.</div></div>
      <input type="number" min="0" step="100" data-champ="mise-defaut" value="${etat.mise}"></div>
    <div class="form-ligne"><div><div class="libelle">Devise affichée</div><div class="aide">Unité de mise et de gain. Aucune conversion n'est effectuée.</div></div>
      <select data-champ="devise">
        ${[["XAF", "FCFA (XAF)"], ["EUR", "Euro (€)"], ["USD", "Dollar ($)"], ["AUCUNE", "Sans unité"]].map(([v, l]) => `<option value="${v}" ${etat.reglages.devise === v ? "selected" : ""}>${l}</option>`).join("")}
      </select></div>
    <div class="form-ligne"><div><div class="libelle">Données locales</div><div class="aide">Ticket, réglages et historique sont conservés dans ce navigateur uniquement.</div></div>
      <button class="bouton bouton-petit bouton-danger" data-action="effacer-donnees">${icone("poubelle")} Tout effacer</button></div>
  </div>
  <div class="alerte info">${icone("info")}<span>${echapper(etat.donnees.avertissement || "Probabilités statistiques, pas des certitudes.")}</span></div>`;
}

function conseilsProfil() {
  return `<div class="carte carte-padding section">
    <div class="mini-titre">${icone("bouclier")} Jouer avec modération</div>
    <div class="conseil">${icone("avertissement")}<span><b>Aucun modèle ne garantit de gain.</b> L'application présente des probabilités, jamais des « pronos sûrs ». Un événement à 90 % échoue encore une fois sur dix.</span></div>
    <div class="conseil">${icone("avertissement")}<span><b>La valeur attendue est souvent négative.</b> La marge du bookmaker est intégrée aux cotes ; un combiné multiplie cette marge autant de fois qu'il contient de sélections.</span></div>
    <div class="conseil">${icone("bouclier")}<span><b>Fixez une bankroll dédiée</b> et ne misez qu'une fraction (Kelly fractionnaire plafonné). Ne poursuivez jamais une perte.</span></div>
    <div class="conseil">${icone("info")}<span><b>Jouer comporte des risques</b> : endettement, dépendance. Interdit aux mineurs. Aide : Joueurs Info Service <b>09 74 75 13 13</b>.</span></div>
    <div class="conseil">${icone("verifie")}<span><b>Comprendre les chiffres.</b> « Réussite mesurée » est une fréquence observée sur des saisons jamais vues par le moteur, pas une promesse pour les prochains matchs.</span></div>
  </div>`;
}

function historiqueProfil() {
  return `<div class="section">
    <div class="titre-section"><h2>Historique des tickets</h2><span class="note">${etat.historique.length} ticket${etat.historique.length > 1 ? "s" : ""}</span></div>
    ${etat.historique.length ? etat.historique.map((t, i) => `<div class="ticket-historique">
      <div class="tete"><div><span class="etiquette ambre">${echapper(t.statut || "En attente")}</span>
        <span class="date" style="margin-left:9px">${echapper(t.date)} · ${t.selections.length} sélection${t.selections.length > 1 ? "s" : ""}</span></div>
        <button class="bouton-retirer" data-action="supprimer-historique" data-index="${i}" aria-label="Supprimer">${icone("poubelle")}</button></div>
      <div class="resume">Chances annoncées <b class="texte-vert">${pct(t.proba)}</b> · cote ${cote(t.coteTotale)} · mise ${montant(t.mise)} → <b>${montant(t.gain)}</b></div>
      <ul>${t.selections.map((s) => `<li>${echapper(s.equipes)} : ${echapper(s.libelle)}</li>`).join("")}</ul>
    </div>`).join("") : `<div class="vide carte">${icone("ticket")}<h3>Aucun ticket enregistré</h3><p>Depuis l'onglet Ticket, cliquez sur « Enregistrer » : le ticket sera conservé ici et pourra être vérifié après les matchs.</p><button class="bouton" data-action="onglet" data-onglet="ticket">Ouvrir le ticket →</button></div>`}
  </div>`;
}

function vueProfil() {
  const corps = { reglages: reglagesProfil, experts: expertsProfil, conseils: conseilsProfil, historique: historiqueProfil };
  return `<div class="titre-section"><h2>Mon profil</h2><span class="note">Préférences et suivi, stockés localement</span></div>
    <div class="onglets">${ONGLETS_PROFIL.map(([id, lib]) => `<button class="onglet ${etat.profilTab === id ? "active" : ""}" data-action="profil-onglet" data-tab="${id}">${lib}</button>`).join("")}</div>
    ${(corps[etat.profilTab] || reglagesProfil)()}`;
}

/* --------------------------------------------------------------- rendu ------ */
const VUES = { accueil: vueAccueil, analyses: vueAnalyses, ticket: vueTicket, stats: vueStats, profil: vueProfil, detail: vueDetail };
const TITRES = {
  accueil: ["Tableau de bord", "Accueil"], analyses: ["Matchs & marchés", "Analyses"],
  ticket: ["Combiné & valeur", "Mon ticket"], stats: ["Validation du moteur", "Statistiques"],
  profil: ["Préférences & suivi", "Mon profil"], detail: ["Analyse d'un match", "Détail du match"],
};

function majEntete() {
  const [sur, titre] = TITRES[etat.onglet];
  $("#sur-titre").textContent = sur;
  $("#titre-page").textContent = titre;
  document.querySelectorAll(".nav-item[data-onglet]").forEach((b) => {
    const actif = b.dataset.onglet === (etat.onglet === "detail" ? "analyses" : etat.onglet);
    b.classList.toggle("actif", actif);
  });
  const d = etat.donnees;
  const enLigne = etat.serveurActif;
  $("#source-badge").className = `source ${enLigne ? "serveur" : ""}`;
  $("#source-badge").innerHTML = `<span class="point"></span><span>${enLigne ? "Serveur de pronostics" : "Données de démonstration"}</span>`;
  $("#date-generation").textContent = `Généré le ${d.genere_le ? `${dateFr(d.genere_le + (d.genere_le.endsWith("Z") ? "" : "Z"))} à ${heureFr(d.genere_le + (d.genere_le.endsWith("Z") ? "" : "Z"))} UTC` : "—"}`;
  const pastille = $("#pastille-source");
  pastille.textContent = enLigne ? "EN DIRECT" : "HORS LIGNE";
  pastille.classList.toggle("serveur", enLigne);
  const g = $("#recherche-globale");
  if (g && g.value !== etat.recherche) g.value = etat.recherche;
}

function rendre(garderScroll = false) {
  if (!etat.donnees) return;
  const y = window.scrollY;
  majEntete();
  contenu.innerHTML = (VUES[etat.onglet] || vueAccueil)();
  majBarreTicket();
  if (garderScroll) window.scrollTo(0, y);
  else window.scrollTo({ top: 0, behavior: "instant" });
}

/* --------------------------------------------------------------- serveur ---- */
function urlServeur() {
  const u = (etat.reglages.serveur || "").trim();
  if (!u) return null;
  return u.replace(/\/$/, "");
}
async function chargerServeur(testerSeulement = false) {
  const base = urlServeur();
  if (!base) { toast("Indiquez d'abord une adresse de serveur (par exemple /api)", "erreur"); return; }
  toast("Connexion au serveur…");
  try {
    const r = await fetch(`${base}/`, { signal: AbortSignal.timeout(6000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const info = await r.json();
    if (testerSeulement) { toast(`Serveur OK : ${info.application || "MISSA FOOT 360"} · ${info.genere_le || ""}`); return; }
    const r2 = await fetch(`${base}/matchs?avec_matrice=true`, { signal: AbortSignal.timeout(12000) });
    if (!r2.ok) throw new Error(`HTTP ${r2.status} sur /matchs`);
    const payload = await r2.json();
    if (!payload.championnats?.length) throw new Error("aucun match renvoyé");
    const locales = JSON.parse(JSON.stringify(etat.donneesLocales));
    locales.championnats = payload.championnats.map((c) => ({ code: c.code, nom: c.nom, matchs: c.matchs }));
    locales.genere_le = payload.genere_le || locales.genere_le;
    locales.source_donnees = "serveur";
    etat.donnees = locales;
    indexer(locales);
    etat.filtreDate = etat.dates[0] || "toutes";
    etat.serveurActif = true;
    etat.ticket = etat.ticket.filter((s) => etat.parId.has(s.matchId));
    sauvegarder();
    rendre();
    toast(`${etat.matchs.length} matchs chargés depuis le serveur`);
  } catch (e) {
    toast(`Serveur injoignable : ${e.message}. Retour aux données locales.`, "erreur");
  }
}
function revenirLocal() {
  etat.donnees = JSON.parse(JSON.stringify(etat.donneesLocales));
  indexer(etat.donnees);
  etat.filtreDate = etat.dates[0] || "toutes";
  etat.serveurActif = false;
  etat.ticket = etat.ticket.filter((s) => etat.parId.has(s.matchId));
  sauvegarder();
  rendre();
  toast("Données de démonstration restaurées");
}

/* ------------------------------------------------------------ événements ---- */
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const a = el.dataset.action;
  switch (a) {
    case "onglet":
      etat.onglet = el.dataset.onglet;
      if (etat.onglet === "analyses" && !etat.filtreDate) etat.filtreDate = etat.dates[0];
      if (etat.onglet !== "detail") etat.detail = null;
      rendre();
      break;
    case "retour":
      etat.detail = null;
      etat.onglet = "analyses";
      rendre();
      break;
    case "voir-detail":
      etat.detail = { matchId: el.dataset.mid, tab: el.dataset.tab || "apercu" };
      etat.onglet = "detail";
      etat.modulation = { attaque_dom: 1, attaque_ext: 1, corners_dom: 1, corners_ext: 1, cartons: 1 };
      etat.rechercheMarches = "";
      rendre();
      break;
    case "onglet-detail":
      if (etat.detail) { etat.detail.tab = el.dataset.tab; rendre(true); }
      break;
    case "profil-onglet":
      etat.profilTab = el.dataset.tab;
      rendre(true);
      break;
    case "filtre-accueil":
      etat.filtreAccueil = el.dataset.val;
      rendre(true);
      break;
    case "filtre-date":
      etat.filtreDate = el.dataset.date;
      rendre(true);
      break;
    case "ligue": {
      const c = el.dataset.code;
      if (etat.liguesOuvertes.has(c)) etat.liguesOuvertes.delete(c);
      else etat.liguesOuvertes.add(c);
      el.closest(".ligue")?.classList.toggle("fermee");
      break;
    }
    case "ajouter":
      ajouterSelection(matchDe(el.dataset.mid), el.dataset.code, el.dataset.libelle, el.dataset.cote);
      break;
    case "retirer":
      etat.ticket.splice(Number(el.dataset.index), 1);
      sauvegarder();
      rendre(true);
      break;
    case "vider-ticket":
      etat.ticket = [];
      sauvegarder();
      rendre();
      toast("Ticket vidé");
      break;
    case "enregistrer-ticket": {
      const r = calculerTicket();
      if (!r) return;
      etat.historique.unshift({
        date: horodatage(), statut: "En attente", proba: r.proba,
        coteTotale: r.coteTotale, mise: etat.mise, gain: r.gain,
        selections: etat.ticket.map((s) => ({ equipes: s.equipes, libelle: s.libelle })),
      });
      sauvegarder();
      toast("Ticket enregistré dans « Profil » : il sera vérifié après les matchs");
      break;
    }
    case "groupe":
      etat.groupeActif = el.dataset.groupe;
      etat.rechercheMarches = "";
      rendre(true);
      break;
    case "reset-modulation":
      etat.modulation = { attaque_dom: 1, attaque_ext: 1, corners_dom: 1, corners_ext: 1, cartons: 1 };
      rendre(true);
      toast("Modulation réinitialisée");
      break;
    case "generer-ticket":
      genererTicket();
      break;
    case "recherche-effacer":
      etat.recherche = "";
      etat.filtreDate = "toutes";
      etat.reglages.confiance = false;
      sauvegarder();
      rendre();
      break;
    case "tester-serveur":
      chargerServeur(true);
      break;
    case "utiliser-serveur":
      chargerServeur(false);
      break;
    case "serveur-local":
      revenirLocal();
      break;
    case "supprimer-historique":
      etat.historique.splice(Number(el.dataset.index), 1);
      sauvegarder();
      rendre(true);
      break;
    case "effacer-donnees":
      etat.ticket = []; etat.historique = []; etat.mise = 1000;
      etat.reglages = { serveur: "", confiance: false, devise: "XAF" };
      sauvegarder();
      rendre();
      toast("Données locales effacées");
      break;
    case "actualiser":
      demarrer(true);
      break;
    default: break;
  }
});

let timerRecherche;
document.addEventListener("input", (e) => {
  const el = e.target;
  const champ = el.dataset?.champ;
  if (!champ) return;
  if (champ === "recherche" || champ === "recherche-marches") {
    clearTimeout(timerRecherche);
    const v = el.value;
    timerRecherche = setTimeout(() => {
      if (champ === "recherche") {
        etat.recherche = v;
        const autre = document.getElementById(el.id === "recherche-globale" ? "recherche-analyses" : "recherche-globale");
        if (autre) autre.value = v;
        if (etat.onglet !== "analyses") { etat.onglet = "analyses"; etat.detail = null; }
        rendre(true);
        if (el.id === "recherche-analyses") {
          const n = document.getElementById("recherche-analyses");
          if (n) { n.focus(); n.setSelectionRange(v.length, v.length); }
        }
      } else {
        etat.rechercheMarches = v;
        const m = matchDe(etat.detail?.matchId);
        const cible = document.getElementById("liste-marches");
        if (m && cible) cible.innerHTML = tableauMarches(m, v ? "TOUS" : etat.groupeActif, v);
      }
    }, 140);
    return;
  }
  if (champ === "modulation") {
    const p = el.dataset.param;
    etat.modulation[p] = Number(el.value);
    const label = document.getElementById(`val-${p}`);
    if (label) label.textContent = `×${Number(el.value).toFixed(2).replace(".", ",")}`;
    const m = matchDe(etat.detail?.matchId);
    const cible = document.getElementById("mod-resultats");
    if (m && cible) cible.innerHTML = resultatsModulation(m);
    return;
  }
  if (champ === "mise") {
    etat.mise = Math.max(0, Number(el.value) || 0);
    sauvegarder();
    majResumeTicket();
    return;
  }
});

document.addEventListener("change", (e) => {
  const el = e.target;
  const champ = el.dataset?.champ;
  if (!champ) return;
  switch (champ) {
    case "cote": {
      const i = Number(el.dataset.index);
      const v = Number(el.value);
      if (etat.ticket[i] && v > 1) { etat.ticket[i].cote = v; sauvegarder(); majResumeTicket(); }
      break;
    }
    case "confiance":
      etat.reglages.confiance = el.checked;
      sauvegarder();
      rendre(true);
      break;
    case "serveur":
      etat.reglages.serveur = el.value.trim();
      sauvegarder();
      break;
    case "mise-defaut":
      etat.mise = Math.max(0, Number(el.value) || 0);
      sauvegarder();
      majResumeTicket();
      break;
    case "devise":
      etat.reglages.devise = el.value;
      sauvegarder();
      rendre(true);
      break;
    case "gen-nb":
      etat.generateur.nb = Math.max(1, Math.min(10, Number(el.value) || 3));
      sauvegarder();
      break;
    case "gen-cote":
      etat.generateur.coteMin = Math.max(1.01, Number(el.value) || 1.2);
      sauvegarder();
      break;
    case "gen-type":
      etat.generateur.types[el.dataset.type] = el.checked;
      sauvegarder();
      break;
    case "famille": {
      etat.familleFiabilite = el.value;
      const fam = etat.donnees.fiabilite?.[el.value] || [];
      const cible = document.getElementById("fiabilite-chart");
      if (cible) cible.innerHTML = barresComparees(fam.map((b) => ({
        label: `${pct(b.de, 0)} – ${pct(b.a, 0)}`, annonce: b.annonce, reel: b.reel, n: b.n,
      })), "annoncé → observé sur saisons de test");
      break;
    }
    default: break;
  }
});

/* ------------------------------------------------------------- démarrage ---- */
async function demarrer(recharger = false) {
  try {
    const r = await fetch(`./data/donnees.json${recharger ? `?t=${Date.now()}` : ""}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const d = await r.json();
    etat.donneesLocales = d;
    // Conserver une éventuelle session serveur lors d'un simple rechargement.
    if (!recharger || !etat.serveurActif) {
      etat.donnees = d;
      indexer(d);
      etat.filtreDate = etat.dates[0] || "toutes";
      etat.serveurActif = false;
    }
    chargerLocal();
    etat.ticket = etat.ticket.filter((s) => etat.parId.has(s.matchId));
    rendre();
    if (recharger) toast("Données rechargées");
  } catch (err) {
    contenu.innerHTML = `<div class="erreur-bloc"><h2>Impossible de charger les données</h2>
      <p>${echapper(err.message)}. Vérifiez que l'application est servie par <code>python3 web/serveur.py</code>
      et que <code>web/data/donnees.json</code> existe (généré par <code>web/scripts/preparer_donnees.py</code>).</p>
      <button class="bouton" data-action="actualiser" style="margin-top:12px">Réessayer</button></div>`;
  }
}

demarrer();
