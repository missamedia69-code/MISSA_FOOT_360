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

    @Test
    fun parcours() {
        // l'application démarre après la configuration (serveur injoignable -> données de démonstration)
        ActivityScenario.launch(MainActivity::class.java)
        attendreDonnees()
        regle.onRoot().captureRoboImage("../../docs/captures/1_matchs.png")
        // Scénario : « 1 » sur le 1er match, « 2 » sur le 2e, « +2,5 buts » sur le 3e
        regle.onAllNodesWithText("1", useUnmergedTree = true)[0].performClick()
        regle.onAllNodesWithText("2", useUnmergedTree = true)[1].performClick()
        regle.onAllNodes(hasScrollToIndexAction())[0].performScrollToIndex(6)
        regle.waitForIdle()
        regle.waitForIdle()
        regle.onAllNodesWithText("+2,5", useUnmergedTree = true)[0].performClick()
        regle.waitForIdle()
        regle.onAllNodes(hasScrollToIndexAction())[0].performScrollToIndex(0)
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/10_scenario_liste.png")
        regle.onNodeWithText("Voir ›").performClick()
        regle.waitForIdle()
        regle.onNodeWithText("Mise").performScrollTo().performTextInput("1000")
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/11_scenario_ticket.png")
        regle.onNodeWithText("Matchs").performClick()
        regle.waitForIdle()
        regle.onAllNodesWithText(" - ", substring = true, useUnmergedTree = true).fetchSemanticsNodes().let { }
        regle.onAllNodesWithText("Tous les paris", substring = true, useUnmergedTree = true)[0].performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/2_detail_resultat.png")
        regle.onNodeWithText("Mi-temps").performScrollTo().performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/3_detail_mi_temps.png")
        regle.onNodeWithText("Corners").performScrollTo().performClick()
        regle.waitForIdle()
        regle.onAllNodesWithText("Plus de 9,5", useUnmergedTree = true)[0].performClick()
        regle.onNodeWithText("Buts").performScrollTo().performClick()
        regle.waitForIdle()
        regle.onAllNodesWithText("Plus de 1,5", useUnmergedTree = true)[0].performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/8_remplacement.png")
        regle.onNodeWithText("Moduler le match", substring = true).performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/4_modulation.png")
        regle.onNodeWithText("Voir ›").performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/5_combine.png")
        regle.onNodeWithText("Assistant").performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/6_assistant.png")
        regle.onNodeWithText("Conseils").performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/7_haute_confiance.png")
        regle.onNodeWithText("Value", substring = true).performClick()
        regle.waitForIdle()
        regle.onRoot().captureRoboImage("../../docs/captures/9_value.png")
    }
}
