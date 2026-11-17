package com.missa.foot360.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.missa.foot360.data.Depot
import com.missa.foot360.data.Match
import com.missa.foot360.data.NotePronostiqueur
import com.missa.foot360.data.Pronostics
import com.missa.foot360.moteur.ResultatCombi
import com.missa.foot360.moteur.SelectionCombi
import com.missa.foot360.moteur.calculerCombinaison
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class EtatApp(
    val chargement: Boolean = true,
    val pronostics: Pronostics = Pronostics(),
    val horsLigne: Boolean = false,
    val erreur: String? = null,
    val experts: List<NotePronostiqueur> = emptyList(),
    val combi: List<SelectionCombi> = emptyList(),
    val resultat: ResultatCombi? = null,
) {
    val matchs: Map<String, Match> by lazy {
        pronostics.championnats.flatMap { it.matchs }.associateBy { it.id }
    }
}

class AppViewModel(app: Application) : AndroidViewModel(app) {
    val depot = Depot(app)
    private val _etat = MutableStateFlow(EtatApp())
    val etat: StateFlow<EtatApp> = _etat.asStateFlow()

    init { charger() }

    fun charger() = viewModelScope.launch {
        _etat.update { it.copy(chargement = true) }
        val r = depot.pronostics()
        val experts = depot.pronostiqueurs()
        _etat.update {
            it.copy(chargement = false, pronostics = r.pronostics, horsLigne = r.horsLigne,
                erreur = r.erreur, experts = experts)
        }
        recalculer()
    }

    fun estSelectionne(matchId: String, code: String) =
        _etat.value.combi.any { it.matchId == matchId && it.code == code }

    /** Ajoute ou retire une sélection : la probabilité du combiné est recalculée immédiatement. */
    fun basculer(match: Match, code: String) {
        _etat.update { e ->
            val existe = e.combi.any { it.matchId == match.id && it.code == code }
            val nouvelle = if (existe) e.combi.filterNot { it.matchId == match.id && it.code == code }
            else e.combi + SelectionCombi(match.id, code, "${match.domicile} - ${match.exterieur}",
                match.marches[code]?.meilleure_cote)
            e.copy(combi = nouvelle)
        }
        recalculer()
    }

    fun modifierCote(index: Int, cote: Double?) {
        _etat.update { e ->
            e.copy(combi = e.combi.mapIndexed { i, s -> if (i == index) s.copy(cote = cote) else s })
        }
        recalculer()
    }

    fun retirer(index: Int) {
        _etat.update { e -> e.copy(combi = e.combi.filterIndexed { i, _ -> i != index }) }
        recalculer()
    }

    fun vider() {
        _etat.update { it.copy(combi = emptyList(), resultat = null) }
    }

    private fun recalculer() {
        _etat.update { e ->
            if (e.combi.isEmpty()) e.copy(resultat = null)
            else e.copy(resultat = calculerCombinaison(e.combi, e.matchs.mapValues { it.value.matrice }))
        }
    }
}
