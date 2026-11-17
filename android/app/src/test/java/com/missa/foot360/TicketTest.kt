package com.missa.foot360

import com.missa.foot360.moteur.JambeCombine
import com.missa.foot360.moteur.RegleTicket
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class TicketTest {
    private fun j(m: String, c: String, cote: Double? = null) = JambeCombine(m, c, m, c, cote)

    @Test
    fun unSeulPariParMatch() {
        var r = RegleTicket.basculer(emptyList(), j("a", "1X2:1"), true)
        r = RegleTicket.basculer(r.ticket, j("b", "OU:2.5:plus"), true)
        r = RegleTicket.basculer(r.ticket, j("a", "BTTS:oui"), true)   // même match : remplace
        assertEquals(listOf("BTTS:oui", "OU:2.5:plus"), r.ticket.map { it.code })
        assertNotNull(r.message)
        // un combiné officiel est UNE sélection
        r = RegleTicket.basculer(r.ticket, j("a", "1X2:1 & BTTS:oui"), true)
        assertEquals(2, r.ticket.size)
        // toucher à nouveau la même option la retire
        r = RegleTicket.basculer(r.ticket, j("b", "OU:2.5:plus"), true)
        assertEquals(listOf("1X2:1 & BTTS:oui"), r.ticket.map { it.code })
        assertNull(r.message)
    }

    @Test
    fun modeAnalyseLibre() {
        var r = RegleTicket.basculer(emptyList(), j("a", "1X2:1"), false)
        r = RegleTicket.basculer(r.ticket, j("a", "BTTS:oui"), false)
        assertEquals(2, r.ticket.size)
        assertEquals(listOf("BTTS:oui"), RegleTicket.normaliser(r.ticket).map { it.code })
    }

    @Test
    fun limitesEtBonus() {
        var t = (1..60).map { j("m$it", "1X2:1") }
        val r = RegleTicket.basculer(t, j("m61", "1X2:1"), true)
        assertEquals(60, r.ticket.size)
        assertNotNull(r.message)
        t = listOf(j("a", "DC:1N", 1.05), j("b", "1X2:1", 1.8), j("c", "1X2:1"))
        val hors = RegleTicket.horsBonus(t) { if (it.matchId == "c") 1.08 else 2.0 }
        assertEquals(listOf("a", "c"), hors.map { it.matchId })
    }

    @Test
    fun assistantRemplace() {
        val t = listOf(j("a", "1X2:1"), j("b", "1X2:2"))
        val r = RegleTicket.ajouterPlusieurs(t, listOf(j("a", "DC:1N"), j("c", "OU:1.5:plus")), true)
        assertEquals(listOf("DC:1N", "1X2:2", "OU:1.5:plus"), r.ticket.map { it.code })
    }
}
