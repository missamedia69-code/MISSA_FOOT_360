package com.missa.foot360.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
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
    val onglets = listOf("Aperçu", "Forme", "Face-à-face", "Scores exacts", "Compos & absences") + groupes
    val NB_ANALYSE = 5
    var onglet by remember { mutableIntStateOf(0) }
    var filtreMarche by remember { mutableStateOf("") }
    var voirModulation by remember { mutableStateOf(false) }
    val mod = etat.modulations[m.id] ?: Modulation()

    LazyColumn(contentPadding = PaddingValues(bottom = 110.dp)) {
        item {
            Column(Modifier.padding(16.dp)) {
                Surtitre("Analyse d'un match")
                Text("${m.domicile} – ${m.exterieur}", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                val nomChamp = etat.pronostics.championnats.firstOrNull { c -> c.matchs.any { it.id == m.id } }?.nom ?: ""
                Text("$nomChamp · ${jourLisible(m.date)} à ${m.heure}", color = Or, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(8.dp))
                val j = vm.jumeau(m.id)
                val bd = j?.let { (0 until it.matrice.size).sumOf { i -> i * it.matrice[i].sum() } }
                val be = j?.let { (0 until it.matrice.size).sumOf { k -> k * it.matrice.sumOf { r -> r[k] } } }
                FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    PuceInfo("Buts attendus", "${cote(bd)} – ${cote(be)}")
                    PuceInfo("Score probable", m.score_probable)
                    if (m.corners_attendus.size == 2) PuceInfo("Corners", m.corners_attendus.joinToString(" – ") { cote(it) })
                    if (m.cartons_attendus.size == 2) PuceInfo("Cartons", m.cartons_attendus.joinToString(" – ") { cote(it) })
                    if (m.methode.isNotEmpty()) PuceInfo("Méthode", m.methode)
                }
                Spacer(Modifier.height(6.dp))
                Text(if (etat.unParMatch)
                    "Touchez un pari pour l'ajouter au ticket (un par match ; plusieurs événements : onglet « Combinés officiels »)."
                else "Mode analyse libre : plusieurs options d'un même match = probabilité conjointe exacte " +
                    "(non jouable tel quel chez un bookmaker).",
                    fontSize = 11.sp, color = if (etat.unParMatch) Discret else Or)
                TextButton(onClick = { voirModulation = !voirModulation }) {
                    Text(if (mod.neutre) "⚙ Moduler le match (absences, forme, arbitre…)" else "⚙ Modulation active — modifier")
                }
                if (voirModulation) PanneauModulation(mod) { vm.moduler(m.id, it) }
            }
        }
        item {
            PrimaryScrollableTabRow(selectedTabIndex = onglet, edgePadding = 8.dp) {
                onglets.forEachIndexed { i, g -> Tab(selected = onglet == i, onClick = { onglet = i }, text = { Text(g) }) }
            }
        }
        when (onglet) {
            0 -> item { OngletApercu(m, etat, vm) }
            1 -> item { OngletForme(m) }
            2 -> item { OngletFaceAFace(m) }
            3 -> item { OngletScores(m, etat, vm) }
            4 -> item { OngletCompos() }
        }
        val groupe = if (onglet >= NB_ANALYSE) onglets[onglet] else null
        if (groupe != null) item {
            OutlinedTextField(filtreMarche, { filtreMarche = it }, singleLine = true,
                placeholder = { Text("Chercher un pari dans les ${etat.pronostics.catalogue.sumOf { it.options.size }} marchés…", fontSize = 13.sp) },
                leadingIcon = { Icon(Icons.Default.Search, null) },
                shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth().padding(start = 12.dp, end = 12.dp, top = 10.dp))
        }
        val f = filtreMarche.trim().lowercase()
        val blocs = etat.pronostics.catalogue.mapNotNull { gm ->
            if (groupe == null) return@mapNotNull null
            if (f.isEmpty()) gm.takeIf { it.groupe == groupe }
            else gm.copy(options = gm.options.filter { "${gm.titre} ${it.libelle}".lowercase().contains(f) }).takeIf { it.options.isNotEmpty() }
        }
        items(blocs) { gm ->
            Carte(Modifier.padding(horizontal = 12.dp, vertical = 5.dp)) {
                Row(Modifier.fillMaxWidth().padding(start = 12.dp, end = 12.dp, top = 10.dp, bottom = 4.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    Text(gm.titre, fontWeight = FontWeight.Bold, color = Vert, modifier = Modifier.weight(1f), fontSize = 14.sp)
                    Text("${gm.options.size} options", fontSize = 10.sp, color = Discret)
                }
                Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 2.dp)) {
                    listOf("SÉLECTION" to 1f, "PROBA" to .5f, "COTE JUSTE" to .5f, "RÉEL" to .4f).forEach { (t, w) ->
                        Text(t, fontSize = 9.sp, color = Discret, letterSpacing = 0.8.sp, modifier = Modifier.weight(w),
                            textAlign = if (w == 1f) androidx.compose.ui.text.style.TextAlign.Start else androidx.compose.ui.text.style.TextAlign.End)
                    }
                    Spacer(Modifier.width(34.dp))
                }
                gm.options.forEach { o ->
                    val p = vm.proba(m.id, o.code)
                    val sel = etat.combi.any { it.matchId == m.id && it.code == o.code }
                    val hist = p?.let { tauxHistorique(etat.pronostics.fiabilite, familleFiabilite(o.code), it) }
                    HorizontalDivider(color = Bord)
                    Row(Modifier.fillMaxWidth().background(if (sel) VertFonce else Color.Transparent)
                        .clickable { vm.basculer(m, o.code, "${gm.titre} : ${o.libelle}") }
                        .padding(horizontal = 12.dp, vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text(o.libelle, fontSize = 13.sp, modifier = Modifier.weight(1f),
                            fontWeight = if (sel) FontWeight.Bold else FontWeight.Normal)
                        PourcentageAnime(p, Modifier.weight(.5f), dec = 1, taille = 13.sp, couleur = couleurProba(p ?: 0.0),
                            alignement = androidx.compose.ui.text.style.TextAlign.End)
                        Text(cote(p?.let { if (it > 0) 1 / it else null }), fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
                            modifier = Modifier.weight(.5f), textAlign = androidx.compose.ui.text.style.TextAlign.End)
                        Text(if (hist != null && hist.n >= 100) pct(hist.reel, 0) else "—", fontSize = 12.sp, color = Discret,
                            modifier = Modifier.weight(.4f), textAlign = androidx.compose.ui.text.style.TextAlign.End)
                        Box(Modifier.padding(start = 8.dp).size(26.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(7.dp))
                            .background(if (sel) Vert else VertFonce), contentAlignment = Alignment.Center) {
                            Text(if (sel) "✓" else "+", color = if (sel) Color.Black else Vert, fontWeight = FontWeight.Bold)
                        }
                    }
                }
                Spacer(Modifier.height(4.dp))
            }
        }
        if (groupe != null && blocs.isEmpty()) item {
            Text("Aucun pari ne correspond à « $filtreMarche ».", fontSize = 13.sp, color = Discret, modifier = Modifier.padding(16.dp))
        }
        item {
            Column(Modifier.padding(16.dp)) {
                Text("Pronostiqueurs", fontWeight = FontWeight.Bold, color = Vert)
                if (m.pronostiqueurs.isEmpty()) Text("Aucun pronostic d'expert enregistré pour ce match.", fontSize = 12.sp)
                m.pronostiqueurs.forEach { a ->
                    Text("${a.pronostiqueur} : ${a.selection} @ ${cote(a.cote)} — ${a.statut} (effet ${signe(a.ajustement)})", fontSize = 12.sp)
                }
                Spacer(Modifier.height(8.dp))
                Text("« Réel » = part des sélections de ce type et de ce niveau de probabilité qui ont réellement " +
                    "gagné sur les saisons de test (jamais vues par le moteur). « Cote juste » = cote sans marge du bookmaker : " +
                    "une cote proposée plus haute est favorable.", fontSize = 11.sp, color = Discret)
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


// ----------------------------------------------------------------------------- onglets d'analyse
@Composable
private fun OngletApercu(m: Match, etat: EtatApp, vm: AppViewModel) {
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Probabilités des résultats", fontWeight = FontWeight.Bold, color = Vert)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("1" to "Victoire ${m.domicile}", "N" to "Match nul", "2" to "Victoire ${m.exterieur}").forEach { (c, t) ->
                val code = "1X2:$c"
                val p = vm.proba(m.id, code)
                Column(Modifier.weight(1f).clickable { vm.basculer(m, code, vm.libelleComplet(code)) },
                    horizontalAlignment = Alignment.CenterHorizontally) {
                    PourcentageAnime(p, taille = 24.sp, couleur = couleurProba(p ?: 0.0))
                    Text(t, fontSize = 11.sp, maxLines = 2, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                }
            }
        }
        Text("Marchés clés", fontWeight = FontWeight.Bold, color = Vert)
        listOf("DC:1N", "DC:N2", "OU:1.5:plus", "OU:2.5:plus", "OU:3.5:moins", "BTTS:oui").forEach { code ->
            val p = vm.proba(m.id, code) ?: return@forEach
            val (r, c) = risque(p)
            val sel = etat.combi.any { it.matchId == m.id && it.code == code }
            Row(Modifier.fillMaxWidth().clickable { vm.basculer(m, code, vm.libelleComplet(code)) }.padding(vertical = 3.dp),
                verticalAlignment = Alignment.CenterVertically) {
                Text((if (sel) "✓ " else "") + vm.libelleComplet(code).substringAfter(" : ").let {
                    "${vm.libelleComplet(code).substringBefore(" : ")} : $it" }, fontSize = 13.sp, modifier = Modifier.weight(1f),
                    maxLines = 1, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis,
                    fontWeight = if (sel) FontWeight.Bold else FontWeight.Normal)
                Text(r, fontSize = 11.sp, color = c, modifier = Modifier.padding(end = 8.dp))
                PourcentageAnime(p, taille = 14.sp, couleur = couleurProba(p))
            }
        }
        // Pourquoi ce pronostic ?
        val a = m.analyse
        Text("Pourquoi ce pronostic ?", fontWeight = FontWeight.Bold, color = Vert)
        val noms = mapOf("marche_ouv" to "Cotes du marché (consensus des bookmakers, marge retirée)",
            "dixon_coles" to "Modèle des buts (attaque/défense sur 3 saisons)", "elo" to "Classement Elo (résultats récents)")
        a.sources.forEach { (k, v) ->
            if (v.size == 3) {
                Text(noms[k] ?: k, fontSize = 12.sp)
                RepartitionBarre(v)
            }
        }
        if (a.final.size == 3) {
            Text("Pronostic final (sources pondérées selon leur précision passée)", fontSize = 12.sp, fontWeight = FontWeight.Bold)
            RepartitionBarre(a.final)
        }
        Text("Le marché pèse le plus lourd : sur 5 700 matchs de test, c'est la source la plus précise. " +
            "Les buts attendus ${m.buts_attendus.joinToString(" – ") { cote(it) }} servent à calculer les scores, " +
            "les mi-temps et tous les autres paris.", fontSize = 11.sp)
    }
}

@Composable
private fun RepartitionBarre(p: List<Double>) {
    Row(Modifier.fillMaxWidth().height(18.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(4.dp))) {
        listOf(Vert to p[0], Color(0xFF8A9A90) to p[1], Or to p[2]).forEach { (c, v) ->
            if (v > 0.01) Box(Modifier.weight(v.toFloat()).fillMaxHeight().background(c), contentAlignment = Alignment.Center) {
                if (v > 0.12) Text(pct(v, 0), fontSize = 10.sp, color = Color.Black, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun OngletForme(m: Match) {
    val a = m.analyse
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        if (a.forme_dom.isEmpty() && a.forme_ext.isEmpty())
            Text("Pas d'historique disponible pour cette compétition (coupes, sélections…).", fontSize = 12.sp)
        listOf(Triple(m.domicile, a.forme_dom, a.stats_dom), Triple(m.exterieur, a.forme_ext, a.stats_ext)).forEach { (eq, f, st) ->
            if (f.isEmpty()) return@forEach
            Text(eq, fontWeight = FontWeight.Bold, color = Vert)
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                f.forEach { x -> Badge(x.res, when (x.res) { "V" -> Vert; "N" -> Color(0xFF8A9A90); else -> Rouge }) }
                Text("  (du plus récent au plus ancien)", fontSize = 10.sp)
            }
            f.forEach { x ->
                Text("${x.date.drop(5).split("-").reversed().joinToString("/")} · ${if (x.lieu == "dom") "vs" else "à"} ${x.adversaire} : ${x.score}",
                    fontSize = 12.sp)
            }
            st?.let {
                Text("Sur ${it.matchs} matchs : ${cote(it.buts_marques)} but(s) marqué(s) et ${cote(it.buts_encaisses)} encaissé(s) par match · " +
                    "plus de 2,5 buts ${pct(it.plus_2_5, 0)} · les deux marquent ${pct(it.btts, 0)} · cage inviolée ${pct(it.clean_sheets, 0)}",
                    fontSize = 11.sp)
                Text("${it.lieu.type.replaceFirstChar { c -> c.uppercase() }} (10 derniers) : ${it.lieu.v} V · ${it.lieu.n} N · ${it.lieu.d} D",
                    fontSize = 11.sp)
            }
        }
    }
}

@Composable
private fun OngletFaceAFace(m: Match) {
    val c = m.analyse.confrontations
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("Dernières confrontations", fontWeight = FontWeight.Bold, color = Vert)
        if (c.isEmpty()) Text("Aucune confrontation dans l'historique disponible (3 dernières saisons).", fontSize = 12.sp)
        c.forEach { x ->
            Row {
                Text(x.date.split("-").reversed().joinToString("/"), fontSize = 12.sp, modifier = Modifier.width(84.dp))
                Text("${x.domicile} ${x.score} ${x.exterieur}", fontSize = 13.sp)
            }
        }
        if (c.isNotEmpty()) Text("Les confrontations directes sont peu nombreuses : le moteur leur donne peu de poids, " +
            "les tendances récentes globales sont plus fiables.", fontSize = 11.sp)
    }
}

/** Scores exacts : les plus probables et la grille complète (domicile en lignes, extérieur en colonnes). */
@Composable
private fun OngletScores(m: Match, etat: EtatApp, vm: AppViewModel) {
    val mat = vm.jumeau(m.id)?.matrice ?: return
    val n = minOf(mat.size, 6)
    val tous = mat.indices.flatMap { i -> mat[i].indices.map { k -> Triple(i, k, mat[i][k]) } }.sortedByDescending { it.third }
    val max = tous.firstOrNull()?.third ?: 1.0
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("Scores les plus probables", fontWeight = FontWeight.Bold, color = Vert)
        tous.take(8).forEach { (i, k, p) ->
            val code = "CS:$i-$k"
            val existe = etat.pronostics.catalogue.any { g -> g.options.any { it.code == code } }
            val sel = etat.combi.any { it.matchId == m.id && it.code == code }
            Row(Modifier.fillMaxWidth().clip(androidx.compose.foundation.shape.RoundedCornerShape(6.dp))
                .background(if (sel) VertFonce else Color.Transparent)
                .let { if (existe) it.clickable { vm.basculer(m, code, vm.libelleComplet(code)) } else it }
                .padding(vertical = 3.dp, horizontal = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                Text("$i – $k", fontSize = 14.sp, fontWeight = FontWeight.Bold, modifier = Modifier.width(52.dp))
                Box(Modifier.weight(1f).height(10.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(5.dp))
                    .background(couleurs.surfaceVariant)) {
                    Box(Modifier.fillMaxWidth((p / max).toFloat()).height(10.dp).background(Vert.copy(alpha = 0.85f)))
                }
                Text(pct(p, 1), fontSize = 12.sp, modifier = Modifier.width(58.dp), textAlign = androidx.compose.ui.text.style.TextAlign.End)
                Text("cote ${cote(1 / p)}", fontSize = 11.sp, color = Discret, modifier = Modifier.width(72.dp),
                    textAlign = androidx.compose.ui.text.style.TextAlign.End)
            }
        }
        Spacer(Modifier.height(6.dp))
        Text("Grille des scores (${m.domicile} en lignes, ${m.exterieur} en colonnes)", fontWeight = FontWeight.Bold, color = Vert, fontSize = 13.sp)
        Row { Spacer(Modifier.width(26.dp)); (0 until n).forEach { k -> Text("$k", Modifier.weight(1f), fontSize = 11.sp, color = Discret,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center) } }
        (0 until n).forEach { i ->
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("$i", Modifier.width(26.dp), fontSize = 11.sp, color = Discret)
                (0 until n).forEach { k ->
                    val p = mat[i][k]
                    val a = (p / max).toFloat().coerceIn(0f, 1f)
                    Box(Modifier.weight(1f).padding(1.dp).height(30.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(4.dp))
                        .background(Vert.copy(alpha = 0.06f + 0.7f * a)), contentAlignment = Alignment.Center) {
                        Text(if (p >= 0.005) "%.0f".format(p * 100) else "·", fontSize = 10.sp,
                            color = if (a > 0.55f) Color.Black else couleurs.onSurface, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
        Text("Valeurs en %. Un score exact reste très incertain : même le plus probable dépasse rarement 15 %.",
            fontSize = 11.sp, color = Discret)
    }
}

@Composable
private fun OngletCompos() {
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("Compositions et absences", fontWeight = FontWeight.Bold, color = Vert)
        Text("Bientôt disponible : il faut brancher une source de données spécialisée (Sportmonks ou API-Football). " +
            "En attendant, si vous connaissez une absence importante, utilisez « Moduler le match » : par exemple, " +
            "buteur principal absent ≈ attaque −10 à −15 %.", fontSize = 12.sp)
        Text("Bon à savoir : les cotes du marché intègrent déjà la plupart des informations connues (blessures, " +
            "suspensions), donc le pronostic en tient en grande partie compte.", fontSize = 11.sp)
    }
}
