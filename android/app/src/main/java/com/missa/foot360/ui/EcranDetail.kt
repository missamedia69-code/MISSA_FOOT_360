package com.missa.foot360.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AddCircleOutline
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.data.Match
import com.missa.foot360.moteur.Selections

private val SECTIONS = listOf(
    "Résultat" to listOf("1", "N", "2"),
    "Double chance" to listOf("1N", "12", "N2"),
    "Nombre de buts" to listOf("plus_1.5", "moins_1.5", "plus_2.5", "moins_2.5", "plus_3.5", "moins_3.5"),
    "Les deux équipes marquent" to listOf("btts_oui", "btts_non", "dom_marque", "ext_marque"),
)

@Composable
fun EcranDetail(m: Match?, etat: EtatApp, vm: AppViewModel) {
    if (m == null) { Text("Match introuvable", Modifier.padding(16.dp)); return }
    LazyColumn(contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 12.dp, bottom = 100.dp)) {
        item {
            Text("${m.domicile} - ${m.exterieur}", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("${m.date.split("-").reversed().joinToString("/")} à ${m.heure}", color = Or)
            Spacer(Modifier.height(8.dp))
            Text("Buts attendus : ${m.buts_attendus.joinToString(" - ") { cote(it) }}  ·  Score le plus probable : ${m.score_probable}")
            Text("Méthode : ${m.methode}", fontSize = 12.sp)
            Spacer(Modifier.height(4.dp))
            Text("Touchez une ligne pour l'ajouter au combiné.", fontSize = 12.sp, color = Vert)
        }
        SECTIONS.forEach { (titre, codes) ->
            item {
                Spacer(Modifier.height(14.dp))
                Text(titre, fontWeight = FontWeight.Bold, color = Vert)
                HorizontalDivider()
            }
            codes.forEach { c -> item { LigneMarche(m, c, etat, vm) } }
        }
        item {
            Spacer(Modifier.height(14.dp))
            Text("Scores exacts les plus probables", fontWeight = FontWeight.Bold, color = Vert)
            HorizontalDivider()
        }
        val scores = m.matrice.flatMapIndexed { i, r -> r.mapIndexed { j, p -> Triple(i, j, p) } }
            .sortedByDescending { it.third }.take(6)
        scores.forEach { (i, j, p) ->
            item {
                val code = "score:$i-$j"
                LigneSimple("Score $i-$j", p, etat.combi.any { it.matchId == m.id && it.code == code }) {
                    vm.basculer(m, code)
                }
            }
        }
        item {
            Spacer(Modifier.height(14.dp))
            Text("Avis des pronostiqueurs", fontWeight = FontWeight.Bold, color = Vert)
            HorizontalDivider()
            if (m.pronostiqueurs.isEmpty()) Text("Aucun pronostic enregistré pour ce match.", fontSize = 13.sp)
            m.pronostiqueurs.forEach { a ->
                Column(Modifier.padding(vertical = 6.dp)) {
                    Text("${a.pronostiqueur} : ${Selections.libelle(a.selection)} @ ${cote(a.cote)}", fontWeight = FontWeight.SemiBold)
                    Text("${a.statut} — effet sur la probabilité : ${signe(a.ajustement)}", fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun LigneMarche(m: Match, code: String, etat: EtatApp, vm: AppViewModel) {
    val mk = m.marches[code] ?: return
    val sel = etat.combi.any { it.matchId == m.id && it.code == code }
    Column(Modifier.fillMaxWidth().clickable { vm.basculer(m, code) }.padding(vertical = 8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(mk.libelle, Modifier.weight(1f), fontWeight = if (sel) FontWeight.Bold else FontWeight.Normal)
            Text(pct(mk.proba), fontWeight = FontWeight.Bold)
            Icon(if (sel) Icons.Default.CheckCircle else Icons.Default.AddCircleOutline, null,
                tint = if (sel) Vert else MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.padding(start = 8.dp))
        }
        BarreProba(mk.proba, Modifier.padding(vertical = 4.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Cote juste ${cote(mk.cote_juste)}", fontSize = 11.sp)
            if (mk.meilleure_cote != null) Text("Meilleure cote ${cote(mk.meilleure_cote)}", fontSize = 11.sp)
            if (mk.valeur != null && mk.valeur > 0.02) Badge("VALUE ${signe(mk.valeur)}", Vert)
        }
        mk.confiance?.let { c ->
            if (c.taux_historique != null && c.n_historique > 0) {
                Text("${c.niveau} — historique : ${pct(c.taux_historique)} de réussite sur ${c.n_historique} sélections",
                    fontSize = 11.sp, color = if (c.haute_confiance) Or else MaterialTheme.colorScheme.onSurface)
            }
        }
    }
}

@Composable
private fun LigneSimple(titre: String, p: Double, sel: Boolean, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Text(titre, Modifier.weight(1f))
        Text("${pct(p)}  (cote juste ${cote(1 / p)})", fontSize = 13.sp)
        Icon(if (sel) Icons.Default.CheckCircle else Icons.Default.AddCircleOutline, null,
            tint = if (sel) Vert else MaterialTheme.colorScheme.onSurface, modifier = Modifier.padding(start = 8.dp))
    }
}
