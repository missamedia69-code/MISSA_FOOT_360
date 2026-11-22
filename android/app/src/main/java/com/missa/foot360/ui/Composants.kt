package com.missa.foot360.ui

import androidx.compose.foundation.background
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

/** Bouton de sélection 1 / N / 2 avec sa probabilité ; surligné s'il est dans le combiné. */
@Composable
fun BoutonSelection(
    titre: String, proba: Double?, selectionne: Boolean, modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    val fond = if (selectionne) Vert else MaterialTheme.colorScheme.surfaceVariant
    val texte = if (selectionne) Color.Black else MaterialTheme.colorScheme.onSurface
    Column(
        modifier.clip(RoundedCornerShape(10.dp)).background(fond).clickable(onClick = onClick)
            .padding(vertical = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(titre, color = texte, fontSize = 12.sp)
        Text(pct(proba, 0), color = texte, fontWeight = FontWeight.Bold, fontSize = 15.sp)
    }
}

@Composable
fun BarreProba(p: Double, modifier: Modifier = Modifier) {
    Box(modifier.fillMaxWidth().height(4.dp).clip(RoundedCornerShape(2.dp))
        .background(MaterialTheme.colorScheme.surfaceVariant)) {
        Box(Modifier.fillMaxWidth(p.toFloat().coerceIn(0f, 1f)).height(4.dp).background(Vert))
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
