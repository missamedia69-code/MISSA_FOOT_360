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
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Barre fixe en bas de l'écran : probabilité du combiné mise à jour en temps réel. */
@Composable
fun BarreCombi(etat: EtatApp, ouvrir: () -> Unit) {
    val r = etat.resultat ?: return
    Row(
        Modifier.fillMaxWidth().background(VertFonce).clickable(onClick = ouvrir)
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text("Combiné : ${etat.combi.size} sélection(s)", fontSize = 12.sp)
            if (r.proba == 0.0) Text("Sélections incompatibles (probabilité nulle)",
                fontWeight = FontWeight.Bold, color = Rouge)
            else Text("Probabilité ${pct(r.proba, 2)}  ·  cote juste ${cote(r.coteJuste)}",
                fontWeight = FontWeight.Bold, color = Vert)
        }
        Text("Voir ›", color = Or)
    }
}

@Composable
fun EcranCombi(etat: EtatApp, vm: AppViewModel) {
    val r = etat.resultat
    LazyColumn(contentPadding = PaddingValues(16.dp)) {
        item {
            Text("Mon combiné", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(4.dp))
            Text("La probabilité est recalculée à chaque modification. Saisissez la cote de votre " +
                "bookmaker pour voir la valeur du combiné.", fontSize = 12.sp)
            Spacer(Modifier.height(12.dp))
        }
        if (etat.combi.isEmpty()) item { Text("Aucune sélection. Touchez un pronostic pour l'ajouter.") }
        itemsIndexed(etat.combi) { i, s ->
            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(s.libelleMatch, fontSize = 12.sp)
                        Text(s.libelle, fontWeight = FontWeight.Bold)
                        val p = vm.proba(s.matchId, s.code)
                        Text("Probabilité seule : ${pct(p)}", fontSize = 12.sp, color = Vert)
                    }
                    var texte by remember(s.matchId, s.code) { mutableStateOf(s.cote?.let { cote(it) } ?: "") }
                    OutlinedTextField(
                        value = texte, singleLine = true, label = { Text("Cote") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        onValueChange = {
                            texte = it
                            vm.modifierCote(i, it.replace(',', '.').toDoubleOrNull()?.takeIf { c -> c > 1.0 })
                        },
                        modifier = Modifier.width(90.dp),
                    )
                    IconButton(onClick = { vm.retirer(i) }) { Icon(Icons.Default.Close, "Retirer") }
                }
            }
        }
        if (r != null) item {
            Spacer(Modifier.height(12.dp))
            var bonus by remember { mutableStateOf(if (etat.bonus > 0) "%.0f".format(etat.bonus * 100) else "") }
            OutlinedTextField(
                value = bonus, singleLine = true, modifier = Modifier.fillMaxWidth(),
                label = { Text("Bonus de gains du bookmaker sur ce combiné (%)") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                onValueChange = {
                    bonus = it
                    vm.modifierBonus((it.replace(',', '.').toDoubleOrNull() ?: 0.0) / 100)
                },
            )
            Spacer(Modifier.height(12.dp))
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Ligne("Probabilité du combiné", pct(r.proba, 2), Vert)
                    Ligne("Cote juste (équitable)", cote(r.coteJuste))
                    Ligne("Cote du bookmaker", cote(r.coteBookmaker))
                    if (etat.bonus > 0) Ligne("Bonus inclus", "+${"%.0f".format(etat.bonus * 100)} %")
                    if (r.probaParMatch.size > 1) r.probaParMatch.forEach { (id, p) ->
                        val mm = etat.matchs[id]
                        Ligne("  ${mm?.domicile ?: id} - ${mm?.exterieur ?: ""}", pct(p))
                    }
                    r.valeurAttendue?.let {
                        Ligne("Valeur attendue", signe(it), if (it > 0) Vert else Rouge)
                    }
                    Text("Sur 100 combinés identiques, environ ${"%.0f".format(r.proba * 100)} seraient gagnants.",
                        fontSize = 12.sp)
                    if (r.memeMatch) Text("Plusieurs sélections sur un même match : la corrélation est prise " +
                        "en compte. Beaucoup de bookmakers refusent ou ajustent ces combinés.", fontSize = 12.sp, color = Or)
                    if (r.proba < 0.05 && r.proba > 0) Text("Combiné très improbable (moins de 1 chance sur 20).",
                        fontSize = 12.sp, color = Rouge)
                    if (r.proba == 0.0) Text("Sélections incompatibles entre elles.", fontSize = 12.sp, color = Rouge)
                    if (r.valeurAttendue != null && r.valeurAttendue < 0) Text("Valeur négative : à long terme, " +
                        "ce type de combiné fait perdre de l'argent.", fontSize = 12.sp, color = Rouge)
                }
            }
            Spacer(Modifier.height(12.dp))
            Button(onClick = { vm.vider() }, modifier = Modifier.fillMaxWidth()) { Text("Vider le combiné") }
        }
    }
}

@Composable
private fun Ligne(titre: String, valeur: String, couleur: androidx.compose.ui.graphics.Color = MaterialTheme.colorScheme.onSurface) {
    Row { Text(titre, Modifier.weight(1f)); Text(valeur, fontWeight = FontWeight.Bold, color = couleur) }
}
