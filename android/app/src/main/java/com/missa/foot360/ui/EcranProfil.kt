package com.missa.foot360.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Groups
import androidx.compose.material.icons.filled.HealthAndSafety
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.SupportAgent
import androidx.compose.material.icons.filled.WorkspacePremium
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.BuildConfig

/** Mon compte : menu (tickets spéciaux, réglages, contact…) et historique des tickets vérifiés. */
@Composable
fun EcranProfil(etat: EtatApp, vm: AppViewModel, aller: (String) -> Unit) {
    val res = etat.pronostics.resultats
    val statuts = etat.tickets.map { statutTicket(it, res) }
    val joues = statuts.count { it == Statut.GAGNE || it == Statut.PERDU }
    val gagnes = statuts.count { it == Statut.GAGNE }
    val contexte = LocalContext.current
    val lien = etat.pronostics.config.lien_telechargement
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 110.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            Carte(Modifier.apparition(), accent = true) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(52.dp).clip(CircleShape).background(VertFonce), contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.Person, null, tint = Vert, modifier = Modifier.size(30.dp))
                    }
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Surtitre("Mon compte")
                        Text("Parieur MISSA", fontWeight = FontWeight.Bold, fontSize = 17.sp)
                        Text("${etat.tickets.size} ticket(s) enregistré(s)" +
                            (if (joues > 0) " · $gagnes gagné(s) sur $joues" else ""), fontSize = 12.sp, color = Discret)
                    }
                }
            }
        }
        item {
            Carte(Modifier.apparition(1)) {
                val entrees = listOf(
                    Triple(Icons.Default.WorkspacePremium, "Tickets spéciaux", "speciaux"),
                    Triple(Icons.Default.Settings, "Réglages", "reglages"),
                    Triple(Icons.Default.SupportAgent, "Nous contacter", "contact"),
                    Triple(Icons.Default.Lightbulb, "Conseils et paris value", "conseils"),
                    Triple(Icons.Default.Groups, "Experts suivis", "experts"),
                    Triple(Icons.Default.Share, "Partager l'application", "partager"),
                )
                entrees.forEachIndexed { i, (icone, titre, cible) ->
                    if (i > 0) HorizontalDivider(color = Bord)
                    EntreeMenu(icone, titre, when (cible) {
                        "speciaux" -> etat.pronostics.tickets_speciaux.size.takeIf { it > 0 }?.let { "$it disponible(s)" }
                        else -> null
                    }) {
                        if (cible == "partager") partager(contexte, "Découvre MISSA FOOT 360, l'analyse football intelligente" +
                            (if (lien.isNotBlank()) " : $lien" else " !"))
                        else aller(cible)
                    }
                }
            }
        }
        item {
            EnTete("Historique des tickets")
            if (joues > 0) {
                val annonce = etat.tickets.zip(statuts).filter { it.second == Statut.GAGNE || it.second == Statut.PERDU }
                    .map { it.first.proba }.average()
                Text("$gagnes gagné(s) sur $joues vérifié(s) · réussite ${pct(gagnes.toDouble() / joues, 0)} " +
                    "(attendu d'après les probabilités : ${pct(annonce, 0)})", fontSize = 12.sp, color = Discret)
            }
            if (etat.tickets.isEmpty()) Text("Aucun ticket enregistré. Dans « Ticket », touchez « Enregistrer ».",
                fontSize = 12.sp, color = Discret)
        }
        itemsIndexed(etat.tickets.zip(statuts), key = { _, it -> it.first.id }) { rang, (t, s) ->
            val couleur = when (s) { Statut.GAGNE -> Vert; Statut.PERDU -> Rouge; else -> Or }
            Carte(Modifier.apparition(rang + 2)) {
                Column(Modifier.padding(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Pastille(s.libelle, couleur, taille = 10.sp)
                        Text("  ${t.date.take(16).replace('T', ' ')} · ${t.jambes.size} sélection(s)", fontSize = 11.sp,
                            color = Discret, modifier = Modifier.weight(1f))
                        IconButton(onClick = { vm.supprimerTicket(t.id) }) { Icon(Icons.Default.Delete, "Supprimer", tint = Discret) }
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
        item {
            Row(Modifier.padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.HealthAndSafety, null, tint = Or, modifier = Modifier.size(16.dp))
                Text("  Jeu responsable : ne misez que ce que vous pouvez perdre. 18+.", fontSize = 11.sp, color = Discret)
            }
            Text("MISSA FOOT 360 · version ${BuildConfig.VERSION_NAME}", fontSize = 10.sp, color = Discret,
                modifier = Modifier.padding(top = 4.dp))
        }
    }
}

@Composable
private fun EntreeMenu(icone: ImageVector, titre: String, badge: String?, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).padding(horizontal = 14.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(34.dp).clip(RoundedCornerShape(9.dp)).background(VertFonce), contentAlignment = Alignment.Center) {
            Icon(icone, null, tint = Vert, modifier = Modifier.size(20.dp))
        }
        Spacer(Modifier.width(12.dp))
        Text(titre, fontSize = 15.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f))
        if (badge != null) { Pastille(badge, Or, taille = 10.sp); Spacer(Modifier.width(6.dp)) }
        Text("›", fontSize = 20.sp, color = Discret)
    }
}
