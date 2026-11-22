package com.missa.foot360.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.missa.foot360.data.LigneStat

/** Statistiques : la preuve que le moteur fait ce qu'il annonce. */
@Composable
fun EcranStats(etat: EtatApp, aller: (String) -> Unit) {
    val st = etat.pronostics.stats_moteur
    val sp = etat.pronostics.suivi_pronostics
    LazyColumn(contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 110.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            Text("Performance du moteur", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text(st?.periode?.let { "Mesurée sur $it." } ?: "Statistiques indisponibles.", fontSize = 12.sp)
        }
        if (st != null) {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Réussite globale", Modifier.weight(1f), fontWeight = FontWeight.Bold)
                            PourcentageAnime(st.reussite_globale, dec = 1, taille = 26.sp, couleur = Vert)
                        }
                        BarreProba(st.reussite_globale, hauteur = 6.dp)
                        Row {
                            Chiffre("%,d".format(st.pronostics_evalues).replace(',', ' '), "évalués", Modifier.weight(1f))
                            Chiffre("%,d".format(st.reussis).replace(',', ' '), "corrects", Modifier.weight(1f))
                            Chiffre("%,d".format(st.pronostics_evalues - st.reussis).replace(',', ' '), "incorrects", Modifier.weight(1f))
                        }
                        Text("Probabilité annoncée en moyenne : ${pct(st.annonce_moyenne)} → réussite réelle : ${pct(st.reussite_globale)}. " +
                            "Quand les deux sont proches, les pourcentages de l'application sont fiables.", fontSize = 11.sp)
                    }
                }
            }
            item { EnTete("Réussite par type de pari") }
            items(st.par_type) { Ligne(it.type, it) }
            item { EnTete("Réussite par niveau de confiance") }
            items(st.par_niveau) { Ligne(it.niveau, it) }
            item { EnTete("Résultat 1X2 par championnat") }
            items(st.par_championnat) { l ->
                Row(Modifier.fillMaxWidth().padding(vertical = 2.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(l.championnat, fontSize = 13.sp, modifier = Modifier.weight(1f), maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text("${pct(l.reussite_1x2, 1)} sur ${l.n}", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
            if (st.combines.isNotEmpty()) {
                item {
                    EnTete("Tickets combinés (2 à 6 matchs)")
                    Text("Une réussite de 62 % par sélection ne veut pas dire 62 % des tickets gagnants : " +
                        "voici la réussite réelle des tickets selon la probabilité annoncée.", fontSize = 11.sp)
                }
                items(st.combines) { t ->
                    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
                        Text("Annoncés ${pct(t.de, 0)}–${pct(minOf(t.a, 1.0), 0)}", fontSize = 13.sp, modifier = Modifier.weight(1f))
                        Text("réels ${pct(t.reel, 1)} (${t.n})", fontSize = 12.sp, fontWeight = FontWeight.Bold,
                            color = if (kotlin.math.abs(t.reel - t.annonce) < 0.03) Vert else Or)
                    }
                }
            }
        }
        if (sp != null) item {
            EnTete("En conditions réelles (pronostics publiés)")
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Pronostic principal : ${sp.principal.regles} joués / ${sp.principal.publies} publiés" +
                        (sp.principal.reussite?.let { " · réussite ${pct(it, 0)} (annoncé ${pct(sp.principal.annonce, 0)})" } ?: ""), fontSize = 12.sp)
                    Text("Haute confiance : ${sp.confiance.regles} joués / ${sp.confiance.publies} publiés" +
                        (sp.confiance.reussite?.let { " · réussite ${pct(it, 0)} (annoncé ${pct(sp.confiance.annonce, 0)})" } ?: ""), fontSize = 12.sp)
                    if (sp.derniers.isEmpty()) Text("Les résultats s'afficheront ici après les matchs.", fontSize = 11.sp)
                    sp.derniers.take(10).forEach { d ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Badge(if (d.gagne) "✓" else "✗", if (d.gagne) Vert else Rouge)
                            Text("  ${d.domicile} ${d.score} ${d.exterieur} · ${d.libelle} (${pct(d.proba, 0)})", fontSize = 11.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                }
            }
        }
        etat.pronostics.suivi_value?.let { v ->
            item {
                EnTete("Paris value", "Voir →") { aller("conseils") }
                Text("${v.publies} publiés · ${v.regles} joués" + (v.clv_moyen?.let { " · CLV moyen ${signe(it)}" } ?: "") +
                    (v.rendement?.let { " · rendement ${signe(it)}" } ?: ""), fontSize = 12.sp)
            }
        }
        item {
            Text("Une probabilité n'est jamais une garantie : même à 90 %, une sélection sur dix est perdante.",
                fontSize = 11.sp, color = Or, modifier = Modifier.padding(top = 8.dp))
        }
    }
}

@Composable
private fun Chiffre(v: String, t: String, modifier: Modifier) {
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(v, fontWeight = FontWeight.Bold, fontSize = 16.sp)
        Text(t, fontSize = 10.sp)
    }
}

@Composable
private fun Ligne(titre: String, l: LigneStat) {
    Column(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(titre, fontSize = 13.sp, modifier = Modifier.weight(1f))
            Text("annoncé ${pct(l.annonce, 0)} → ", fontSize = 11.sp)
            Text(pct(l.reussite, 1), fontSize = 13.sp, fontWeight = FontWeight.Bold, color = couleurProba(l.reussite ?: 0.0),
                modifier = Modifier.width(56.dp))
        }
        BarreProba(l.reussite ?: 0.0, couleur = couleurProba(l.reussite ?: 0.0), hauteur = 3.dp)
    }
}
