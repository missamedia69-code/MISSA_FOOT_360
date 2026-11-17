package com.missa.foot360.moteur

/**
 * Règles d'un ticket combiné chez un bookmaker (ex. BetPawa) :
 * - une seule sélection par match : les sélections d'un même match sont dépendantes et ne sont
 *   pas acceptées ensemble (les combinés officiels « 1X2 & les deux marquent », etc. comptent
 *   pour UNE sélection) ;
 * - 60 sélections au maximum ;
 * - le bonus de gains ne concerne que les sélections à 1,10 ou plus.
 */
object RegleTicket {
    const val MAX_SELECTIONS = 60
    const val COTE_MIN_BONUS = 1.10

    data class Resultat(val ticket: List<JambeCombine>, val message: String?)

    /** Ajoute (ou retire si déjà présente) une sélection en respectant les règles du ticket. */
    fun basculer(ticket: List<JambeCombine>, jambe: JambeCombine, unParMatch: Boolean): Resultat {
        if (ticket.any { it.matchId == jambe.matchId && it.code == jambe.code }) {
            return Resultat(ticket.filterNot { it.matchId == jambe.matchId && it.code == jambe.code }, null)
        }
        if (unParMatch) {
            val ancienne = ticket.firstOrNull { it.matchId == jambe.matchId }
            if (ancienne != null) {
                return Resultat(
                    ticket.map { if (it.matchId == jambe.matchId) jambe else it },
                    "« ${ancienne.libelle} » remplacé par « ${jambe.libelle} » : un seul pari par match sur un ticket.",
                )
            }
        }
        if (ticket.size >= MAX_SELECTIONS) {
            return Resultat(ticket, "Un ticket est limité à $MAX_SELECTIONS sélections.")
        }
        return Resultat(ticket + jambe, null)
    }

    /** Ajoute plusieurs sélections (assistant) : chacune remplace celle de son match. */
    fun ajouterPlusieurs(ticket: List<JambeCombine>, jambes: List<JambeCombine>, unParMatch: Boolean): Resultat {
        var t = ticket
        var remplacees = 0
        for (j in jambes) {
            if (t.any { it.matchId == j.matchId && it.code == j.code }) continue
            val r = basculer(t, j, unParMatch)
            if (r.ticket.size == t.size && r.message != null && r.ticket != t) remplacees++
            t = r.ticket
        }
        return Resultat(t, if (remplacees > 0) "$remplacees sélection(s) remplacée(s) : un seul pari par match." else null)
    }

    /** Passage en mode ticket : on ne garde que la dernière sélection de chaque match. */
    fun normaliser(ticket: List<JambeCombine>): List<JambeCombine> =
        ticket.reversed().distinctBy { it.matchId }.reversed()

    /** Sélections dont la cote (saisie, sinon cote juste) est sous le minimum du bonus. */
    fun horsBonus(ticket: List<JambeCombine>, coteJuste: (JambeCombine) -> Double?): List<JambeCombine> =
        ticket.filter { j -> (j.cote ?: coteJuste(j))?.let { it < COTE_MIN_BONUS } == true }
}
