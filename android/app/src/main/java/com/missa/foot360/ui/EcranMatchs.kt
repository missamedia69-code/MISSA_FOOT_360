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

@OptIn(ExperimentalFoundationApi::class)
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

    LazyColumn(contentPadding = PaddingValues(bottom = 90.dp)) {
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

@Composable
fun CarteMatch(m: Match, vm: AppViewModel, etat: EtatApp, ouvrir: () -> Unit) {
    Card(
        Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 5.dp).clickable(onClick = ouvrir),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(m.heure, fontSize = 12.sp, color = Or)
                Spacer(Modifier.width(8.dp))
                Text("${m.domicile} - ${m.exterieur}", fontWeight = FontWeight.SemiBold,
                    maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
            }
            Spacer(Modifier.height(4.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Score probable ${m.score_probable}", fontSize = 11.sp)
                Text("· Prono : ${m.pronostic_principal}", fontSize = 11.sp)
            }
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("1", "N", "2").forEach { c ->
                    val code = "1X2:$c"
                    BoutonSelection(c, vm.proba(m.id, code) ?: m.marches[c]?.proba,
                        etat.combi.any { it.matchId == m.id && it.code == code },
                        Modifier.weight(1f)) { vm.basculer(m, code, "1X2 : $c") }
                }
            }
            val sure = m.selection_haute_confiance
            if (sure != null || m.selections_value.isNotEmpty() || m.pronostiqueurs.isNotEmpty()) {
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (sure != null) {
                        val c = m.marches[sure]?.confiance
                        Badge("★ ${c?.let { m.marches[sure]?.libelle } ?: sure} · historique ${pct(c?.taux_historique, 0)}", Or)
                    }
                    if (m.selections_value.isNotEmpty()) Badge("VALUE", Vert)
                    if (m.pronostiqueurs.isNotEmpty()) Badge("${m.pronostiqueurs.size} expert(s)", couleurs.surfaceVariant, couleurs.onSurface)
                }
            }
        }
    }
}
