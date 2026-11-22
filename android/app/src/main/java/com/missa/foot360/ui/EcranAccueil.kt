package com.missa.foot360.ui

import androidx.compose.foundation.background
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

    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 110.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            Text("ANALYSE FOOTBALL INTELLIGENTE", fontSize = 11.sp, color = Vert, fontWeight = FontWeight.Bold)
            Text(if (etat.horsLigne) "Données de démonstration (hors ligne)"
                 else "Analyses du ${dateGeneration(etat.pronostics.genere_le)}", fontSize = 12.sp)
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Indicateur("${etat.matchs.size}", "Matchs analysés", Modifier.weight(1f))
                Indicateur(pct(st?.reussite_globale, 0), "Réussite mesurée", Modifier.weight(1f))
                Indicateur("${etat.matchs.values.count { it.selection_haute_confiance != null }}", "Sélections fiables", Modifier.weight(1f))
            }
            if (st != null) Text("Réussite mesurée sur ${"%,d".format(st.pronostics_evalues).replace(',', ' ')} pronostics de matchs " +
                "jamais vus par le moteur ; ${pct(st.par_niveau.firstOrNull()?.reussite, 0)} pour la confiance très haute.",
                fontSize = 10.sp, modifier = Modifier.padding(top = 4.dp))
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("Aujourd'hui", "Demain", "Tous").forEach { f ->
                    FilterChip(selected = filtre == f, onClick = { filtre = f }, label = { Text(f, fontSize = 12.sp) })
                }
            }
        }
        item { EnTete("Matchs recommandés", "Voir tout →") { aller("matchs") } }
        if (recommandes.isEmpty()) item { Text("Aucune sélection très fiable pour cette période.", fontSize = 12.sp) }
        items(recommandes.take(8), key = { it.first.id }) { (m, code) -> CarteRecommandee(m, code, etat, vm, ouvrir) }

        val value = etat.pronostics.value.filter { v -> tous.any { it.id == v.match_id } }
        if (value.isNotEmpty()) {
            item { EnTete("Meilleures opportunités (value)", "Voir tout →") { aller("conseils") } }
            items(value.take(3), key = { "v" + it.match_id + it.selection }) { v ->
                Card(Modifier.fillMaxWidth().clickable { ouvrir(v.match_id) }) {
                    Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("${v.domicile} – ${v.exterieur}", fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text("${v.libelle} · cote ${cote(v.meilleure_cote)}${v.bookmaker?.let { " ($it)" } ?: ""}", fontSize = 12.sp, color = Or)
                        }
                        Badge("+${"%.1f".format(v.valeur_brute * 100)} %", Vert)
                    }
                }
            }
        }
        item {
            Card(Modifier.fillMaxWidth().clickable { aller("assistant") },
                colors = CardDefaults.cardColors(containerColor = VertFonce)) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Générateur de tickets", fontWeight = FontWeight.Bold, color = Vert)
                        Text("Choisissez le nombre de matchs et le risque : le moteur assemble le ticket le plus sûr.", fontSize = 12.sp)
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
                        "haute confiance : ${pct(s.confiance.reussite, 0)} sur ${s.confiance.regles}.", fontSize = 12.sp)
            }
        }
    }
}

@Composable
private fun Indicateur(valeur: String, titre: String, modifier: Modifier) {
    Column(modifier.clip(RoundedCornerShape(10.dp)).background(MaterialTheme.colorScheme.surface).padding(10.dp),
        horizontalAlignment = Alignment.CenterHorizontally) {
        Text(valeur, fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Vert)
        Text(titre, fontSize = 10.sp, maxLines = 1)
    }
}

@Composable
fun EnTete(titre: String, action: String? = null, onAction: () -> Unit = {}) {
    Row(Modifier.fillMaxWidth().padding(top = 6.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(titre, fontWeight = FontWeight.Bold, fontSize = 15.sp, modifier = Modifier.weight(1f))
        if (action != null) Text(action, fontSize = 12.sp, color = Vert, modifier = Modifier.clickable(onClick = onAction))
    }
}

@Composable
private fun CarteRecommandee(m: Match, code: String, etat: EtatApp, vm: AppViewModel, ouvrir: (String) -> Unit) {
    val p = vm.proba(m.id, code) ?: 0.0
    val (r, couleur) = risque(p)
    val dans = etat.combi.any { it.matchId == m.id && it.code == code }
    val nomChamp = etat.pronostics.championnats.firstOrNull { c -> c.matchs.any { it.id == m.id } }?.nom ?: ""
    Card(Modifier.fillMaxWidth().clickable { ouvrir(m.id) }) {
        Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("${nomChamp.uppercase()} · ${m.heure}", fontSize = 10.sp, color = Or, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(m.domicile, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(m.exterieur, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(vm.libelleComplet(code).substringAfter(" : "), fontSize = 12.sp, color = Vert)
                    Spacer(Modifier.width(6.dp))
                    Text("Risque : $r", fontSize = 11.sp, color = couleur)
                }
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                PourcentageAnime(p, taille = 22.sp, couleur = couleurProba(p))
                Spacer(Modifier.height(4.dp))
                BoutonSelection(if (dans) "Ajouté" else "+ Ajouter", null, dans, Modifier.width(84.dp)) {
                    vm.basculer(m, code, vm.libelleComplet(code))
                }
            }
        }
    }
}
