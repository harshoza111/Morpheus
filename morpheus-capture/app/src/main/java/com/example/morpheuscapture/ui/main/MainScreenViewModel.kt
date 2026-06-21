package com.example.morpheuscapture.ui.main

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.morpheuscapture.data.DataRepository
import com.example.morpheuscapture.data.LogItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface SyncState {
    object Idle : SyncState
    object Syncing : SyncState
    object Success : SyncState
    data class Error(val message: String) : SyncState
}

class MainScreenViewModel(
    private val dataRepository: DataRepository,
    context: Context
) : ViewModel() {

    private val sharedPrefs = context.getSharedPreferences("morpheus_prefs", Context.MODE_PRIVATE)

    private val _serverUrl = MutableStateFlow(
        sharedPrefs.getString("server_url", "http://192.168.1.100:8000") ?: "http://192.168.1.100:8000"
    )
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()

    private val _syncState = MutableStateFlow<SyncState>(SyncState.Idle)
    val syncState: StateFlow<SyncState> = _syncState.asStateFlow()

    val allLogs: StateFlow<List<LogItem>> = dataRepository.allLogs
    val unsyncedCount: StateFlow<Int> = dataRepository.unsyncedCount

    fun saveLog(text: String) {
        if (text.trim().isNotEmpty()) {
            dataRepository.saveLog(text)
        }
    }

    fun updateServerUrl(url: String) {
        _serverUrl.value = url
        sharedPrefs.edit().putString("server_url", url).apply()
    }

    fun syncLogs() {
        viewModelScope.launch {
            _syncState.value = SyncState.Syncing
            val success = dataRepository.syncLogs(_serverUrl.value)
            if (success) {
                _syncState.value = SyncState.Success
            } else {
                _syncState.value = SyncState.Error("Sync failed. Check server URL and network.")
            }
        }
    }

    fun clearSyncedLogs() {
        dataRepository.clearSyncedLogs()
    }

    fun resetSyncState() {
        _syncState.value = SyncState.Idle
    }
}
