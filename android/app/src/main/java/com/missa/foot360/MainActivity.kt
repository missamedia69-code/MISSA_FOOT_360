package com.missa.foot360

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Groups
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.SportsSoccer
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.ReceiptLong
import androidx.compose.material3.BadgedBox
import androidx.compose.ui.unit.sp
import androidx.compose.ui.unit.dp
import com.missa.foot360.ui.EcranAccueil
import com.missa.foot360.ui.EcranStats
import com.missa.foot360.ui.EcranProfil
import com.missa.foot360.ui.EcranTicketsSpeciaux
import com.missa.foot360.ui.EcranContact
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.missa.foot360.ui.AppViewModel
import com.missa.foot360.ui.BandeauJeuResponsable
import com.missa.foot360.ui.BarreCombi
import com.missa.foot360.ui.EcranAssistant
import com.missa.foot360.ui.EcranCombi
import com.missa.foot360.ui.EcranConseils
import com.missa.foot360.ui.EcranDetail
import com.missa.foot360.ui.EcranExperts
import com.missa.foot360.ui.EcranMatchs
import com.missa.foot360.ui.EcranReglages
import com.missa.foot360.ui.MissaTheme
import com.missa.foot360.ui.Vert
import com.missa.foot360.ui.Discret

class MainActivity : ComponentActivity() {
    private val vm: AppViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MissaTheme { Application(vm) } }
    }
}

private val ONGLETS = listOf(
    Triple("accueil", "Accueil", Icons.Default.Home),
    Triple("matchs", "Analyses", Icons.Default.SportsSoccer),
    Triple("combi", "Ticket", Icons.Default.ReceiptLong),
    Triple("stats", "Stats", Icons.Default.BarChart),
    Triple("profil", "Profil", Icons.Default.Person),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun Application(vm: AppViewModel) {
    val etat by vm.etat.collectAsState()
    val nav = rememberNavController()
    val route = nav.currentBackStackEntryAsState().value?.destination?.route
    var majeur by remember { mutableStateOf(vm.depot.majeurConfirme) }

    if (!majeur) {
        AlertDialog(
            onDismissRequest = {},
            title = { Text("Réservé aux majeurs") },
            text = { Text("MISSA FOOT 360 fournit des probabilités statistiques, pas des certitudes. " +
                "Les paris sportifs comportent des risques (endettement, dépendance). " +
                "Confirmez-vous avoir 18 ans ou plus ?") },
            confirmButton = { TextButton({ vm.depot.majeurConfirme = true; majeur = true }) { Text("J'ai 18 ans ou plus") } },
        )
    }

    val snack = remember { SnackbarHostState() }
    LaunchedEffect(etat.message) {
        etat.message?.let { snack.showSnackbar(it, duration = SnackbarDuration.Short); vm.messageVu() }
    }

    Scaffold(
        snackbarHost = {
            SnackbarHost(snack) { d ->
                androidx.compose.material3.Snackbar(
                    modifier = Modifier.padding(horizontal = 12.dp)
                        .border(1.dp, com.missa.foot360.ui.Vert.copy(alpha = 0.35f), androidx.compose.foundation.shape.RoundedCornerShape(12.dp)),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
                    containerColor = androidx.compose.ui.graphics.Color(0xFF12261A), contentColor = androidx.compose.ui.graphics.Color(0xFFEDF5EF),
                ) { Text("✓  " + d.visuals.message, fontSize = 13.sp) }
            }
        },
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(androidx.compose.ui.text.buildAnnotatedString {
                            append("MISSA FOOT ")
                            pushStyle(androidx.compose.ui.text.SpanStyle(color = Vert)); append("360"); pop()
                        }, fontWeight = FontWeight.Bold, fontSize = 19.sp, letterSpacing = 0.5.sp)
                        Text("ANALYSE FOOTBALL INTELLIGENTE", fontSize = 9.sp, color = Discret, letterSpacing = 1.2.sp)
                    }
                },
                navigationIcon = {
                    if (route != null && ONGLETS.none { it.first == route }) {
                        IconButton({ nav.popBackStack() }) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Retour") }
                    }
                },
                actions = {
                    // Bouton « Actualiser » : l'icône tourne pendant le téléchargement
                    val rotation = rememberInfiniteTransition(label = "rotation")
                    val angle by rotation.animateFloat(0f, 360f,
                        infiniteRepeatable(tween(900, easing = LinearEasing)), label = "angle")
                    IconButton(onClick = { vm.actualiser() }) {
                        Icon(Icons.Default.Refresh, "Actualiser", tint = Vert,
                            modifier = if (etat.actualisation) Modifier.graphicsLayer { rotationZ = angle } else Modifier)
                    }
                    IconButton(onClick = { if (route != "reglages") nav.navigate("reglages") }) {
                        Icon(Icons.Default.Settings, "Réglages", tint = com.missa.foot360.ui.Discret)
                    }
                },
            )
        },
        bottomBar = {
            Column {
                AnimatedVisibility(
                    visible = route != "combi" && etat.resultat != null,
                    enter = slideInVertically { it } + fadeIn(),
                    exit = slideOutVertically { it } + fadeOut(),
                ) { BarreCombi(etat) { nav.navigate("combi") } }
                BandeauJeuResponsable("Probabilités, pas certitudes. 18+. Jouez avec modération.")
                NavigationBar {
                    ONGLETS.forEach { (r, titre, icone) ->
                        NavigationBarItem(
                            selected = route == r,
                            onClick = { allerA(nav, r) },
                            icon = {
                                if (r == "combi" && etat.combi.isNotEmpty()) {
                                    // la pastille rebondit à chaque ajout ou retrait
                                    val rebond = remember { androidx.compose.animation.core.Animatable(1f) }
                                    LaunchedEffect(etat.combi.size) {
                                        rebond.snapTo(1.5f); rebond.animateTo(1f, androidx.compose.animation.core.spring(dampingRatio = 0.35f))
                                    }
                                    BadgedBox(badge = { androidx.compose.material3.Badge(Modifier.graphicsLayer { scaleX = rebond.value; scaleY = rebond.value }) {
                                        Text("${etat.combi.size}") } }) { Icon(icone, titre) }
                                }
                                else Icon(icone, titre)
                            },
                            label = { Text(titre, fontSize = 11.sp) },
                        )
                    }
                }
            }
        },
    ) { marges ->
        val aller: (String) -> Unit = { r -> if (ONGLETS.any { it.first == r }) allerA(nav, r) else nav.navigate(r) }
        NavHost(nav, startDestination = "accueil", modifier = Modifier.padding(marges),
            enterTransition = { fadeIn(tween(260)) + androidx.compose.animation.slideInHorizontally(tween(260)) { it / 14 } },
            exitTransition = { fadeOut(tween(180)) },
            popEnterTransition = { fadeIn(tween(260)) },
            popExitTransition = { fadeOut(tween(180)) + androidx.compose.animation.slideOutHorizontally(tween(220)) { it / 14 } }) {
            composable("accueil") { EcranAccueil(etat, vm, { nav.navigate("match/$it") }, aller) }
            composable("matchs") { EcranMatchs(etat, vm) { nav.navigate("match/$it") } }
            composable("assistant") { EcranAssistant(etat, vm) { allerA(nav, "combi") } }
            composable("conseils") { EcranConseils(etat, vm) { nav.navigate("match/$it") } }
            composable("stats") { EcranStats(etat, aller) }
            composable("profil") { EcranProfil(etat, vm, aller) }
            composable("experts") { EcranExperts(etat) }
            composable("reglages") { EcranReglages(vm, etat) }
            composable("speciaux") { EcranTicketsSpeciaux(etat, vm) }
            composable("contact") { EcranContact(etat) }
            composable("combi") { EcranCombi(etat, vm, aller) }
            composable("match/{id}") { e -> EcranDetail(etat.matchs[e.arguments?.getString("id")], etat, vm) }
        }
    }
}

private fun allerA(nav: NavHostController, route: String) {
    if (route == "accueil") {
        nav.popBackStack("accueil", inclusive = false)  // retour direct à l'accueil
    } else {
        nav.navigate(route) {
            popUpTo("accueil")
            launchSingleTop = true
        }
    }
}
