package com.missa.foot360

import com.missa.foot360.moteur.SelectionCombi
import com.missa.foot360.moteur.Selections
import com.missa.foot360.moteur.calculerCombinaison
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.exp
import kotlin.math.pow

class CombinaisonTest {
    private fun poisson(k: Int, l: Double): Double = exp(-l) * l.pow(k) / (1..k).fold(1.0) { a, b -> a * b }

    private fun matrice(lam: Double, mu: Double): List<List<Double>> {
        val m = List(10) { i -> List(10) { j -> poisson(i, lam) * poisson(j, mu) } }
        val s = m.sumOf { it.sum() }
        return m.map { r -> r.map { it / s } }
    }

    private val a = matrice(1.6, 1.0)
    private val b = matrice(1.2, 1.3)

    @Test
    fun selectionsSimples() {
        val total = Selections.proba(a, listOf("1")) + Selections.proba(a, listOf("N")) +
            Selections.proba(a, listOf("2"))
        assertEquals(1.0, total, 1e-9)
        assertEquals(1.0, Selections.proba(a, listOf("plus_2.5")) + Selections.proba(a, listOf("moins_2.5")), 1e-9)
    }

    @Test
    fun matchsDifferentsMultiplies() {
        val r = calculerCombinaison(
            listOf(SelectionCombi("a", "1", "A", 1.8), SelectionCombi("b", "N", "B", 3.4)),
            mapOf("a" to a, "b" to b),
        )
        assertEquals(Selections.proba(a, listOf("1")) * Selections.proba(b, listOf("N")), r.proba, 1e-12)
        assertEquals(1.8 * 3.4, r.coteBookmaker!!, 1e-9)
        assertTrue(!r.memeMatch)
    }

    @Test
    fun memeMatchCorrele() {
        val r = calculerCombinaison(
            listOf(SelectionCombi("a", "1", "A"), SelectionCombi("a", "plus_2.5", "A")),
            mapOf("a" to a),
        )
        assertEquals(Selections.proba(a, listOf("1", "plus_2.5")), r.proba, 1e-12)
        assertTrue(r.memeMatch)
        val incompatible = calculerCombinaison(
            listOf(SelectionCombi("a", "1", "A"), SelectionCombi("a", "2", "A")), mapOf("a" to a))
        assertEquals(0.0, incompatible.proba, 0.0)
    }

    @Test
    fun scoreExact() {
        assertEquals(a[2][1], Selections.proba(a, listOf("score:2-1")), 1e-12)
    }
}
