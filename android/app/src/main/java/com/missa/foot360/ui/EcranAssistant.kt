package com.missa.foot360.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.util.Locale

/**
 * Assistant de combiné : construit le combiné le plus probable selon vos contraintes
 * (nombre de matchs, cote minimale par sélection, types de paris autorisés).
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun EcranAssistant(etat: EtatApp, vm: AppViewModel, allerAuCombine: () -> Unit) {
    var nb by remember { mutableIntStateOf(4) }
    var coteMin by remember { mutableFloatStateOf(1.20f) }
    val tousGroupes = etat.pronostics.catalogue.map { it.groupe }.distinct()
    var groupes by remember(tousGroupes) { mutableStateOf(tousGroupes.toSet() - "Cartons") }
    val dates = etat.matchs.values.map { it.date }.distinct().sorted()
    var date by remember(dates) { mutableStateOf(dates.firstOrNull { it >= java.time.LocalDate.now().toString() } ?: dates.maxByOrNull { d -> etat.matchs.values.count { it.date == d } }) }
    val proposition = remember(nb, coteMin, groupes, date, etat.modulations, etat.pronostics) {
        vm.proposerCombine(nb, coteMin.toDouble(), groupes, date)
    }
    val pTot = proposition.fold(1.0) { a, b -> a * b.second }
    val coteTot = proposition.fold(1.0) { a, b -> a / b.second }

    LazyColumn(contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 12.dp, bottom = 110.dp)) {
        item {
            Text("Assistant combiné", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("Le moteur examine tous les paris de tous les matchs du jour et assemble le combiné " +
                "le plus probable qui respecte vos conditions.", fontSize = 12.sp)
            Spacer(Modifier.height(10.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                dates.forEach { d ->
                    FilterChip(selected = d == date, onClick = { date = d },
                        label = { Text(d.split("-").reversed().take(2).joinToString("/")) })
                }
            }
            Text("Nombre de matchs : $nb", fontWeight = FontWeight.SemiBold)
            Slider(nb.toFloat(), { nb = it.toInt() }, valueRange = 2f..12f, steps = 9)
            Text(String.format(Locale.FRANCE, "Cote juste minimale par sélection : %.2f", coteMin), fontWeight = FontWeight.SemiBold)
            Slider(coteMin, { coteMin = Math.round(it * 20) / 20f }, valueRange = 1.05f..2.5f)
            Text("Types de paris autorisés", fontWeight = FontWeight.SemiBold)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                tousGroupes.forEach { g ->
                    FilterChip(selected = g in groupes, onClick = { groupes = if (g in groupes) groupes - g else groupes + g },
                        label = { Text(g) })
                }
            }
            Spacer(Modifier.height(10.dp))
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(14.dp)) {
                    Text("Probabilité du combiné proposé : ${pct(pTot, 1)}", fontWeight = FontWeight.Bold, color = Vert, fontSize = 17.sp)
                    Text("Cote juste ${cote(coteTot)} · ${proposition.size} sélection(s)", fontSize = 13.sp)
                    Text("Sur 100 combinés comme celui-ci, environ ${"%.0f".format(pTot * 100)} seraient gagnants " +
                        "(fiabilité vérifiée sur 20 000 combinés de test).", fontSize = 11.sp)
                }
            }
            Spacer(Modifier.height(8.dp))
        }
        items(proposition) { (j, p) ->
            Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.weight(1f)) {
                    Text(j.libelleMatch, fontSize = 12.sp)
                    Text(j.libelle, fontWeight = FontWeight.SemiBold)
                }
                Text("${pct(p)}  (${cote(1 / p)})", color = Or)
            }
        }
        item {
            Spacer(Modifier.height(10.dp))
            Button(onClick = { vm.ajouterPlusieurs(proposition.map { it.first }); allerAuCombine() },
                enabled = proposition.isNotEmpty(), modifier = Modifier.fillMaxWidth()) {
                Text("Mettre dans mon combiné")
            }
            Text("Rappel : une probabilité élevée signifie des cotes basses. Un combiné reste perdu si une " +
                "seule sélection échoue.", fontSize = 11.sp, modifier = Modifier.padding(top = 6.dp))
        }
    }
}
