package com.missa.foot360.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.runtime.setValue
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

// Charte « vert néon sur charbon » (reprise et harmonisée avec la version web)
val Vert = Color(0xFF2CE083)
val VertFonce = Color(0xFF0B3A20)
val Or = Color(0xFFF4BD45)
val Rouge = Color(0xFFFF6F6F)
val Orange = Color(0xFFF59A4A)
val Discret = Color(0xFF9AB0A1)
val Bord = Color(0x18FFFFFF)

val couleurs = darkColorScheme(
    primary = Vert, onPrimary = Color(0xFF04140B), primaryContainer = VertFonce, onPrimaryContainer = Vert,
    secondary = Or, secondaryContainer = VertFonce, onSecondaryContainer = Vert,
    background = Color(0xFF060E09), onBackground = Color(0xFFEDF5EF),
    surface = Color(0xFF0A1610), onSurface = Color(0xFFEDF5EF),
    surfaceVariant = Color(0xFF1E2D24), onSurfaceVariant = Discret,
    surfaceContainerLowest = Color(0xFF07110B), surfaceContainerLow = Color(0xFF0E1913),
    surfaceContainer = Color(0xFF111D16), surfaceContainerHigh = Color(0xFF14211A),
    surfaceContainerHighest = Color(0xFF17241C), surfaceTint = Vert,
    outline = Color(0x29FFFFFF), outlineVariant = Bord, error = Rouge,
)

/** Devise affichée pour les mises et les gains (réglable dans Profil → Réglages). */
var devise by androidx.compose.runtime.mutableStateOf("FCFA")

/** Petit titre de section en capitales vertes (« TABLEAU DE BORD »). */
@Composable
fun Surtitre(texte: String, couleur: Color = Vert) {
    Text(texte.uppercase(), fontSize = 10.sp, color = couleur, fontWeight = FontWeight.Bold, letterSpacing = 1.4.sp)
}

/** Pastille teintée : texte coloré sur fond de la même couleur, très atténué (risque, informations). */
@Composable
fun Pastille(texte: String, couleur: Color = Discret, modifier: Modifier = Modifier, taille: TextUnit = 11.sp) {
    Text(texte, color = couleur, fontSize = taille, fontWeight = FontWeight.SemiBold, maxLines = 1,
        modifier = modifier.clip(RoundedCornerShape(50)).background(couleur.copy(alpha = 0.13f))
            .border(1.dp, couleur.copy(alpha = 0.28f), RoundedCornerShape(50))
            .padding(horizontal = 8.dp, vertical = 3.dp))
}

/** Puce d'information « Libellé valeur » (en-tête de la fiche match). */
@Composable
fun PuceInfo(titre: String, valeur: String) {
    Row(Modifier.clip(RoundedCornerShape(8.dp)).background(couleurs.surfaceContainerHighest)
        .border(1.dp, Bord, RoundedCornerShape(8.dp)).padding(horizontal = 8.dp, vertical = 4.dp)) {
        Text("$titre ", fontSize = 11.sp, color = Discret)
        Text(valeur, fontSize = 11.sp, fontWeight = FontWeight.Bold)
    }
}

/** Carte bordée, légèrement teintée de vert (style commun à tous les écrans). */
@Composable
fun Carte(modifier: Modifier = Modifier, accent: Boolean = false, onClick: (() -> Unit)? = null,
          content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit) {
    val forme = RoundedCornerShape(14.dp)
    val fond = if (accent) androidx.compose.ui.graphics.Brush.linearGradient(listOf(Color(0xFF0F3121), Color(0xFF0D1A13)))
               else androidx.compose.ui.graphics.SolidColor(couleurs.surfaceContainer)
    Column(modifier.fillMaxWidth().clip(forme).background(fond)
        .border(1.dp, if (accent) Vert.copy(alpha = 0.25f) else Bord, forme)
        .let { if (onClick != null) it.clickable(onClick = onClick) else it }, content = content)
}

@Composable
fun MissaTheme(content: @Composable () -> Unit) = MaterialTheme(colorScheme = couleurs, content = content)

fun pct(p: Double?, dec: Int = 1): String =
    if (p == null) "—" else String.format(Locale.FRANCE, "%.${dec}f %%", p * 100)

fun cote(c: Double?): String = if (c == null) "—" else String.format(Locale.FRANCE, "%.2f", c)

fun montant(v: Double): String = String.format(Locale.FRANCE, "%,.0f", v).replace('\u202F', ' ').replace('\u00A0', ' ') +
    (if (devise.isNotEmpty()) " $devise" else "")

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
    alignement: TextAlign? = null,
) {
    if (p == null) { Text("—", modifier, fontSize = taille, color = couleur, textAlign = alignement); return }
    val v by animateFloatAsState(p.toFloat(), tween(450, easing = FastOutSlowInEasing), label = "pct")
    Text(pct(v.toDouble(), dec), modifier, fontSize = taille, color = couleur,
        fontWeight = if (gras) FontWeight.Bold else FontWeight.Normal, textAlign = alignement)
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

/** Petit bouton « + Ajouter » / « ✓ Ajouté » (vert bordé, plein quand la sélection est au ticket). */
@Composable
fun BoutonAjouter(dans: Boolean, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val fond by animateColorAsState(if (dans) Vert else VertFonce.copy(alpha = 0.6f), tween(250), label = "fondAjout")
    Text(if (dans) "✓ Ajouté" else "+ Ajouter", color = if (dans) Color(0xFF04140B) else Vert, fontSize = 12.sp,
        fontWeight = FontWeight.Bold, textAlign = TextAlign.Center,
        modifier = modifier.clip(RoundedCornerShape(9.dp)).background(fond)
            .border(1.dp, Vert.copy(alpha = 0.4f), RoundedCornerShape(9.dp)).clickable(onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 6.dp))
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
        Modifier.fillMaxWidth().background(Color(0xFF1C1708)).padding(6.dp),
        horizontalArrangement = Arrangement.Center,
    ) {
        Text("⚠ $texte", color = Or, fontSize = 11.sp, textAlign = TextAlign.Center)
    }
}
