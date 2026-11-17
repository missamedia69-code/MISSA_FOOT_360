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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.PrimaryScrollableTabRow
import androidx.compose.material3.Slider
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.data.Match
import com.missa.foot360.moteur.Modulation
import java.util.Locale

@OptIn(ExperimentalLayoutApi::class, androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun EcranDetail(m: Match?, etat: EtatApp, vm: AppViewModel) {
    if (m == null) { Text("Match introuvable", Modifier.padding(16.dp)); return }
    if (m.jumeau == null) { Text("Données détaillées indisponibles pour ce match.", Modifier.padding(16.dp)); return }
    val groupes = etat.pronostics.catalogue.map { it.groupe }.distinct()
    var onglet by remember { mutableIntStateOf(0) }
    var voirModulation by remember { mutableStateOf(false) }
    val mod = etat.modulations[m.id] ?: Modulation()

    LazyColumn(contentPadding = PaddingValues(bottom = 110.dp)) {
        item {
            Column(Modifier.padding(16.dp)) {
                Text("${m.domicile} - ${m.exterieur}", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                Text("${m.date.split("-").reversed().joinToString("/")} à ${m.heure}", color = Or)
                Spacer(Modifier.height(6.dp))
                val j = vm.jumeau(m.id)
                val bd = j?.let { (0 until it.matrice.size).sumOf { i -> i * it.matrice[i].sum() } }
                val be = j?.let { (0 until it.matrice.size).sumOf { k -> k * it.matrice.sumOf { r -> r[k] } } }
                Text("Buts attendus : ${cote(bd)} - ${cote(be)}  ·  Corners : ${m.corners_attendus.joinToString(" - ") { cote(it) }}  ·  Cartons : ${m.cartons_attendus.joinToString(" - ") { cote(it) }}", fontSize = 13.sp)
                Text("Touchez une option pour l'ajouter au combiné. Plusieurs options d'un même match = probabilité conjointe exacte.",
                    fontSize = 12.sp, color = Vert)
                TextButton(onClick = { voirModulation = !voirModulation }) {
                    Text(if (mod.neutre) "⚙ Moduler le match (absences, forme, arbitre…)" else "⚙ Modulation active — modifier")
                }
                if (voirModulation) PanneauModulation(mod) { vm.moduler(m.id, it) }
            }
        }
        item {
            PrimaryScrollableTabRow(selectedTabIndex = onglet, edgePadding = 8.dp) {
                groupes.forEachIndexed { i, g -> Tab(selected = onglet == i, onClick = { onglet = i }, text = { Text(g) }) }
            }
        }
        val groupe = groupes.getOrNull(onglet)
        items(etat.pronostics.catalogue.filter { it.groupe == groupe }) { gm ->
            Column(Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
                Text(gm.titre, fontWeight = FontWeight.Bold, color = Vert)
                HorizontalDivider(Modifier.padding(vertical = 4.dp))
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    gm.options.forEach { o ->
                        val p = vm.proba(m.id, o.code)
                        val sel = etat.combi.any { it.matchId == m.id && it.code == o.code }
                        val hist = p?.let { tauxHistorique(etat.pronostics.fiabilite, familleFiabilite(o.code), it) }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            BoutonSelection(o.libelle, p, sel, Modifier.width(104.dp)) {
                                vm.basculer(m, o.code, "${gm.titre} : ${o.libelle}")
                            }
                            Text("cote juste ${cote(p?.let { if (it > 0) 1 / it else null })}", fontSize = 10.sp)
                            if (hist != null && hist.n >= 100 && (p ?: 0.0) >= 0.5)
                                Text("réel ${pct(hist.reel, 0)}", fontSize = 10.sp, color = Or)
                        }
                    }
                }
            }
        }
        item {
            Column(Modifier.padding(16.dp)) {
                Text("Pronostiqueurs", fontWeight = FontWeight.Bold, color = Vert)
                if (m.pronostiqueurs.isEmpty()) Text("Aucun pronostic d'expert enregistré pour ce match.", fontSize = 12.sp)
                m.pronostiqueurs.forEach { a ->
                    Text("${a.pronostiqueur} : ${a.selection} @ ${cote(a.cote)} — ${a.statut} (effet ${signe(a.ajustement)})", fontSize = 12.sp)
                }
                Spacer(Modifier.height(8.dp))
                Text("« réel » = part des sélections de ce type et de ce niveau de probabilité qui ont réellement " +
                    "gagné sur les saisons de test (jamais vues par le moteur).", fontSize = 11.sp)
            }
        }
    }
}

@Composable
private fun PanneauModulation(mod: Modulation, changer: (Modulation) -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Text("Votre information corrige le modèle. Exemples : buteur principal absent ≈ attaque −10 à −15 % ; " +
                "arbitre sévère ≈ cartons +20 %.", fontSize = 11.sp)
            Curseur("Attaque domicile", mod.attaqueDom) { changer(mod.copy(attaqueDom = it)) }
            Curseur("Attaque extérieur", mod.attaqueExt) { changer(mod.copy(attaqueExt = it)) }
            Curseur("Corners domicile", mod.cornersDom) { changer(mod.copy(cornersDom = it)) }
            Curseur("Corners extérieur", mod.cornersExt) { changer(mod.copy(cornersExt = it)) }
            Curseur("Cartons (arbitre, enjeu)", mod.cartons) { changer(mod.copy(cartons = it)) }
            TextButton(onClick = { changer(Modulation()) }) { Text("Réinitialiser") }
        }
    }
}

@Composable
private fun Curseur(titre: String, valeur: Double, changer: (Double) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(titre, fontSize = 12.sp, modifier = Modifier.width(150.dp))
        Slider(value = valeur.toFloat(), onValueChange = { changer(Math.round(it * 20) / 20.0) },
            valueRange = 0.5f..1.5f, steps = 19, modifier = Modifier.weight(1f))
        Text(String.format(Locale.FRANCE, "%+.0f %%", (valeur - 1) * 100), fontSize = 12.sp,
            modifier = Modifier.width(48.dp))
    }
}
