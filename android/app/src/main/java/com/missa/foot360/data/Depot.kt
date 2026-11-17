package com.missa.foot360.data

import android.content.Context
import com.missa.foot360.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

/** Accès aux données : API du moteur, avec repli sur des données de démonstration hors ligne. */
class Depot(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true; isLenient = true; coerceInputValues = true }
    private val client = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    private val prefs = context.getSharedPreferences("missa", Context.MODE_PRIVATE)

    var urlApi: String
        get() = prefs.getString("url_api", BuildConfig.API_PAR_DEFAUT) ?: BuildConfig.API_PAR_DEFAUT
        set(v) = prefs.edit().putString("url_api", v.trim().trimEnd('/')).apply()

    /** Mode « analyse libre » : plusieurs sélections par match (non jouable chez un bookmaker). */
    var plusieursParMatch: Boolean
        get() = prefs.getBoolean("plusieurs_par_match", false)
        set(v) = prefs.edit().putBoolean("plusieurs_par_match", v).apply()

    var majeurConfirme: Boolean
        get() = prefs.getBoolean("majeur", false)
        set(v) = prefs.edit().putBoolean("majeur", v).apply()

    data class Chargement(val pronostics: Pronostics, val horsLigne: Boolean, val erreur: String?)

    /** Mode « fichier » : l'adresse pointe vers un pronostics.json publié (GitHub Actions). */
    private val modeFichier get() = urlApi.endsWith(".json")

    private fun get(chemin: String): String {
        val url = if (modeFichier) urlApi.substringBeforeLast('/') + "/" + chemin else urlApi + chemin
        val req = Request.Builder().url(url).header("Cache-Control", "no-cache").build()
        client.newCall(req).execute().use { r ->
            if (!r.isSuccessful) error("HTTP ${r.code}")
            return r.body?.string() ?: error("Réponse vide")
        }
    }

    suspend fun pronostics(): Chargement = withContext(Dispatchers.IO) {
        try {
            Chargement(json.decodeFromString<Pronostics>(get(if (modeFichier) "pronostics.json" else "/matchs?avec_matrice=true")), false, null)
        } catch (e: Exception) {
            val demo = context.assets.open("demo.json").bufferedReader().use { it.readText() }
            Chargement(json.decodeFromString<Pronostics>(demo), true, e.message)
        }
    }

    suspend fun pronostiqueurs(): List<NotePronostiqueur> = withContext(Dispatchers.IO) {
        try {
            json.decodeFromString<List<NotePronostiqueur>>(get(if (modeFichier) "pronostiqueurs.json" else "/pronostiqueurs"))
        } catch (e: Exception) {
            emptyList()
        }
    }
}
