package com.missa.foot360.ui

import androidx.compose.foundation.clickable
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
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.moteur.Jumeau

/** Mode haute confiance : uniquement les sélections dont l'historique mesuré dépasse 85 %. */
@Composable
fun EcranConfiance(etat: EtatApp, vm: AppViewModel, ouvrir: (String) -> Unit) {
    val liste = etat.matchs.values.mapNotNull { m ->
        m.selection_haute_confiance?.let { c -> Triple(m, c, m.marches[c]) }
    }.sortedByDescending { it.third?.proba ?: 0.0 }
    // NB : ces sélections sont recalculées avec la modulation éventuelle de l'utilisateur
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 12.dp, bottom = 100.dp)) {
        item {
            Text("Mode haute confiance", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("Sélections dont le niveau de probabilité a atteint au moins 85 % de réussite réelle " +
                "sur les saisons de test (jamais vues par le moteur). Ce n'est pas une garantie : " +
                "environ 1 sur 10 reste perdante, et les cotes sont basses.", fontSize = 12.sp)
            Spacer(Modifier.height(10.dp))
            if (liste.isEmpty()) Text("Aucune sélection haute confiance pour les matchs disponibles.")
        }
        items(liste, key = { it.first.id }) { (m, code, mk) ->
            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable { ouvrir(m.id) }) {
                Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("${m.date.split("-").reversed().joinToString("/")} ${m.heure} · ${m.domicile} - ${m.exterieur}", fontSize = 12.sp)
                        Text(mk?.libelle ?: code, fontWeight = FontWeight.Bold, color = Or)
                        Text("Probabilité ${pct(mk?.proba)} · historique ${pct(mk?.confiance?.taux_historique)} " +
                            "sur ${mk?.confiance?.n_historique ?: 0}", fontSize = 12.sp)
                    }
                    val cj = Jumeau.depuisAncien(code)
                    val dejaLa = etat.combi.any { it.matchId == m.id && it.code == cj }
                    BoutonSelection(if (dejaLa) "Ajouté" else "Ajouter", vm.proba(m.id, cj) ?: mk?.proba, dejaLa,
                        Modifier.width(88.dp)) { vm.basculer(m, cj, mk?.libelle ?: cj) }
                }
            }
        }
    }
}

@Composable
fun EcranExperts(etat: EtatApp) {
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 12.dp, bottom = 100.dp)) {
        item {
            Text("Pronostiqueurs", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("Classement selon la valeur obtenue contre la cote de clôture (CLV), seul indicateur " +
                "de talent qui se confirme dans le temps. Le profit et le taux de réussite ne sont pas " +
                "utilisés : ils dépendent trop du hasard. Un pronostiqueur n'influence le moteur qu'après " +
                "50 pronostics et une preuve statistique (t-score ≥ 2).", fontSize = 12.sp)
            Spacer(Modifier.height(10.dp))
            if (etat.experts.isEmpty()) Text("Aucun pronostiqueur enregistré (ou serveur injoignable).")
        }
        items(etat.experts, key = { it.nom }) { e ->
            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Column(Modifier.padding(12.dp)) {
                    Text(e.nom, fontWeight = FontWeight.Bold)
                    Text(e.statut, color = if (e.ajustement > 0) Vert else Or, fontSize = 13.sp)
                    Text("${e.n} pronostics · CLV moyen ${signe(e.clv_moyen)} · t-score ${"%.2f".format(e.t_score)}" +
                        " · battent la clôture : ${pct(e.pct_battu, 0)}", fontSize = 12.sp)
                    Text("Effet sur les probabilités : ${signe(e.ajustement)}", fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
fun EcranReglages(vm: AppViewModel, etat: EtatApp) {
    var url by remember { mutableStateOf(vm.depot.urlApi) }
    Column(Modifier.padding(16.dp)) {
        Text("Réglages", fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(url, { url = it }, label = { Text("Adresse des pronostics (fichier .json publié ou serveur)") },
            singleLine = true, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        Button(onClick = { vm.depot.urlApi = url; vm.charger() }) { Text("Enregistrer et recharger") }
        Spacer(Modifier.height(8.dp))
        Text(if (etat.horsLigne) "État : hors ligne (données de démonstration)${etat.erreur?.let { " — $it" } ?: ""}"
            else "État : connecté — pronostics générés le ${etat.pronostics.genere_le}", fontSize = 12.sp)
        Spacer(Modifier.height(20.dp))
        Text("Jeu responsable", fontWeight = FontWeight.Bold, color = Or)
        Text("Les pronostics sont des probabilités, jamais des certitudes. Ne misez que ce que vous " +
            "pouvez perdre. Interdit aux mineurs. Besoin d'aide : Joueurs Info Service 09 74 75 13 13.",
            fontSize = 12.sp)
    }
}
