package com.missa.foot360

import com.missa.foot360.moteur.Jumeau
import com.missa.foot360.moteur.JambeCombine
import com.missa.foot360.moteur.Modulation
import com.missa.foot360.moteur.ParamsJumeau
import com.missa.foot360.moteur.calculerCombine
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.double
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Le moteur du téléphone doit donner exactement les mêmes probabilités que le moteur Python. */
class JumeauPariteTest {
    private fun params(o: JsonObject) = ParamsJumeau(
        o["matrice"]!!.jsonArray.map { r -> r.jsonArray.map { it.jsonPrimitive.double } },
        o["part_1mt"]!!.jsonArray.map { it.jsonPrimitive.double },
        o["corners"]!!.jsonArray.map { it.jsonPrimitive.double },
        o["cartons"]!!.jsonArray.map { it.jsonPrimitive.double },
    )

    @Test
    fun memesResultatsQuePython() {
        val txt = javaClass.classLoader!!.getResource("vecteurs_jumeau.json").readText()
        val cas = Json.parseToJsonElement(txt).jsonArray
        val cache = HashMap<String, Jumeau>()
        var ecartMax = 0.0
        for (c in cas) {
            val o = c.jsonObject
            val mod = o["modulation"]!!.jsonObject
            fun m(k: String) = mod[k]?.jsonPrimitive?.double ?: 1.0
            val modulation = Modulation(m("attaque_dom"), m("attaque_ext"), m("corners_dom"), m("corners_ext"), m("cartons"))
            val cle = o["jumeau"].toString() + modulation
            val j = cache.getOrPut(cle) { Jumeau(params(o["jumeau"]!!.jsonObject), modulation) }
            val attendu = o["proba"]!!.jsonPrimitive.double
            val obtenu = j.proba(o["selection"]!!.jsonPrimitive.content)
            ecartMax = maxOf(ecartMax, kotlin.math.abs(attendu - obtenu))
            assertEquals("${o["selection"]} $modulation", attendu, obtenu, 1e-6)
        }
        println("Cas comparés : ${cas.size}, écart maximal : $ecartMax")
    }

    @Test
    fun combineMultiMatchs() {
        val p = ParamsJumeau(
            List(10) { i -> List(10) { j -> if (i + j < 6) 1.0 / 21 else 0.0 } },
            listOf(0.418, 0.0086), listOf(5.3, 4.4, 56.0, 0.087), listOf(1.9, 2.1, 0.33),
        )
        val a = Jumeau(p)
        val r = calculerCombine(
            listOf(JambeCombine("a", "1X2:1", "A", "1", 2.0), JambeCombine("b", "OU:2.5:plus", "B", "+2,5", 1.8)),
            mapOf("a" to a, "b" to a), bonus = 0.1,
        )
        assertEquals(a.proba("1X2:1") * a.proba("OU:2.5:plus"), r.proba, 1e-12)
        assertEquals(r.proba * 3.6 * 1.1 - 1, r.valeurAttendue!!, 1e-9)
        assertTrue(Jumeau(p, Modulation(attaqueDom = 0.7)).proba("1X2:1") < a.proba("1X2:1"))
    }
}
