/* Harnais Node : calcule les probabilités d'une liste de cas avec le jumeau JS.
 * Usage : node web/tests/jumeau_node.mjs /tmp/cas.json  > resultats.json
 * Entrée : {"donnees": "<chemin web/data/donnees.json>", "cas": [...]}
 * Sortie : [{"proba": ..., "ref": ...}, ...] dans le même ordre.
 */
import fs from "node:fs";
import { JumeauMatch, jumeauDepuisMatch, probaCombine } from "../js/jumeau.js";

const entree = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const donnees = JSON.parse(fs.readFileSync(entree.donnees, "utf8"));
const matchs = new Map();
for (const c of donnees.championnats) for (const m of c.matchs) matchs.set(m.id, m);

const sortie = entree.cas.map((cas) => {
  const J0 = cas.matchId ? jumeauDepuisMatch(matchs.get(cas.matchId)) : null;
  const J = J0 && cas.modulation ? J0.moduler(cas.modulation) : J0;
  let proba;
  if (cas.type === "combine") {
    const jumeaux = { [cas.matchId]: J };
    proba = probaCombine(cas.legs.map((code) => ({ matchId: cas.matchId, code })),
      jumeaux, false).proba;
  } else if (cas.type === "ticket") {
    const jumeaux = {};
    for (const leg of cas.legs) jumeaux[leg.matchId] =
      jumeauDepuisMatch(matchs.get(leg.matchId));
    proba = probaCombine(cas.legs, jumeaux, true).proba;
  } else {
    proba = J.proba(cas.code);
  }
  return { proba };
});
process.stdout.write(JSON.stringify(sortie));
