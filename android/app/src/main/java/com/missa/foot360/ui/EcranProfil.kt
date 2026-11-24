package com.missa.foot360.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Profil : historique des tickets (vérifiés automatiquement), experts, réglages. */
@Composable
fun EcranProfil(etat: EtatApp, vm: AppViewModel, aller: (String) -> Unit) {
    val res = etat.pronostics.resultats
    val statuts = etat.tickets.map { statutTicket(it, res) }
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 110.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            Surtitre("Mon compte")
            Text("Mon profil", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Row(Modifier.padding(top = 6.dp)) {
                listOf("Réglages" to "reglages", "Experts" to "experts", "Conseils" to "conseils").forEach { (t, r) ->
                    Carte(Modifier.weight(1f).padding(end = 6.dp), onClick = { aller(r) }) {
                        Text(t, Modifier.padding(12.dp), fontWeight = FontWeight.SemiBold, color = Vert)
                    }
                }
            }
        }
        item {
            EnTete("Historique des tickets")
            val joues = statuts.count { it == Statut.GAGNE || it == Statut.PERDU }
            if (joues > 0) {
                val gagnes = statuts.count { it == Statut.GAGNE }
                val annonce = etat.tickets.zip(statuts).filter { it.second == Statut.GAGNE || it.second == Statut.PERDU }
                    .map { it.first.proba }.average()
                Text("$gagnes gagné(s) sur $joues vérifié(s) · réussite ${pct(gagnes.toDouble() / joues, 0)} " +
                    "(attendu d'après les probabilités : ${pct(annonce, 0)})", fontSize = 12.sp)
            }
            if (etat.tickets.isEmpty()) Text("Aucun ticket enregistré. Dans « Ticket », touchez « Enregistrer le ticket ».", fontSize = 12.sp)
        }
        items(etat.tickets.zip(statuts), key = { it.first.id }) { (t, s) ->
            val couleur = when (s) { Statut.GAGNE -> Vert; Statut.PERDU -> Rouge; else -> Or }
            Carte {
                Column(Modifier.padding(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Pastille(s.libelle, couleur, taille = 10.sp)
                        Text("  ${t.date.take(16).replace('T', ' ')} · ${t.jambes.size} sélection(s)", fontSize = 11.sp, modifier = Modifier.weight(1f))
                        IconButton(onClick = { vm.supprimerTicket(t.id) }) { Icon(Icons.Default.Delete, "Supprimer") }
                    }
                    Text("Chances annoncées ${pct(t.proba, 1)}" + (t.cote?.let { " · cote ${cote(it)}" } ?: "") +
                        (t.mise?.let { m -> " · mise ${montant(m)}" + (t.cote?.let { " → ${montant(m * it)}" } ?: "") } ?: ""),
                        fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    t.jambes.forEach { j ->
                        val sj = statutSelection(j.code, res[j.matchId])
                        val score = res[j.matchId]?.joinToString("-")
                        Text("${when (sj) { Statut.GAGNE -> "✓"; Statut.PERDU -> "✗"; else -> "•" }} ${j.libelleMatch}${score?.let { " ($it)" } ?: ""} : ${j.libelle}",
                            fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                            color = when (sj) { Statut.GAGNE -> Vert; Statut.PERDU -> Rouge; else -> couleurs.onSurface })
                    }
                }
            }
        }
    }
}
