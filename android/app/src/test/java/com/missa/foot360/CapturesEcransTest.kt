package com.missa.foot360

import android.content.Context
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.test.core.app.ActivityScenario
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.hasScrollToIndexAction
import androidx.compose.ui.test.performScrollToIndex
import androidx.compose.ui.test.performScrollToNode
import androidx.compose.ui.test.hasScrollToNodeAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipeUp
import androidx.compose.ui.test.onRoot
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.github.takahirom.roborazzi.captureRoboImage
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

/** Captures d'écran de l'application (données de démonstration), rendues sans téléphone. */
@RunWith(AndroidJUnit4::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [35], qualifiers = "w400dp-h860dp-xxhdpi")
class CapturesEcransTest {
    @Before
    fun majeur() {
        ApplicationProvider.getApplicationContext<Context>()
            .getSharedPreferences("missa", Context.MODE_PRIVATE).edit()
            .putBoolean("majeur", true).putString("url_api", "http://127.0.0.1:9").commit()
    }

    @get:Rule
    val regle = createEmptyComposeRule()

    private fun attendreDonnees() = regle.waitUntil(20_000) {
        regle.onAllNodesWithText("Pronostic :", substring = true).fetchSemanticsNodes().isNotEmpty()
    }

    private fun capture(nom: String) {
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/$nom.png")
    }

    @Test
    fun parcours() {
        ActivityScenario.launch(MainActivity::class.java)
        regle.waitUntil(20_000) { regle.onAllNodesWithText("Matchs recommandés").fetchSemanticsNodes().isNotEmpty() }
        capture("01_accueil")
        // Analyses : liste des matchs, ticket en 3 sélections sur 3 matchs différents
        regle.onNodeWithText("Analyses").performClick()
        attendreDonnees()
        regle.onNodeWithText("Toutes les dates").performClick()
        regle.waitForIdle()
        regle.onAllNodesWithText("1", useUnmergedTree = true)[0].performClick()
        regle.onAllNodes(hasScrollToIndexAction())[0].performScrollToIndex(7)
        regle.waitForIdle()
        regle.onAllNodesWithText("2", useUnmergedTree = true)[0].performClick()
        regle.onAllNodes(hasScrollToIndexAction())[0].performScrollToIndex(11)
        regle.waitForIdle()
        regle.onAllNodesWithText("+2,5", useUnmergedTree = true)[0].performClick()
        regle.onAllNodes(hasScrollToIndexAction())[0].performScrollToIndex(0)
        regle.waitForIdle()
        capture("02_analyses")
        // Fiche d'un match : aperçu (pourquoi), forme, face-à-face, handicaps
        regle.onAllNodesWithText("Tous les paris", substring = true, useUnmergedTree = true)[0].performClick()
        capture("03_match_apercu")
        regle.onNodeWithText("Forme").performScrollTo().performClick()
        capture("04_match_forme")
        regle.onNodeWithText("Scores exacts").performScrollTo().performClick()
        capture("05_match_scores")
        regle.onNodeWithText("Handicaps").performScrollTo().performClick()
        capture("05b_match_handicaps")
        // Ticket : mise, risque, conseil, enregistrement
        regle.onNodeWithText("Ticket").performClick()
        regle.waitForIdle()
        regle.onNodeWithText("Mise").performScrollTo().performTextInput("1000")
        capture("06_ticket")
        regle.onAllNodes(hasScrollToNodeAction())[0].performScrollToNode(hasText("Enregistrer le ticket"))
        regle.onNodeWithText("Enregistrer le ticket").performClick()
        regle.waitForIdle()
        // Statistiques et profil
        regle.onNodeWithText("Stats").performClick()
        capture("07_stats")
        regle.onNodeWithText("Profil").performClick()
        capture("08_profil")
        // Générateur de tickets et conseils
        regle.onNodeWithText("Accueil").performClick()
        regle.waitForIdle()
        regle.onAllNodes(hasScrollToNodeAction())[0].performScrollToNode(hasText("Générateur de tickets"))
        regle.onNodeWithText("Générateur de tickets").performClick()
        capture("09_generateur")
        regle.onNodeWithText("Profil").performClick()
        regle.waitForIdle()
        regle.onNodeWithText("Conseils").performClick()
        regle.waitForIdle()
        regle.onNodeWithText("Value", substring = true).performClick()
        capture("10_value")
    }
}
