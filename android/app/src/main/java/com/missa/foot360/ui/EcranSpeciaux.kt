package com.missa.foot360.ui

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.data.TicketSpecial

/** Tickets préparés et publiés par l'équipe MISSA FOOT 360. */
@Composable
fun EcranTicketsSpeciaux(etat: EtatApp, vm: AppViewModel) {
    val liste = etat.pronostics.tickets_speciaux
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 110.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Surtitre("Sélection de l'équipe")
            Text("Tickets spéciaux", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("Des tickets préparés par l'équipe MISSA FOOT 360. Les chances affichées sont recalculées par le moteur.",
                fontSize = 12.sp, color = Discret)
        }
        if (liste.isEmpty()) item {
            Carte { Text("Aucun ticket spécial pour le moment. Revenez bientôt : ils apparaissent ici dès leur publication.",
                Modifier.padding(14.dp), fontSize = 13.sp, color = Discret) }
        }
        itemsIndexed(liste, key = { _, t -> t.id }) { rang, t ->
            androidx.compose.foundation.layout.Box(Modifier.apparition(rang)) { CarteTicketSpecial(t, etat, vm, detaille = true) }
        }
    }
}

@Composable
fun CarteTicketSpecial(t: TicketSpecial, etat: EtatApp, vm: AppViewModel, detaille: Boolean = false) {
    val p = vm.probaSpeciale(t)
    val coteTotale = t.selections.mapNotNull { it.cote }.takeIf { it.size == t.selections.size && it.isNotEmpty() }
        ?.fold(1.0) { a, b -> a * b }
    val dejaCopie = t.selections.isNotEmpty() && t.selections.all { s -> etat.combi.any { it.matchId == s.match_id && it.code == s.code } }
    Carte(accent = true) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Surtitre("★ Ticket spécial", Or)
                    Text(t.titre, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    Text(listOf(t.auteur, t.publie_le.take(10).let { jourMois(it) }).filter { it.isNotBlank() }.joinToString(" · "),
                        fontSize = 11.sp, color = Discret)
                }
                Column(horizontalAlignment = Alignment.End) {
                    if (p != null) PourcentageAnime(p, dec = 1, taille = 22.sp, couleur = couleurProba(p))
                    coteTotale?.let { Text("cote ${cote(it)}", fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }
                }
            }
            if (t.description.isNotBlank()) Text(t.description, fontSize = 12.sp, color = Discret)
            t.selections.forEach { s ->
                val m = s.match_id?.let { etat.matchs[it] }
                val ps = m?.let { vm.proba(it.id, s.code) }
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 2.dp)) {
                    LogoEquipe(m?.domicile ?: s.domicile, etat.pronostics.logos[m?.domicile ?: s.domicile], 18.dp)
                    Spacer(Modifier.width(4.dp))
                    LogoEquipe(m?.exterieur ?: s.exterieur, etat.pronostics.logos[m?.exterieur ?: s.exterieur], 18.dp)
                    Spacer(Modifier.width(8.dp))
                    Column(Modifier.weight(1f)) {
                        Text("${m?.domicile ?: s.domicile} – ${m?.exterieur ?: s.exterieur}", fontSize = 12.sp,
                            maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(s.libelle.ifBlank { vm.libelleComplet(s.code) }, fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
                            color = Vert, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                    Column(horizontalAlignment = Alignment.End) {
                        s.cote?.let { Text(cote(it), fontSize = 12.sp, fontWeight = FontWeight.Bold) }
                        Text(if (m == null) "terminé" else pct(ps, 0), fontSize = 10.sp, color = Discret)
                    }
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { vm.copierSpecial(t) }, enabled = !dejaCopie && vm.jambesSpeciales(t).isNotEmpty(),
                    modifier = Modifier.weight(1f)) { Text(if (dejaCopie) "✓ Dans mon ticket" else "Copier dans mon ticket", fontSize = 13.sp) }
            }
        }
    }
}

/** Nous contacter : coordonnées publiées dans data/config_app.json (modifiables sans mise à jour). */
@Composable
fun EcranContact(etat: EtatApp) {
    val c = etat.pronostics.config.contact
    val uri = LocalUriHandler.current
    val contexte = LocalContext.current
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Surtitre("Assistance")
        Text("Nous contacter", fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text(c.message.ifBlank { "Une question, une suggestion, un problème ? Écrivez-nous." }, fontSize = 13.sp, color = Discret)
        val canaux = listOfNotNull(
            c.whatsapp.takeIf { it.isNotBlank() }?.let { Triple("WhatsApp", it, "https://wa.me/" + it.filter { ch -> ch.isDigit() }) },
            c.telegram.takeIf { it.isNotBlank() }?.let { Triple("Telegram", it, "https://t.me/" + it.removePrefix("@")) },
            c.email.takeIf { it.isNotBlank() }?.let { Triple("E-mail", it, "mailto:$it?subject=MISSA%20FOOT%20360") },
            c.facebook.takeIf { it.isNotBlank() }?.let { Triple("Facebook", it, if (it.startsWith("http")) it else "https://facebook.com/$it") },
        )
        if (canaux.isEmpty()) Carte { Text("Les coordonnées seront bientôt disponibles ici.", Modifier.padding(14.dp), fontSize = 13.sp) }
        canaux.forEachIndexed { i, (nom, valeur, lien) ->
            Carte(Modifier.apparition(i), onClick = { runCatching { uri.openUri(lien) } }) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(when (nom) { "WhatsApp" -> "💬"; "Telegram" -> "✈️"; "E-mail" -> "✉️"; else -> "👍" }, fontSize = 22.sp)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(nom, fontWeight = FontWeight.Bold)
                        Text(valeur, fontSize = 12.sp, color = Discret)
                    }
                    Text("›", fontSize = 22.sp, color = Vert)
                }
            }
        }
        etat.pronostics.config.lien_telechargement.takeIf { it.isNotBlank() }?.let { lien ->
            OutlinedButton(onClick = {
                contexte.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain")
                    .putExtra(Intent.EXTRA_TEXT, "Découvre MISSA FOOT 360, l'analyse football intelligente : $lien"), "Partager l'application"))
            }, modifier = Modifier.fillMaxWidth()) { Text("Partager l'application avec un ami") }
        }
    }
}

/** Ouvre le menu de partage d'Android avec le texte donné. */
fun partager(contexte: android.content.Context, texte: String) {
    contexte.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain")
        .putExtra(Intent.EXTRA_TEXT, texte), "Partager le ticket"))
}

