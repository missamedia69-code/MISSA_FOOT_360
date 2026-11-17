package com.missa.foot360.moteur

/**
 * Calcul en temps réel de la probabilité d'un combiné, sur le téléphone.
 *
 * Même logique que le moteur Python (missa/selections.py) :
 * - chaque sélection est une condition sur le score final (i buts domicile, j buts extérieur) ;
 * - matchs différents : probabilités multipliées ;
 * - même match : probabilité conjointe lue dans la matrice des scores (corrélations respectées).
 */
object Selections {
    val libelles: Map<String, String> = linkedMapOf(
        "1" to "Victoire domicile", "N" to "Match nul", "2" to "Victoire extérieur",
        "1N" to "Double chance 1N", "12" to "Double chance 12", "N2" to "Double chance N2",
        "plus_1.5" to "Plus de 1,5 but", "moins_1.5" to "Moins de 1,5 but",
        "plus_2.5" to "Plus de 2,5 buts", "moins_2.5" to "Moins de 2,5 buts",
        "plus_3.5" to "Plus de 3,5 buts", "moins_3.5" to "Moins de 3,5 buts",
        "btts_oui" to "Les deux équipes marquent", "btts_non" to "Une équipe ne marque pas",
        "dom_marque" to "Le domicile marque", "ext_marque" to "L'extérieur marque",
    )

    fun libelle(code: String): String =
        if (code.startsWith("score:")) "Score exact ${code.removePrefix("score:")}"
        else libelles[code] ?: code

    fun condition(code: String, i: Int, j: Int): Boolean = when (code) {
        "1" -> i > j
        "N" -> i == j
        "2" -> i < j
        "1N" -> i >= j
        "12" -> i != j
        "N2" -> i <= j
        "plus_1.5" -> i + j >= 2
        "moins_1.5" -> i + j <= 1
        "plus_2.5" -> i + j >= 3
        "moins_2.5" -> i + j <= 2
        "plus_3.5" -> i + j >= 4
        "moins_3.5" -> i + j <= 3
        "btts_oui" -> i > 0 && j > 0
        "btts_non" -> i == 0 || j == 0
        "dom_marque" -> i > 0
        "ext_marque" -> j > 0
        else -> if (code.startsWith("score:")) {
            val (a, b) = code.removePrefix("score:").split("-").map { it.toInt() }
            i == a && j == b
        } else false
    }

    fun proba(matrice: List<List<Double>>, codes: Collection<String>): Double {
        var s = 0.0
        for (i in matrice.indices) for (j in matrice[i].indices) {
            if (codes.all { condition(it, i, j) }) s += matrice[i][j]
        }
        return s
    }
}

data class SelectionCombi(
    val matchId: String,
    val code: String,
    val libelleMatch: String,
    val cote: Double? = null,
)

data class ResultatCombi(
    val proba: Double,
    val coteJuste: Double?,
    val coteBookmaker: Double?,
    val valeurAttendue: Double?,
    val memeMatch: Boolean,
    val probaParMatch: Map<String, Double>,
)

fun calculerCombinaison(
    selections: List<SelectionCombi>,
    matrices: Map<String, List<List<Double>>>,
): ResultatCombi {
    val parMatch = selections.groupBy { it.matchId }
    val probaParMatch = parMatch.mapValues { (id, sels) ->
        val m = matrices[id] ?: return@mapValues 0.0
        Selections.proba(m, sels.map { it.code })
    }
    val proba = if (selections.isEmpty()) 0.0 else probaParMatch.values.fold(1.0) { a, b -> a * b }
    val cotes = selections.map { it.cote }
    val coteBk = if (selections.isNotEmpty() && cotes.all { it != null && it > 1.0 })
        cotes.fold(1.0) { a, b -> a * b!! } else null
    return ResultatCombi(
        proba = proba,
        coteJuste = if (proba > 0) 1.0 / proba else null,
        coteBookmaker = coteBk,
        valeurAttendue = coteBk?.let { proba * it - 1.0 },
        memeMatch = parMatch.values.any { it.size > 1 },
        probaParMatch = probaParMatch,
    )
}
