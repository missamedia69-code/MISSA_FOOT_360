package com.missa.foot360.moteur

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow

/**
 * Jumeau numérique d'un match, calculé sur le téléphone (même modèle que missa/jumeau.py).
 *
 * - BUTS    : loi jointe (score 1re mi-temps, score final) ; la part de 1re mi-temps dépend du
 *             nombre de buts du match.
 * - CORNERS : total ~ binomiale négative, réparti par une bêta-binomiale.
 * - CARTONS : Poisson bivariée (les cartons des deux équipes sont corrélés).
 *
 * Sélection : « marché[@période]:options », « | » = OU, « & » = ET. Ex. « DC:1N & OU:3.5:moins ».
 */
data class ParamsJumeau(
    val matrice: List<List<Double>>,
    val part1mt: List<Double>,        // (a, b)
    val corners: List<Double>,        // (moy dom, moy ext, k total, rho)
    val cartons: List<Double>,        // (moy dom, moy ext, covariance)
)

data class Modulation(
    val attaqueDom: Double = 1.0, val attaqueExt: Double = 1.0,
    val cornersDom: Double = 1.0, val cornersExt: Double = 1.0, val cartons: Double = 1.0,
) {
    val neutre get() = this == Modulation()
}

private const val MAX_CORNERS = 25
private const val MAX_CARTONS = 14

object Lois {
    // log Γ (approximation de Lanczos, précision ~1e-15)
    private val g = doubleArrayOf(
        0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
        -176.61502916214059, 12.507343278686905, -0.13857109526572012,
        9.9843695780195716e-6, 1.5056327351493116e-7,
    )

    fun lgamma(x: Double): Double {
        if (x < 0.5) return ln(Math.PI / kotlin.math.sin(Math.PI * x)) - lgamma(1 - x)
        val xx = x - 1
        var a = g[0]
        val t = xx + 7.5
        for (i in 1 until 9) a += g[i] / (xx + i)
        return 0.5 * ln(2 * Math.PI) + (xx + 0.5) * ln(t) - t + ln(a)
    }

    fun lnComb(n: Int, k: Int) = lgamma(n + 1.0) - lgamma(k + 1.0) - lgamma(n - k + 1.0)

    fun binom(k: Int, n: Int, p: Double): Double {
        if (k < 0 || k > n) return 0.0
        if (p <= 0) return if (k == 0) 1.0 else 0.0
        if (p >= 1) return if (k == n) 1.0 else 0.0
        return exp(lnComb(n, k) + k * ln(p) + (n - k) * ln(1 - p))
    }

    fun poisson(k: Int, l: Double): Double =
        if (l <= 0) (if (k == 0) 1.0 else 0.0) else exp(k * ln(l) - l - lgamma(k + 1.0))

    /** Binomiale négative de moyenne m, dispersion k. */
    fun nb(x: Int, k: Double, m: Double): Double {
        val p = k / (k + m)
        return exp(lgamma(x + k) - lgamma(k) - lgamma(x + 1.0) + k * ln(p) + x * ln(1 - p))
    }

    fun betabinom(x: Int, n: Int, a: Double, b: Double): Double =
        exp(lnComb(n, x) + lgamma(x + a) + lgamma(n - x + b) - lgamma(n + a + b) -
            (lgamma(a) + lgamma(b) - lgamma(a + b)))
}

class Jumeau(val p: ParamsJumeau, val modulation: Modulation = Modulation()) {
    private val n = p.matrice.size

    /** Matrice du score final après modulation (basculement exponentiel exact). */
    val matrice: Array<DoubleArray> by lazy {
        val m = Array(n) { i -> DoubleArray(n) { j ->
            p.matrice[i][j] * modulation.attaqueDom.pow(i) * modulation.attaqueExt.pow(j)
        } }
        val s = m.sumOf { it.sum() }
        m.forEach { r -> for (j in r.indices) r[j] /= s }
        m
    }

    /** G[a][b][i][j] aplati : P(1re MT = a-b, final = i-j). */
    private val buts: DoubleArray by lazy {
        val g = DoubleArray(n * n * n * n)
        val (a0, b0) = p.part1mt
        for (i in 0 until n) for (j in 0 until n) {
            val s = min(max(a0 + b0 * (i + j), 0.05), 0.95)
            val pij = matrice[i][j]
            if (pij == 0.0) continue
            for (a in 0..i) {
                val pa = Lois.binom(a, i, s)
                for (b in 0..j) g[((a * n + b) * n + i) * n + j] = pij * pa * Lois.binom(b, j, s)
            }
        }
        g
    }

    private val corners: Array<DoubleArray> by lazy {
        val md = p.corners[0] * modulation.cornersDom
        val me = p.corners[1] * modulation.cornersExt
        val k = p.corners[2]
        val rho = p.corners[3]
        val nn = MAX_CORNERS
        val mt = md + me
        val pp = md / mt
        val g = Array(nn + 1) { DoubleArray(nn + 1) }
        for (tot in 0..2 * nn) {
            val pt = Lois.nb(tot, k, mt)
            if (pt < 1e-12) continue
            for (x in 0..tot) {
                val y = tot - x
                if (x > nn || y > nn) continue
                val px = if (rho > 0) {
                    val c = 1 / rho - 1
                    Lois.betabinom(x, tot, pp * c, (1 - pp) * c)
                } else Lois.binom(x, tot, pp)
                g[x][y] += pt * px
            }
        }
        normaliser(g)
    }

    private val cartons: Array<DoubleArray> by lazy {
        val c = modulation.cartons
        val m1 = p.cartons[0] * c
        val m2 = p.cartons[1] * c
        val w = max(0.0, min(p.cartons[2] * c, 0.95 * min(m1, m2)))
        val u = m1 - w
        val v = m2 - w
        val nn = MAX_CARTONS
        val g = Array(nn + 1) { DoubleArray(nn + 1) }
        for (k in 0..nn) {
            val pw = Lois.poisson(k, w)
            for (x in k..nn) for (y in k..nn) g[x][y] += pw * Lois.poisson(x - k, u) * Lois.poisson(y - k, v)
        }
        normaliser(g)
    }

    private fun normaliser(g: Array<DoubleArray>): Array<DoubleArray> {
        val s = g.sumOf { it.sum() }
        g.forEach { r -> for (j in r.indices) r[j] /= s }
        return g
    }

    // ------------------------------------------------------------------ évaluation
    fun proba(selection: String): Double = proba(listOf(selection))

    fun proba(selections: List<String>): Double {
        val expr = selections.joinToString(" & ")
        val parComp = mutableMapOf<String, MutableList<List<String>>>()
        for (disj in expr.split("&")) {
            val termes = disj.split("|").map { it.trim() }.filter { it.isNotEmpty() }
            val comps = termes.map { composante(it) }.toSet()
            require(comps.size == 1) { "Un « ou » doit porter sur une seule famille" }
            parComp.getOrPut(comps.first()) { mutableListOf() }.add(termes)
        }
        var res = 1.0
        for ((comp, conj) in parComp) {
            res *= when (comp) {
                "buts" -> {
                    var s = 0.0
                    for (a in 0 until n) for (b in 0 until n) for (i in a until n) for (j in b until n) {
                        val pr = buts[((a * n + b) * n + i) * n + j]
                        if (pr == 0.0) continue
                        if (conj.all { d -> d.any { termeButs(it, a, b, i, j) } }) s += pr
                    }
                    s
                }
                else -> {
                    val g = if (comp == "corners") corners else cartons
                    var s = 0.0
                    for (x in g.indices) for (y in g[x].indices) {
                        if (g[x][y] == 0.0) continue
                        if (conj.all { d -> d.any { termeComptage(it, x, y) } }) s += g[x][y]
                    }
                    s
                }
            }
        }
        return res
    }

    companion object {
        fun composante(code: String) = when {
            code.startsWith("CORNERS_") -> "corners"
            code.startsWith("CARTONS_") -> "cartons"
            else -> "buts"
        }

        private fun ou(total: Int, ligne: Double, sens: String) =
            if (sens == "plus") total > ligne else total < ligne

        private fun res(x: Double, y: Double, o: String) = when (o) {
            "1" -> x > y; "N" -> x == y; "2" -> x < y
            "1N" -> x >= y; "12" -> x != y; "N2" -> x <= y
            else -> error("option $o")
        }

        private fun res(x: Int, y: Int, o: String) = res(x.toDouble(), y.toDouble(), o)

        private fun bornes(t: String): Pair<Int, Int> = when {
            t.endsWith("+") -> t.dropLast(1).toInt() to Int.MAX_VALUE
            t.contains("-") -> t.split("-").let { it[0].toInt() to it[1].toInt() }
            else -> t.toInt() to t.toInt()
        }

        private fun dans(v: Int, t: String) = bornes(t).let { (lo, hi) -> v in lo..hi }

        fun termeButs(code: String, a: Int, b: Int, i: Int, j: Int): Boolean {
            val parts = code.split(":")
            var nom = parts[0]
            val o = parts.drop(1)
            var periode = "FT"
            if ("@" in nom) nom.split("@").let { nom = it[0]; periode = it[1] }
            val (x, y) = when (periode) { "MT1" -> a to b; "MT2" -> (i - a) to (j - b); else -> i to j }
            fun eq(s: String) = if (s == "dom") x else y
            val a2 = i - a
            val b2 = j - b
            return when (nom) {
                "1X2", "DC" -> res(x, y, o[0])
                "OU" -> ou(x + y, o[0].toDouble(), o[1])
                "BTTS" -> ((x > 0) && (y > 0)) == (o[0] == "oui")
                "CS" -> o[0].split("-").let { x == it[0].toInt() && y == it[1].toInt() }
                "TG", "MG" -> dans(x + y, o[0])
                "PI" -> (x + y) % 2 == (if (o[0] == "pair") 0 else 1)
                "MARGE" -> if (o[0] == "nul") x == y else {
                    val d = if (o[0].startsWith("dom")) x - y else y - x
                    dans(d, o[0].substring(3))
                }
                "EQ_OU" -> ou(eq(o[0]), o[1].toDouble(), o[2])
                "EQ_TG" -> dans(eq(o[0]), o[1])
                "EQ_PI" -> eq(o[0]) % 2 == (if (o[1] == "pair") 0 else 1)
                "MARQUE" -> (eq(o[0]) > 0) == (o[1] == "oui")
                "CLEAN" -> ((if (o[0] == "dom") y else x) == 0) == (o[1] == "oui")
                "SANS_ENC" -> if (o[0] == "dom") x > y && y == 0 else y > x && x == 0
                "HCP3" -> res(x + o[0].toDouble(), y.toDouble(), o[1])
                "HCP2" -> if (o[1] == "1") x + o[0].toDouble() > y else x + o[0].toDouble() < y
                "MTFT" -> o[0].split("/").let { res(a, b, it[0]) && res(i, j, it[1]) }
                "MT_PLUS" -> when (o[0]) { "MT1" -> a + b > a2 + b2; "MT2" -> a2 + b2 > a + b; else -> a + b == a2 + b2 }
                "GAGNE_2MT" -> if (o[0] == "dom") a > b && a2 > b2 else b > a && b2 > a2
                "GAGNE_1MT" -> if (o[0] == "dom") a > b || a2 > b2 else b > a || b2 > a2
                "MARQUE_2MT" -> if (o[0] == "dom") a > 0 && a2 > 0 else b > 0 && b2 > 0
                "OU_2MT" -> ou(a + b, o[0].toDouble(), o[1]) && ou(a2 + b2, o[0].toDouble(), o[1])
                else -> error("Marché inconnu : $nom")
            }
        }

        fun termeComptage(code: String, x: Int, y: Int): Boolean {
            val parts = code.split(":")
            val nom = parts[0].substringAfter("_")
            val o = parts.drop(1)
            return when (nom) {
                "OU" -> ou(x + y, o[0].toDouble(), o[1])
                "1X2" -> res(x, y, o[0])
                "EQ_OU" -> ou(if (o[0] == "dom") x else y, o[1].toDouble(), o[2])
                "HCP2" -> if (o[1] == "1") x + o[0].toDouble() > y else x + o[0].toDouble() < y
                "PI" -> (x + y) % 2 == (if (o[0] == "pair") 0 else 1)
                "TOTAL" -> dans(x + y, o[0])
                else -> error("Marché inconnu : $nom")
            }
        }

        /** Ancien code de sélection -> code du jumeau. */
        fun depuisAncien(code: String): String = when (code) {
            "1", "N", "2" -> "1X2:$code"
            "1N", "12", "N2" -> "DC:$code"
            "btts_oui" -> "BTTS:oui"
            "btts_non" -> "BTTS:non"
            else -> if (code.startsWith("plus_") || code.startsWith("moins_"))
                "OU:${code.substringAfter("_")}:${code.substringBefore("_")}" else code
        }
    }
}

data class JambeCombine(
    val matchId: String,
    val code: String,
    val libelleMatch: String,
    val libelle: String,
    val cote: Double? = null,
)

data class ResultatCombine(
    val proba: Double,
    val coteJuste: Double?,
    val coteBookmaker: Double?,
    val valeurAttendue: Double?,
    val memeMatch: Boolean,
    val probaParMatch: Map<String, Double>,
)

fun calculerCombine(
    jambes: List<JambeCombine>,
    jumeaux: Map<String, Jumeau>,
    bonus: Double = 0.0,
): ResultatCombine {
    val parMatch = jambes.groupBy { it.matchId }
    val pm = parMatch.mapValues { (id, js) -> jumeaux[id]?.proba(js.map { it.code }) ?: 0.0 }
    val p = if (jambes.isEmpty()) 0.0 else pm.values.fold(1.0) { x, y -> x * y }
    val cotes = jambes.map { it.cote }
    val bk = if (jambes.isNotEmpty() && cotes.all { it != null && it > 1.0 }) cotes.fold(1.0) { x, y -> x * y!! } else null
    return ResultatCombine(
        proba = p,
        coteJuste = if (p > 0) 1 / p else null,
        coteBookmaker = bk,
        valeurAttendue = bk?.let { p * it * (1 + bonus) - 1 },
        memeMatch = parMatch.values.any { it.size > 1 },
        probaParMatch = pm,
    )
}

@Suppress("unused")
private fun presque(a: Double, b: Double) = abs(a - b) < 1e-9
