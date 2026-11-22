package com.missa.foot360.ui

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
import androidx.compose.material3.Card
import androidx.compose.material3.PrimaryTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.moteur.Jumeau

/** Onglet « Conseils » : haute confiance (probabilité élevée) et value (cote trop généreuse). */
@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun EcranConseils(etat: EtatApp, vm: AppViewModel, ouvrir: (String) -> Unit) {
    var onglet by remember { mutableIntStateOf(0) }
    Column {
        PrimaryTabRow(selectedTabIndex = onglet) {
            Tab(onglet == 0, { onglet = 0 }, text = { Text("Haute confiance") })
            Tab(onglet == 1, { onglet = 1 }, text = { Text("Value (${etat.pronostics.value.size})") })
        }
        if (onglet == 0) EcranConfiance(etat, vm, ouvrir) else EcranValue(etat, vm, ouvrir)
    }
}

@Composable
fun EcranValue(etat: EtatApp, vm: AppViewModel, ouvrir: (String) -> Unit) {
    val liste = etat.pronostics.value
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 12.dp, bottom = 110.dp)) {
        item {
            Text("Paris value", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("Un pari est « value » quand la meilleure cote du marché dépasse son prix juste (probabilité " +
                "du consensus, marge retirée). C'est la seule méthode dont l'avantage est démontré à long terme " +
                "(Buchdahl ; Kaunitz et al. : +3,5 % sur 56 435 paris). Le taux de réussite est souvent faible " +
                "(beaucoup d'outsiders) : seul le résultat sur des centaines de paris compte.", fontSize = 12.sp)
            Spacer(Modifier.height(8.dp))
            BilanValue(etat)
            Spacer(Modifier.height(8.dp))
            if (liste.isEmpty()) Text("Aucun pari value pour les matchs publiés.")
        }
        items(liste, key = { it.match_id + it.selection }) { v ->
            val m = etat.matchs[v.match_id]
            val code = Jumeau.depuisAncien(v.selection)
            val dans = etat.combi.any { it.matchId == v.match_id && it.code == code }
            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("${m?.date?.split("-")?.reversed()?.joinToString("/") ?: ""} ${m?.heure ?: ""} · ${v.championnat}", fontSize = 11.sp)
                        Text("${v.domicile} - ${v.exterieur}", fontSize = 13.sp)
                        Text(v.libelle, fontWeight = FontWeight.Bold, color = Vert)
                        Text("Probabilité ${pct(v.proba)} · cote juste ${cote(v.cote_juste)}", fontSize = 12.sp)
                        Text("Meilleure cote ${cote(v.meilleure_cote)}${v.bookmaker?.let { " chez $it" } ?: ""} · valeur ${signe(v.valeur_brute)}",
                            fontSize = 12.sp, color = Or)
                        Text("Mise conseillée (Kelly prudent) : ${pct(v.mise_kelly)} de votre capital", fontSize = 11.sp)
                        if (v.valeur_corrigee < v.valeur_brute / 2)
                            Text("Match encore loin : une partie de cette valeur disparaît souvent avant le coup d'envoi.",
                                fontSize = 10.sp)
                    }
                    Spacer(Modifier.width(8.dp))
                    if (m != null) BoutonSelection(if (dans) "Ajouté" else "Ajouter", v.proba, dans, Modifier.width(88.dp)) {
                        vm.basculer(m, code, v.libelle, v.meilleure_cote)
                    }
                }
            }
        }
        item {
            Text("Vérifiez la cote chez votre bookmaker : la value n'existe que si vous obtenez une cote au moins " +
                "égale à la cote juste. Saisissez-la dans votre ticket pour voir la valeur réelle.", fontSize = 11.sp,
                modifier = Modifier.padding(top = 8.dp))
        }
    }
}

@Composable
private fun BilanValue(etat: EtatApp) {
    val s = etat.pronostics.suivi_value ?: return
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text("Bilan des paris value publiés", fontWeight = FontWeight.Bold)
            Text("${s.publies} publiés · ${s.regles} joués · ${s.en_attente} en attente", fontSize = 12.sp)
            if (s.clv_moyen != null) Text("Valeur contre la cote de clôture (CLV) : ${signe(s.clv_moyen)} en moyenne" +
                (s.clv_positif?.let { " · ${pct(it, 0)} battent la clôture" } ?: ""), fontSize = 12.sp,
                color = if (s.clv_moyen > 0) Vert else Rouge)
            if (s.rendement != null) Text("Rendement réel à mise égale : ${signe(s.rendement)} (réussite ${pct(s.reussite, 0)})",
                fontSize = 12.sp)
            if (s.regles < 200) Text("Échantillon encore petit : le CLV est l'indicateur fiable ; le rendement dépend " +
                "beaucoup du hasard tant qu'il y a moins de quelques centaines de paris.", fontSize = 10.sp)
        }
    }
}
