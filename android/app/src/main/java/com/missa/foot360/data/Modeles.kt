@file:Suppress("PropertyName")

package com.missa.foot360.data

import kotlinx.serialization.Serializable

/** Modèles correspondant au JSON produit par le moteur (scripts/generer_pronostics.py / API). */

@Serializable
data class Pronostics(
    val genere_le: String = "",
    val avertissement: String = "",
    val championnats: List<Championnat> = emptyList(),
    val catalogue: List<GroupeMarche> = emptyList(),
    val fiabilite: Map<String, List<TrancheFiabilite>> = emptyMap(),
)

@Serializable
data class OptionMarche(val code: String, val libelle: String)

@Serializable
data class GroupeMarche(val groupe: String, val titre: String, val options: List<OptionMarche>)

/** Historique mesuré : sélections annoncées entre « de » et « a » -> taux de réussite réel. */
@Serializable
data class TrancheFiabilite(val de: Double, val a: Double, val n: Int, val annonce: Double, val reel: Double)

@Serializable
data class JumeauJson(
    val matrice: List<List<Double>>,
    val part_1mt: List<Double>,
    val corners: List<Double>,
    val cartons: List<Double>,
)

@Serializable
data class Championnat(val code: String, val nom: String, val matchs: List<Match> = emptyList())

@Serializable
data class Confiance(
    val niveau: String = "",
    val taux_historique: Double? = null,
    val n_historique: Int = 0,
    val haute_confiance: Boolean = false,
)

@Serializable
data class Marche(
    val libelle: String,
    val proba: Double,
    val cote_juste: Double? = null,
    val meilleure_cote: Double? = null,
    val valeur: Double? = null,
    val confiance: Confiance? = null,
)

@Serializable
data class AvisPronostiqueur(
    val pronostiqueur: String,
    val selection: String,
    val cote: Double,
    val ajustement: Double = 0.0,
    val statut: String = "",
)

@Serializable
data class Match(
    val id: String,
    val championnat: String = "",
    val coup_envoi: String = "",
    val domicile: String,
    val exterieur: String,
    val methode: String = "",
    val buts_attendus: List<Double> = emptyList(),
    val score_probable: String = "",
    val pronostic_principal: String = "",
    val selection_haute_confiance: String? = null,
    val selections_value: List<String> = emptyList(),
    val marches: Map<String, Marche> = emptyMap(),
    val pronostiqueurs: List<AvisPronostiqueur> = emptyList(),
    val matrice: List<List<Double>> = emptyList(),
    val jumeau: JumeauJson? = null,
    val corners_attendus: List<Double> = emptyList(),
    val cartons_attendus: List<Double> = emptyList(),
) {
    /** Coup d'envoi dans le fuseau horaire du téléphone (les heures publiées sont en UTC, « …Z »). */
    private val local: java.time.LocalDateTime?
        get() = runCatching {
            if (coup_envoi.endsWith("Z") || coup_envoi.length > 19)
                java.time.OffsetDateTime.parse(coup_envoi)
                    .atZoneSameInstant(java.time.ZoneId.systemDefault()).toLocalDateTime()
            else java.time.LocalDateTime.parse(coup_envoi)
        }.getOrNull()
    val date: String get() = local?.toLocalDate()?.toString() ?: coup_envoi.take(10)
    val heure: String get() = local?.toLocalTime()?.toString()?.take(5) ?: coup_envoi.drop(11).take(5)
}

@Serializable
data class NotePronostiqueur(
    val nom: String,
    val n: Int = 0,
    val clv_moyen: Double = 0.0,
    val t_score: Double = 0.0,
    val pct_battu: Double? = null,
    val fiable: Boolean = false,
    val ajustement: Double = 0.0,
    val statut: String = "",
)
