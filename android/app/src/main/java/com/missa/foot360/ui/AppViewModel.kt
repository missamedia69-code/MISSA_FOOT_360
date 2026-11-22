package com.missa.foot360.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.missa.foot360.data.Depot
import com.missa.foot360.data.Match
import com.missa.foot360.data.NotePronostiqueur
import com.missa.foot360.data.Pronostics
import com.missa.foot360.data.TrancheFiabilite
import com.missa.foot360.moteur.JambeCombine
import com.missa.foot360.moteur.Jumeau
import com.missa.foot360.moteur.Modulation
import com.missa.foot360.moteur.ParamsJumeau
import com.missa.foot360.moteur.RegleTicket
import com.missa.foot360.moteur.ResultatCombine
import com.missa.foot360.moteur.calculerCombine
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
    val combi: List<JambeCombine> = emptyList(),
    val resultat: ResultatCombine? = null,
    val modulations: Map<String, Modulation> = emptyMap(),
    val bonus: Double = 0.0,
    val unParMatch: Boolean = true,
    val message: String? = null,
) {
    val matchs: Map<String, Match> by lazy {
        pronostics.championnats.flatMap { it.matchs }.associateBy { it.id }
    }
}

/** Famille de fiabilité d'un code (même règle que scripts/valider_jumeau.py). */
fun familleFiabilite(code: String): String = when {
    code.startsWith("CORNERS_") -> "corners"
    code.startsWith("CARTONS_") -> "cartons"
    "&" in code -> "combines_officiels"
    listOf("@MT", "MTFT", "MT_PLUS", "_2MT", "_1MT").any { it in code } -> "mi_temps"
    code.startsWith("CS") -> "score_exact"
    else -> "buts_match"
}

/** Taux de réussite réellement observé pour cette famille à ce niveau de probabilité. */
fun tauxHistorique(fiab: Map<String, List<TrancheFiabilite>>, famille: String, p: Double): TrancheFiabilite? =
    fiab[famille]?.firstOrNull { p >= it.de && p < it.a }

class AppViewModel(app: Application) : AndroidViewModel(app) {
    val depot = Depot(app)
    private val _etat = MutableStateFlow(EtatApp())
    val etat: StateFlow<EtatApp> = _etat.asStateFlow()
    private val cacheJumeaux = HashMap<Pair<String, Modulation>, Jumeau>()

    init {
        _etat.update { it.copy(unParMatch = !depot.plusieursParMatch) }
        charger()
    }

    fun messageVu() = _etat.update { it.copy(message = null) }

    /** Mode ticket (une sélection par match, comme chez le bookmaker) ou analyse libre. */
    fun changerMode(unParMatch: Boolean) {
        depot.plusieursParMatch = !unParMatch
        _etat.update { e ->
            val t = if (unParMatch) RegleTicket.normaliser(e.combi) else e.combi
            e.copy(unParMatch = unParMatch, combi = t,
                message = if (unParMatch && t.size < e.combi.size) "Ticket corrigé : une seule sélection gardée par match." else null)
        }
        recalculer()
    }

    fun charger() = viewModelScope.launch {
        _etat.update { it.copy(chargement = true) }
        val r = depot.pronostics()
        val experts = depot.pronostiqueurs()
        cacheJumeaux.clear()
        _etat.update {
            it.copy(chargement = false, pronostics = r.pronostics, horsLigne = r.horsLigne,
                erreur = r.erreur, experts = experts)
        }
        recalculer()
    }

    /** Jumeau du match (avec la modulation choisie par l'utilisateur). */
    fun jumeau(matchId: String): Jumeau? {
        val e = _etat.value
        val m = e.matchs[matchId] ?: return null
        val j = m.jumeau ?: return null
        val mod = e.modulations[matchId] ?: Modulation()
        return cacheJumeaux.getOrPut(matchId to mod) {
            Jumeau(ParamsJumeau(j.matrice, j.part_1mt, j.corners, j.cartons), mod)
        }
    }

    fun proba(matchId: String, code: String): Double? = runCatching { jumeau(matchId)?.proba(code) }.getOrNull()

    fun moduler(matchId: String, mod: Modulation) {
        _etat.update { it.copy(modulations = it.modulations + (matchId to mod)) }
        recalculer()
    }

    fun estSelectionne(matchId: String, code: String) =
        _etat.value.combi.any { it.matchId == matchId && it.code == code }

    /** Ajoute ou retire une sélection en respectant les règles du ticket ; recalcul immédiat. */
    fun basculer(match: Match, code: String, libelle: String, cote: Double? = null) {
        _etat.update { e ->
            val r = RegleTicket.basculer(e.combi,
                JambeCombine(match.id, code, "${match.domicile} - ${match.exterieur}", libelle, cote), e.unParMatch)
            e.copy(combi = r.ticket, message = r.message)
        }
        recalculer()
    }

    fun ajouterPlusieurs(jambes: List<JambeCombine>) {
        _etat.update { e ->
            val r = RegleTicket.ajouterPlusieurs(e.combi, jambes, e.unParMatch)
            e.copy(combi = r.ticket, message = r.message)
        }
        recalculer()
    }

    fun modifierCote(index: Int, cote: Double?) {
        _etat.update { e -> e.copy(combi = e.combi.mapIndexed { i, s -> if (i == index) s.copy(cote = cote) else s }) }
        recalculer()
    }

    fun modifierBonus(b: Double) {
        _etat.update { it.copy(bonus = b) }
        recalculer()
    }

    fun retirer(index: Int) {
        _etat.update { e -> e.copy(combi = e.combi.filterIndexed { i, _ -> i != index }) }
        recalculer()
    }

    fun vider() = _etat.update { it.copy(combi = emptyList(), resultat = null) }

    private fun recalculer() {
        val e = _etat.value
        if (e.combi.isEmpty()) { _etat.update { it.copy(resultat = null) }; return }
        val jumeaux = e.combi.map { it.matchId }.distinct().mapNotNull { id -> jumeau(id)?.let { id to it } }.toMap()
        val r = runCatching { calculerCombine(e.combi, jumeaux, e.bonus) }.getOrNull()
        _etat.update { it.copy(resultat = r) }
    }

    /**
     * Assistant : pour chaque match, la sélection la plus probable dont la cote juste reste
     * au moins égale à coteMin (ex. 1,10 exigée par certains bookmakers pour le bonus),
     * puis les nbMatchs matchs les plus sûrs.
     */
    fun proposerCombine(nbMatchs: Int, coteMin: Double, groupes: Set<String>, date: String?): List<Pair<JambeCombine, Double>> {
        val e = _etat.value
        val options = e.pronostics.catalogue.filter { it.groupe in groupes }
            .flatMap { g -> g.options.map { o -> o.code to "${g.titre} : ${o.libelle}" } }
        val candidats = e.matchs.values.filter { it.jumeau != null && (date == null || it.date == date) }.mapNotNull { m ->
            options.mapNotNull { (code, lib) ->
                proba(m.id, code)?.takeIf { it > 0 && 1 / it >= coteMin }?.let { p ->
                    JambeCombine(m.id, code, "${m.domicile} - ${m.exterieur}", lib) to p
                }
            }.maxByOrNull { it.second }
        }
        return candidats.sortedByDescending { it.second }.take(nbMatchs)
    }
}
