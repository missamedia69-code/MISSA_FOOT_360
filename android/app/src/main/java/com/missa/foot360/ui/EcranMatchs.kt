package com.missa.foot360.ui

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.data.Match
import com.missa.foot360.moteur.Jumeau

@OptIn(ExperimentalFoundationApi::class, androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun EcranMatchs(etat: EtatApp, vm: AppViewModel, ouvrir: (String) -> Unit) {
    if (etat.chargement) {
        Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally) { CircularProgressIndicator() }
        return
    }
    val dates = etat.pronostics.championnats.flatMap { c -> c.matchs.map { it.date } }.distinct().sorted()
    // Jour affiché par défaut : aujourd'hui ou le prochain jour de match, sinon le plus chargé
    val parDefaut = remember(dates) {
        val aujourdhui = java.time.LocalDate.now().toString()
        val tous = etat.pronostics.championnats.flatMap { c -> c.matchs.map { it.date } }
        dates.firstOrNull { it >= aujourdhui } ?: dates.maxByOrNull { d -> tous.count { it == d } }
    }
    var date by remember(dates) { mutableStateOf(parDefaut) }
    val replies = remember { mutableStateMapOf<String, Boolean>() }

    PullToRefreshBox(isRefreshing = etat.actualisation, onRefresh = { vm.actualiser() }) {
    LazyColumn(contentPadding = PaddingValues(bottom = 90.dp)) {
        if (!etat.horsLigne && etat.pronostics.genere_le.isNotEmpty()) item {
            Text("Pronostics calculés le ${dateGeneration(etat.pronostics.genere_le)} · tirez vers le bas ou touchez ⟳ pour actualiser",
                fontSize = 11.sp, modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp))
        }
        if (!etat.horsLigne && dates.isEmpty()) item {
            Text("Aucun match à venir n'est publié pour le moment. Les calendriers et les cotes sont " +
                "mis à jour le mardi et le vendredi après-midi ; les pronostics sont recalculés " +
                "automatiquement toutes les 3 heures.", fontSize = 13.sp, modifier = Modifier.padding(16.dp))
        }
        if (etat.horsLigne) item {
            Text("Mode démonstration hors ligne (pronostics injoignables : pas de connexion ?). Données d'exemple.",
                color = Or, fontSize = 12.sp, modifier = Modifier.padding(12.dp))
        }
        item {
            LazyRow(contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(dates) { d ->
                    FilterChip(selected = d == date, onClick = { date = d },
                        label = { Text(d.split("-").reversed().joinToString("/")) })
                }
            }
        }
        etat.pronostics.championnats.forEach { champ ->
            val matchs = champ.matchs.filter { it.date == date }
            if (matchs.isEmpty()) return@forEach
            val replie = replies[champ.code] == true
            stickyHeader(key = champ.code) {
                Row(
                    Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.background)
                        .clickable { replies[champ.code] = !replie }.padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(champ.nom, fontWeight = FontWeight.Bold, color = Vert, modifier = Modifier.weight(1f))
                    Text("${matchs.size} matchs", fontSize = 12.sp)
                    Icon(if (replie) Icons.Default.ExpandMore else Icons.Default.ExpandLess, null)
                }
            }
            if (!replie) items(matchs, key = { it.id }) { m ->
                CarteMatch(m, vm, etat) { ouvrir(m.id) }
            }
        }
    }
    }
}

/** Options rapides proposées sur chaque carte (code du jumeau, libellé court). */
private val OPTIONS_RAPIDES = listOf(
    "DC:1N" to "1N", "DC:12" to "12", "DC:N2" to "N2",
    "OU:1.5:plus" to "+1,5", "OU:2.5:plus" to "+2,5", "OU:2.5:moins" to "−2,5", "OU:3.5:moins" to "−3,5",
    "BTTS:oui" to "2 marquent", "BTTS:non" to "Pas les 2",
    "HCP2:-1.5:1" to "Dom. −1,5", "HCP2:1.5:1" to "Dom. +1,5",
    "HCP3:-1:1" to "H(−1) 1", "1X2@MT1:1" to "MT 1", "1X2@MT1:N" to "MT N",
)

@Composable
fun CarteMatch(m: Match, vm: AppViewModel, etat: EtatApp, ouvrir: () -> Unit) {
    val prono = m.pronostic_principal
    val pProno = vm.proba(m.id, "1X2:$prono") ?: m.marches[prono]?.proba
    val texteProno = when (prono) { "1" -> "Victoire ${m.domicile}"; "2" -> "Victoire ${m.exterieur}"; else -> "Match nul" }
    Card(
        Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 4.dp).clickable(onClick = ouvrir),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(horizontal = 10.dp, vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(m.heure, fontSize = 12.sp, color = Or, modifier = Modifier.width(42.dp))
                Text("${m.domicile} – ${m.exterieur}", fontWeight = FontWeight.SemiBold, fontSize = 14.sp,
                    maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
                if (m.selections_value.isNotEmpty()) Badge("VALUE", Vert)
            }
            // Pronostic du moteur, en clair
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Pronostic : ", fontSize = 12.sp)
                Text(texteProno, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Vert,
                    maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f, fill = false))
                Text(" · ", fontSize = 12.sp)
                PourcentageAnime(pProno, taille = 12.sp, couleur = Vert)
                Text("  ·  score ${m.score_probable}", fontSize = 11.sp)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("1", "N", "2").forEach { c ->
                    val code = "1X2:$c"
                    BoutonSelection(c, vm.proba(m.id, code) ?: m.marches[c]?.proba,
                        etat.combi.any { it.matchId == m.id && it.code == code },
                        Modifier.weight(1f)) { vm.basculer(m, code, vm.libelleComplet(code)) }
                }
            }
            // Autres paris, faites glisser
            LazyRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                items(OPTIONS_RAPIDES, key = { it.first }) { (code, court) ->
                    BoutonSelection(court, vm.proba(m.id, code), etat.combi.any { it.matchId == m.id && it.code == code },
                        Modifier.width(76.dp)) { vm.basculer(m, code, vm.libelleComplet(code)) }
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                val sure = m.selection_haute_confiance
                if (sure != null) {
                    val c = m.marches[sure]?.confiance
                    Badge("★ ${m.marches[sure]?.libelle ?: sure} · réel ${pct(c?.taux_historique, 0)}", Or)
                }
                if (m.pronostiqueurs.isNotEmpty()) {
                    Spacer(Modifier.width(6.dp))
                    Badge("${m.pronostiqueurs.size} expert(s)", couleurs.surfaceVariant, couleurs.onSurface)
                }
                Spacer(Modifier.weight(1f))
                Text("Tous les paris (${etat.pronostics.catalogue.sumOf { it.options.size }}) ›",
                    fontSize = 11.sp, color = Or, modifier = Modifier.clickable(onClick = ouvrir))
            }
        }
    }
}
