package com.missa.foot360.ui

import androidx.compose.foundation.background
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.util.Locale

val Vert = Color(0xFF1DB954)
val VertFonce = Color(0xFF0E3B24)
val Or = Color(0xFFFFC94D)
val Rouge = Color(0xFFE5534B)

val couleurs = darkColorScheme(
    primary = Vert, secondary = Or, background = Color(0xFF0B1410), surface = Color(0xFF13201A),
    surfaceVariant = Color(0xFF1B2C23), onPrimary = Color.Black, onBackground = Color(0xFFE8F2EC),
    onSurface = Color(0xFFE8F2EC), error = Rouge,
)

@Composable
fun MissaTheme(content: @Composable () -> Unit) = MaterialTheme(colorScheme = couleurs, content = content)

fun pct(p: Double?, dec: Int = 1): String =
    if (p == null) "—" else String.format(Locale.FRANCE, "%.${dec}f %%", p * 100)

fun cote(c: Double?): String = if (c == null) "—" else String.format(Locale.FRANCE, "%.2f", c)

fun montant(v: Double): String = String.format(Locale.FRANCE, "%,.0f", v)

fun signe(v: Double?): String = if (v == null) "—" else String.format(Locale.FRANCE, "%+.1f %%", v * 100)

@Composable
fun Badge(texte: String, fond: Color, couleurTexte: Color = Color.Black) {
    Text(
        texte, color = couleurTexte, fontSize = 11.sp, fontWeight = FontWeight.Bold,
        modifier = Modifier.clip(RoundedCornerShape(6.dp)).background(fond)
            .padding(horizontal = 6.dp, vertical = 2.dp),
    )
}

/** Pourcentage animé : la valeur « défile » jusqu'à la nouvelle valeur quand elle change. */
@Composable
fun PourcentageAnime(
    p: Double?, modifier: Modifier = Modifier, dec: Int = 0, taille: TextUnit = 14.sp,
    couleur: Color = MaterialTheme.colorScheme.onSurface, gras: Boolean = true,
) {
    if (p == null) { Text("—", modifier, fontSize = taille, color = couleur); return }
    val v by animateFloatAsState(p.toFloat(), tween(450, easing = FastOutSlowInEasing), label = "pct")
    Text(pct(v.toDouble(), dec), modifier, fontSize = taille, color = couleur,
        fontWeight = if (gras) FontWeight.Bold else FontWeight.Normal)
}

/** Couleur selon la probabilité : vert ≥ 50 %, or ≥ 20 %, rouge en dessous. */
fun couleurProba(p: Double): Color = if (p >= 0.5) Vert else if (p >= 0.2) Or else Rouge

/** Tuile de sélection compacte (libellé + probabilité) ; surlignée si elle est dans le ticket. */
@Composable
fun BoutonSelection(
    titre: String, proba: Double?, selectionne: Boolean, modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    val fond by animateColorAsState(if (selectionne) Vert else MaterialTheme.colorScheme.surfaceVariant,
        tween(250), label = "fond")
    val texte by animateColorAsState(if (selectionne) Color.Black else MaterialTheme.colorScheme.onSurface,
        tween(250), label = "texte")
    val echelle by animateFloatAsState(if (selectionne) 1.04f else 1f, spring(dampingRatio = 0.5f), label = "echelle")
    Column(
        modifier.graphicsLayer { scaleX = echelle; scaleY = echelle }
            .clip(RoundedCornerShape(8.dp)).background(fond).clickable(onClick = onClick)
            .padding(horizontal = 6.dp, vertical = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(titre, color = texte, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        PourcentageAnime(proba, taille = 13.sp, couleur = texte)
    }
}

/** Barre de probabilité animée. */
@Composable
fun BarreProba(p: Double, modifier: Modifier = Modifier, couleur: Color = Vert, hauteur: Dp = 4.dp) {
    val v by animateFloatAsState(p.toFloat().coerceIn(0f, 1f), tween(450, easing = FastOutSlowInEasing), label = "barre")
    val c by animateColorAsState(couleur, tween(300), label = "couleur")
    Box(modifier.fillMaxWidth().height(hauteur).clip(RoundedCornerShape(hauteur / 2))
        .background(MaterialTheme.colorScheme.surfaceVariant)) {
        Box(Modifier.fillMaxWidth(v).height(hauteur).background(c))
    }
}

@Composable
fun BandeauJeuResponsable(texte: String) {
    Row(
        Modifier.fillMaxWidth().background(Color(0xFF2A1F0A)).padding(8.dp),
        horizontalArrangement = Arrangement.Center,
    ) {
        Text("⚠ $texte", color = Or, fontSize = 11.sp, textAlign = TextAlign.Center)
    }
}
