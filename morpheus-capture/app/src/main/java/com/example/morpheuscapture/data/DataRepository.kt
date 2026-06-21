package com.example.morpheuscapture.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

interface DataRepository {
    val allLogs: StateFlow<List<LogItem>>
    val unsyncedCount: StateFlow<Int>

    fun refresh()
    fun saveLog(text: String)
    suspend fun syncLogs(serverUrl: String): Boolean
    fun clearSyncedLogs()
}

class DefaultDataRepository(context: Context) : DataRepository {
    private val dbHelper = DatabaseHelper(context)
    
    private val _allLogs = MutableStateFlow<List<LogItem>>(emptyList())
    override val allLogs: StateFlow<List<LogItem>> = _allLogs.asStateFlow()

    private val _unsyncedCount = MutableStateFlow(0)
    override val unsyncedCount: StateFlow<Int> = _unsyncedCount.asStateFlow()

    init {
        refresh()
    }

    override fun refresh() {
        val logs = dbHelper.getAllLogs()
        _allLogs.value = logs
        _unsyncedCount.value = logs.count { !it.synced }
    }

    override fun saveLog(text: String) {
        val isoTimestamp = getCurrentIsoTimestamp()
        dbHelper.insertLog(text, isoTimestamp)
        refresh()
    }

    override fun clearSyncedLogs() {
        dbHelper.deleteSyncedLogs()
        refresh()
    }

    override suspend fun syncLogs(serverUrl: String): Boolean = withContext(Dispatchers.IO) {
        val unsynced = dbHelper.getUnsyncedLogs()
        if (unsynced.isEmpty()) {
            return@withContext true
        }

        var connection: HttpURLConnection? = null
        try {
            val cleanedUrl = serverUrl.trim().removeSuffix("/")
            val url = URL("$cleanedUrl/sync")
            connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 15000
            connection.readTimeout = 60000
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json; utf-8")
            connection.setRequestProperty("Accept", "application/json")

            // Build JSON matching SyncPayload: { "logs": [ { "id": "...", "text": "...", "created_at": "..." } ] }
            val payload = JSONObject()
            val logsArray = JSONArray()
            for (log in unsynced) {
                val logObj = JSONObject()
                logObj.put("id", log.id)
                logObj.put("text", log.text)
                logObj.put("created_at", log.createdAt)
                logsArray.put(logObj)
            }
            payload.put("logs", logsArray)

            val jsonInputString = payload.toString()
            connection.outputStream.use { os ->
                val input = jsonInputString.toByteArray(Charsets.UTF_8)
                os.write(input, 0, input.size)
            }

            val responseCode = connection.responseCode
            if (responseCode == HttpURLConnection.HTTP_OK) {
                val responseText = connection.inputStream.bufferedReader().use { it.readText() }
                val responseJson = JSONObject(responseText)
                val isSuccess = responseJson.optBoolean("success", false)
                if (isSuccess) {
                    // Update database
                    dbHelper.markAsSynced(unsynced.map { it.id })
                    withContext(Dispatchers.Main) {
                        refresh()
                    }
                    return@withContext true
                }
            }
            false
        } catch (e: Exception) {
            e.printStackTrace()
            false
        } finally {
            connection?.disconnect()
        }
    }

    private fun getCurrentIsoTimestamp(): String {
        val df = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)
        df.timeZone = TimeZone.getTimeZone("UTC")
        return df.format(Date())
    }
}
