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
            Text((if (etat.unParMatch) "Ticket" else "Combiné libre") + " : ${etat.combi.size} sélection(s)" +
                (r.coteBookmaker?.let { c -> etat.mise?.let { m -> " · gain ${montant(m * c * (1 + etat.bonus))}" } } ?: ""),
                fontSize = 12.sp, maxLines = 1)
            if (r.proba == 0.0) Text("Sélections incompatibles (probabilité nulle)",
                fontWeight = FontWeight.Bold, color = Rouge)
            else Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Réussite ", fontWeight = FontWeight.Bold, color = Vert)
                PourcentageAnime(r.proba, dec = 1, taille = 16.sp, couleur = couleurProba(r.proba))
                Text("  ·  " + (r.coteBookmaker?.let { c -> "cote ${cote(c)}" } ?: "cote juste ${cote(r.coteJuste)}"), fontWeight = FontWeight.Bold, color = Vert,
                    maxLines = 1, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
            }
            if (r.proba > 0) BarreProba(r.proba, Modifier.padding(top = 4.dp), couleurProba(r.proba), 3.dp)
        }
        Text("Voir ›", color = Or)
    }
}

@Composable
fun EcranCombi(etat: EtatApp, vm: AppViewModel, aller: (String) -> Unit = {}) {
    val r = etat.resultat
    LazyColumn(contentPadding = PaddingValues(16.dp)) {
        item {
            Surtitre("Combiné & valeur")
            Text(if (etat.unParMatch) "Mon ticket" else "Mon combiné (analyse libre)", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
        }
        if (etat.combi.isEmpty()) item {
            Text("Votre ticket est vide. Touchez une sélection dans « Accueil » ou « Analyses », ou laissez le moteur " +
                "en proposer un.", fontSize = 13.sp)
            Spacer(Modifier.height(10.dp))
            Button(onClick = { aller("assistant") }, modifier = Modifier.fillMaxWidth()) { Text("Générer un ticket automatiquement") }
        }
        // --- Résumé en haut : visible immédiatement, mis à jour en temps réel ---
        if (r != null) item {
            Carte(accent = true) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    val (niv, coul) = risque(r.proba)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("Chances de réussite", fontWeight = FontWeight.Bold)
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("${etat.combi.size} sélection(s)  ", fontSize = 12.sp, color = Discret)
                                Pastille("Risque ${niv.lowercase()}", coul, taille = 10.sp)
                            }
                        }
                        PourcentageAnime(r.proba, dec = 1, taille = 30.sp, couleur = couleurProba(r.proba))
                    }
                    BarreProba(r.proba, couleur = couleurProba(r.proba), hauteur = 6.dp)
                    Text("Sur 100 tickets identiques, environ ${"%.0f".format(r.proba * 100)} seraient gagnants.", fontSize = 12.sp)
                    Ligne("Cote totale du ticket", cote(r.coteBookmaker))
                    Ligne("Cote juste (équitable)", cote(r.coteJuste))
                    val manquantes = etat.combi.count { it.cote == null }
                    if (manquantes > 0) Text("$manquantes cote(s) à saisir pour calculer la cote totale et les gains.",
                        fontSize = 12.sp, color = Or)
                    var mise by remember { mutableStateOf(etat.mise?.let { "%.0f".format(it) } ?: "") }
                    OutlinedTextField(
                        value = mise, singleLine = true, modifier = Modifier.fillMaxWidth(),
                        label = { Text("Mise") }, suffix = { if (devise.isNotEmpty()) Text(devise) },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        onValueChange = { mise = it; vm.modifierMise(it.replace(',', '.').toDoubleOrNull()) },
                    )
                    val m = etat.mise
                    if (m != null && r.coteBookmaker != null) {
                        val gain = m * r.coteBookmaker * (1 + etat.bonus)
                        Ligne("Gain potentiel (si gagné)", montant(gain), Vert)
                        Ligne("Gain moyen attendu", (if (gain * r.proba - m >= 0) "+" else "") + montant(gain * r.proba - m),
                            if (gain * r.proba - m >= 0) Vert else Rouge)
                    }
                    r.valeurAttendue?.let { Ligne("Valeur du ticket", signe(it), if (it > 0) Vert else Rouge) }
                    if (r.proba < 0.05 && r.proba > 0) Text("Ticket très improbable (moins de 1 chance sur 20).",
                        fontSize = 12.sp, color = Rouge)
                    if (r.proba == 0.0) Text("Sélections incompatibles entre elles.", fontSize = 12.sp, color = Rouge)
                    if (r.valeurAttendue != null && r.valeurAttendue < 0) Text("Valeur négative : à long terme, " +
                        "ce type de ticket fait perdre de l'argent.", fontSize = 12.sp, color = Rouge)
                    if (!r.memeMatch && etat.combi.size > 1) Text("D'un match à l'autre, les probabilités se multiplient ; " +
                        "sur un même match, les sélections sont combinées avec leurs corrélations exactes.", fontSize = 11.sp, color = Discret)
                    if (r.memeMatch) Text("Analyse libre : plusieurs sélections sur un même match (corrélation prise " +
                        "en compte). Ce ticket ne serait PAS accepté tel quel par un bookmaker.", fontSize = 12.sp, color = Rouge)
                }
            }
            Spacer(Modifier.height(8.dp))
            // Mise recommandée (Kelly fractionnaire) : nulle si le ticket a une valeur négative
            r.coteBookmaker?.let { c ->
                val k = kelly(r.proba, c)
                Carte {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Surtitre("Mise recommandée (Kelly)")
                        Text(if (k > 0) "Ce ticket a une valeur positive : misez au plus ${pct(k, 1)} de votre capital de jeu" + "."
                             else "Valeur négative : le moteur ne recommande aucune mise sur ce ticket. Jouez-le seulement pour le plaisir, avec une petite somme.",
                            fontSize = 12.sp, color = if (k > 0) Vert else Discret)
                        Text("Calcul : quart de Kelly, plafonné à 5 % du capital. Ne poursuivez jamais une perte.", fontSize = 10.sp, color = Discret)
                    }
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Sélections (${etat.combi.size})", fontSize = 17.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                androidx.compose.material3.OutlinedButton(onClick = { vm.enregistrerTicket() },
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)) { Text("✓ Enregistrer", fontSize = 12.sp) }
                Spacer(Modifier.width(6.dp))
                val ctx = androidx.compose.ui.platform.LocalContext.current
                androidx.compose.material3.OutlinedButton(onClick = { partager(ctx, vm.texteTicket()) },
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)) { Text("Partager", fontSize = 12.sp) }
                Spacer(Modifier.width(6.dp))
                androidx.compose.material3.OutlinedButton(onClick = { vm.vider() },
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)) { Text("Vider", fontSize = 12.sp, color = Rouge) }
            }
            Text("Cotes préremplies avec la meilleure cote du marché quand elle est connue : remplacez-les par celles de " +
                "votre bookmaker (maximum ${com.missa.foot360.moteur.RegleTicket.MAX_SELECTIONS} sélections).",
                fontSize = 11.sp, color = Discret)
        }
        itemsIndexed(etat.combi) { i, s ->
            Carte(Modifier.padding(vertical = 4.dp).apparition(i)) {
                Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    val mm = etat.matchs[s.matchId]
                    if (mm != null) {
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            LogoEquipe(mm.domicile, etat.pronostics.logos[mm.domicile], 20.dp)
                            LogoEquipe(mm.exterieur, etat.pronostics.logos[mm.exterieur], 20.dp)
                        }
                        Spacer(Modifier.width(8.dp))
                    }
                    Column(Modifier.weight(1f)) {
                        if (mm != null) Text("${jourMois(mm.date)} ${mm.heure}", fontSize = 10.sp, color = Or)
                        Text(s.libelleMatch, fontSize = 12.sp)
                        Text(s.libelle, fontWeight = FontWeight.Bold)
                        val p = vm.proba(s.matchId, s.code)
                        Text("Probabilité seule : ${pct(p)} · cote juste ${cote(p?.let { if (it > 0) 1 / it else null })}",
                            fontSize = 12.sp, color = Vert)
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
            Spacer(Modifier.height(8.dp))
            var bonus by remember { mutableStateOf(if (etat.bonus > 0) "%.0f".format(etat.bonus * 100) else "") }
            OutlinedTextField(
                value = bonus, singleLine = true, modifier = Modifier.fillMaxWidth(),
                label = { Text("Bonus de gains du bookmaker sur ce ticket (%)") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                onValueChange = {
                    bonus = it
                    vm.modifierBonus((it.replace(',', '.').toDoubleOrNull() ?: 0.0) / 100)
                },
            )
            val hors = com.missa.foot360.moteur.RegleTicket.horsBonus(etat.combi) { j ->
                vm.proba(j.matchId, j.code)?.let { if (it > 0) 1 / it else null } }
            if (hors.isNotEmpty()) Text("${hors.size} sélection(s) à moins de 1,10 : en général non prise(s) en " +
                "compte pour le bonus de gains.", fontSize = 12.sp, color = Or)
            if (r.probaParMatch.size > 1) {
                Spacer(Modifier.height(8.dp))
                Text("Détail par match", fontWeight = FontWeight.Bold)
                r.probaParMatch.forEach { (id, p) ->
                    val mm = etat.matchs[id]
                    Ligne("${mm?.domicile ?: id} - ${mm?.exterieur ?: ""}", pct(p))
                }
            }
            Spacer(Modifier.height(10.dp))
            Carte {
                Column(Modifier.padding(12.dp)) {
                    Surtitre("Conseil du moteur")
                    val faible = etat.combi.mapNotNull { j -> vm.proba(j.matchId, j.code)?.let { j to it } }.minByOrNull { it.second }
                    Text(buildString {
                        if (faible != null && etat.combi.size > 1)
                            append("Sélection la plus fragile : ${faible.first.libelleMatch} (${pct(faible.second, 0)}). Retirez-la pour faire passer le ticket à ${pct(r.proba / faible.second, 0)}. ")
                        append("Chaque sélection ajoutée multiplie le risque. Vérifiez les dernières informations (compositions, absences) avant de jouer.")
                    }, fontSize = 12.sp)
                }
            }
            Spacer(Modifier.height(10.dp))
            Button(onClick = { vm.enregistrerTicket() }, modifier = Modifier.fillMaxWidth()) { Text("Enregistrer le ticket") }
        }
    }
}

/** Quart de Kelly plafonné à 5 % : part du capital à miser ; 0 si la valeur est négative. */
fun kelly(p: Double, c: Double): Double =
    if (c <= 1.0) 0.0 else (((p * c - 1) / (c - 1)) / 4).coerceIn(0.0, 0.05)

@Composable
private fun Ligne(titre: String, valeur: String, couleur: androidx.compose.ui.graphics.Color = MaterialTheme.colorScheme.onSurface) {
    Row { Text(titre, Modifier.weight(1f)); Text(valeur, fontWeight = FontWeight.Bold, color = couleur) }
}
