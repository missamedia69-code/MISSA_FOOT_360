package com.missa.foot360.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.layout.Box
import kotlin.math.roundToInt
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.data.Match
import com.missa.foot360.moteur.Jumeau
import java.time.LocalDate

/** Accueil : le centre de contrôle (indicateurs réels, matchs recommandés, opportunités). */
@Composable
fun EcranAccueil(etat: EtatApp, vm: AppViewModel, ouvrir: (String) -> Unit, aller: (String) -> Unit) {
    val aujourdhui = LocalDate.now().toString()
    val demain = LocalDate.now().plusDays(1).toString()
    var filtre by remember { mutableStateOf("Tous") }
    val tous = etat.matchs.values.filter {
        when (filtre) { "Aujourd'hui" -> it.date == aujourdhui; "Demain" -> it.date == demain; else -> true }
    }
    val recommandes = tous.mapNotNull { m -> m.selection_haute_confiance?.let { c -> m to Jumeau.depuisAncien(c) } }
        .sortedByDescending { (m, c) -> vm.proba(m.id, c) ?: 0.0 }
    val st = etat.pronostics.stats_moteur

    if (etat.chargement) { ListeSquelette(); return }
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 110.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        etat.pronostics.config.annonce.takeIf { it.isNotBlank() }?.let { a ->
            item { Carte(Modifier.apparition()) { Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Text("📣", fontSize = 18.sp); Spacer(Modifier.width(8.dp)); Text(a, fontSize = 13.sp, color = Or) } } }
        }
        item {
            // Bandeau d'accueil : source des données, promesse, indicateurs mesurés
            Carte(Modifier.apparition(), accent = true) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        PointPulse(if (etat.horsLigne) Or else Vert)
                        Spacer(Modifier.width(6.dp))
                        Pastille(if (etat.horsLigne) "Données de démonstration (hors ligne)"
                                 else "En ligne · calculé le ${dateGeneration(etat.pronostics.genere_le)}",
                            if (etat.horsLigne) Or else Vert)
                    }
                    Text("Analyse football intelligente", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Text("Marché, Dixon-Coles et Elo combinés selon leur précision passée. Chaque match a son " +
                        "jumeau numérique : ${etat.pronostics.catalogue.sumOf { it.options.size }} paris calculés " +
                        "à partir d'une seule loi de probabilité.", fontSize = 12.sp, color = Discret)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Indicateur(etat.matchs.size, "", "Matchs analysés", Modifier.weight(1f))
                        Indicateur(((st?.reussite_globale ?: 0.0) * 100).roundToInt(), " %", "Réussite mesurée", Modifier.weight(1f))
                        Indicateur(etat.matchs.values.count { it.selection_haute_confiance != null }, "", "Sélections fiables", Modifier.weight(1f))
                    }
                    if (st != null) Text("Mesurée sur ${"%,d".format(st.pronostics_evalues).replace(',', ' ')} pronostics " +
                        "de matchs jamais vus par le moteur ; ${pct(st.par_niveau.firstOrNull()?.reussite, 0)} pour la confiance très haute.",
                        fontSize = 11.sp, color = Discret)
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("Aujourd'hui" to "Aujourd'hui · ${jourMois(aujourdhui)}", "Demain" to "Demain · ${jourMois(demain)}",
                    "Tous" to "Tous").forEach { (f, lib) ->
                    FilterChip(selected = filtre == f, onClick = { filtre = f }, label = { Text(lib, fontSize = 12.sp) })
                }
            }
        }
        item { EnTete("Matchs recommandés", "Voir tout →") { aller("matchs") } }
        if (recommandes.isEmpty()) item { Text("Aucune sélection très fiable pour cette période.", fontSize = 12.sp, color = Discret) }
        itemsIndexed(recommandes.take(8), key = { _, it -> it.first.id }) { rang, (m, code) ->
            Box(Modifier.apparition(rang)) { CarteRecommandee(m, code, etat, vm, ouvrir) }
        }
        if (etat.pronostics.tickets_speciaux.isNotEmpty()) {
            item { EnTete("Tickets spéciaux", "Voir tout →") { aller("speciaux") } }
            items(etat.pronostics.tickets_speciaux.take(2), key = { "ts" + it.id }) { t -> CarteTicketSpecial(t, etat, vm) }
        }

        val value = etat.pronostics.value.filter { v -> tous.any { it.id == v.match_id } }
        if (value.isNotEmpty()) {
            item { EnTete("Valeurs détectées", "Voir tout →") { aller("conseils") } }
            items(value.take(3), key = { "v" + it.match_id + it.selection }) { v ->
                val m = etat.matchs[v.match_id]
                val code = codeValue(v.selection)
                val dans = etat.combi.any { it.matchId == v.match_id && it.code == code }
                Carte(onClick = { ouvrir(v.match_id) }) {
                    Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("${v.championnat.uppercase()} · ${m?.heure ?: ""}", fontSize = 10.sp, color = Or,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text("${v.domicile} – ${v.exterieur}", fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text("${v.libelle} · ${pct(v.proba, 1)} · cote ${cote(v.meilleure_cote)}", fontSize = 11.sp, color = Discret)
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text("+${"%.1f".format(v.valeur_brute * 100)} %", color = Vert, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                            v.bookmaker?.let { Text(it, fontSize = 10.sp, color = Discret, maxLines = 1) }
                            if (m != null && code != null) BoutonAjouter(dans, Modifier.padding(top = 4.dp)) {
                                vm.basculer(m, code, vm.libelleComplet(code), v.meilleure_cote)
                            }
                        }
                    }
                }
            }
        }
        item {
            Carte(accent = true, onClick = { aller("assistant") }) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Surtitre("Assistant de combiné")
                        Text("Générateur de tickets", fontWeight = FontWeight.Bold)
                        Text("Choisissez le nombre de matchs et le risque : le moteur assemble le ticket le plus sûr.",
                            fontSize = 12.sp, color = Discret)
                    }
                    Text("›", fontSize = 24.sp, color = Vert)
                }
            }
        }
        etat.pronostics.suivi_pronostics?.let { s ->
            item {
                EnTete("Bilan en direct", "Détails →") { aller("stats") }
                Text(if (s.principal.regles == 0) "${s.principal.publies} pronostics publiés : les premiers résultats apparaîtront après les matchs."
                     else "Pronostics principaux : ${pct(s.principal.reussite, 0)} de réussite sur ${s.principal.regles} matchs joués · " +
                        "haute confiance : ${pct(s.confiance.reussite, 0)} sur ${s.confiance.regles}.", fontSize = 12.sp, color = Discret)
            }
        }
    }
}

/** « 2026-11-22 » -> « 22/11 ». */
fun jourMois(iso: String): String = if (iso.length < 10) iso else "${iso.substring(8, 10)}/${iso.substring(5, 7)}"

/** Code du jumeau correspondant à une sélection « value » publiée (1, N, 2, plus_2.5, moins_2.5). */
fun codeValue(sel: String): String? = when (sel) {
    "1", "N", "2" -> "1X2:$sel"
    "plus_2.5" -> "OU:2.5:plus"
    "moins_2.5" -> "OU:2.5:moins"
    else -> null
}

@Composable
private fun Indicateur(valeur: Int, suffixe: String, titre: String, modifier: Modifier) {
    Column(modifier.clip(RoundedCornerShape(12.dp)).background(Color(0x66060E09))
        .border(1.dp, Bord, RoundedCornerShape(12.dp)).padding(horizontal = 10.dp, vertical = 8.dp)) {
        NombreAnime(valeur, suffixe)
        Text(titre, fontSize = 10.sp, maxLines = 1, color = Discret)
    }
}

@Composable
fun EnTete(titre: String, action: String? = null, onAction: () -> Unit = {}) {
    Row(Modifier.fillMaxWidth().padding(top = 6.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(titre, fontWeight = FontWeight.Bold, fontSize = 16.sp, modifier = Modifier.weight(1f))
        if (action != null) Text(action, fontSize = 12.sp, color = Vert, modifier = Modifier.clickable(onClick = onAction))
    }
}

@Composable
private fun CarteRecommandee(m: Match, code: String, etat: EtatApp, vm: AppViewModel, ouvrir: (String) -> Unit) {
    val p = vm.proba(m.id, code) ?: 0.0
    val (r, couleur) = risque(p)
    val dans = etat.combi.any { it.matchId == m.id && it.code == code }
    val nomChamp = etat.pronostics.championnats.firstOrNull { c -> c.matchs.any { it.id == m.id } }?.nom ?: ""
    Carte(onClick = { ouvrir(m.id) }) {
        Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("${nomChamp.uppercase()} · ${m.heure}", fontSize = 10.sp, color = Or, maxLines = 1, overflow = TextOverflow.Ellipsis)
                listOf(m.domicile, m.exterieur).forEach { eq ->
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 1.dp)) {
                        LogoEquipe(eq, etat.pronostics.logos[eq], 20.dp)
                        Spacer(Modifier.width(7.dp))
                        Text(eq, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(vm.libelleComplet(code).substringAfter(" : "), fontSize = 12.sp, color = Vert, fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.width(6.dp))
                    Pastille("Risque ${r.lowercase()}", couleur, taille = 10.sp)
                }
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                PourcentageAnime(p, taille = 22.sp, couleur = couleurProba(p))
                Spacer(Modifier.height(4.dp))
                BoutonAjouter(dans, Modifier.width(92.dp)) {
                    vm.basculer(m, code, vm.libelleComplet(code))
                }
            }
        }
    }
}
