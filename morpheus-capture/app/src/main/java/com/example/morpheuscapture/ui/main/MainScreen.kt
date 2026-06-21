package com.example.morpheuscapture.ui.main

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Create
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.morpheuscapture.data.DefaultDataRepository
import com.example.morpheuscapture.data.LogItem
import com.example.morpheuscapture.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val repository = remember { DefaultDataRepository(context.applicationContext) }
    val viewModel: MainScreenViewModel = viewModel {
        MainScreenViewModel(repository, context.applicationContext)
    }

    val allLogs by viewModel.allLogs.collectAsStateWithLifecycle()
    val unsyncedCount by viewModel.unsyncedCount.collectAsStateWithLifecycle()
    val serverUrl by viewModel.serverUrl.collectAsStateWithLifecycle()
    val syncState by viewModel.syncState.collectAsStateWithLifecycle()

    var selectedTab by rememberSaveable { mutableStateOf(0) }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        bottomBar = {
            NavigationBar(
                containerColor = DarkSurface,
                tonalElevation = 8.dp
            ) {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = { Icon(Icons.Default.Create, contentDescription = "Capture") },
                    label = { Text("Capture") },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = PrimaryNeon,
                        selectedTextColor = PrimaryNeon,
                        unselectedIconColor = GrayText,
                        unselectedTextColor = GrayText,
                        indicatorColor = BorderColor
                    )
                )
                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = { Icon(Icons.Default.Settings, contentDescription = "Sync & Config") },
                    label = { Text("Sync") },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = PrimaryNeon,
                        selectedTextColor = PrimaryNeon,
                        unselectedIconColor = GrayText,
                        unselectedTextColor = GrayText,
                        indicatorColor = BorderColor
                    )
                )
            }
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(DarkBg)
                .padding(innerPadding)
        ) {
            // Header Bar
            MorpheusHeader()

            if (selectedTab == 0) {
                CaptureTab(
                    unsyncedCount = unsyncedCount,
                    allLogs = allLogs,
                    onSaveLog = { text -> viewModel.saveLog(text) }
                )
            } else {
                SyncTab(
                    serverUrl = serverUrl,
                    syncState = syncState,
                    unsyncedCount = unsyncedCount,
                    onUpdateUrl = { url -> viewModel.updateServerUrl(url) },
                    onSync = { viewModel.syncLogs() },
                    onClearSynced = { viewModel.clearSyncedLogs() },
                    onResetSyncState = { viewModel.resetSyncState() }
                )
            }
        }
    }
}

@Composable
fun MorpheusHeader() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 16.dp, horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "M O R P H E U S",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = PrimaryNeon,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 4.sp
        )
        Text(
            text = "Companion Log Capture",
            fontSize = 12.sp,
            color = GrayText,
            fontFamily = FontFamily.SansSerif,
            letterSpacing = 1.sp,
            modifier = Modifier.padding(top = 4.dp)
        )
        Spacer(modifier = Modifier.height(12.dp))
        HorizontalDivider(color = BorderColor, thickness = 1.dp)
    }
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun CaptureTab(
    unsyncedCount: Int,
    allLogs: List<LogItem>,
    onSaveLog: (String) -> Unit
) {
    var logText by remember { mutableStateOf("") }
    val keyboardController = LocalSoftwareKeyboardController.current

    val suggestions = listOf(
        "Gym Workout 🏋️",
        "Meditation 🧘",
        "Coding 💻",
        "Reading 📖",
        "Productive day",
        "Meeting 👥"
    )

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Status Badge Card
        item {
            UnsyncedStatusCard(count = unsyncedCount)
        }

        // Text capture area
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor, RoundedCornerShape(16.dp))
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "New Log Entry",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = LightText
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = logText,
                        onValueChange = { logText = it },
                        placeholder = { Text("What did you accomplish?", color = GrayText) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(120.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = PrimaryNeon,
                            unfocusedBorderColor = BorderColor,
                            focusedTextColor = LightText,
                            unfocusedTextColor = LightText,
                            focusedContainerColor = DarkBg,
                            unfocusedContainerColor = DarkBg
                        ),
                        shape = RoundedCornerShape(12.dp)
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    // Suggestion chips
                    Text(
                        text = "Quick tags",
                        fontSize = 11.sp,
                        color = GrayText,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        suggestions.forEach { suggestion ->
                            SuggestionChip(
                                onClick = {
                                    logText = if (logText.trim().isEmpty()) {
                                        suggestion
                                    } else {
                                        "$logText $suggestion"
                                    }
                                },
                                label = { Text(suggestion, fontSize = 12.sp) },
                                colors = SuggestionChipDefaults.suggestionChipColors(
                                    containerColor = BorderColor,
                                    labelColor = LightText
                                ),
                                border = BorderStroke(0.dp, Color.Transparent)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = {
                            if (logText.trim().isNotEmpty()) {
                                onSaveLog(logText)
                                logText = ""
                                keyboardController?.hide()
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryNeon),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text("Save Log Entry", color = Color.Black, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        // Recent Logs Section Header
        item {
            Text(
                text = "Recent Logs",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = LightText,
                modifier = Modifier.padding(top = 8.dp)
            )
        }

        if (allLogs.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 32.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No logs captured yet.",
                        color = GrayText,
                        textAlign = TextAlign.Center
                    )
                }
            }
        } else {
            items(allLogs) { log ->
                LogCard(log = log)
            }
        }
        
        item {
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
fun UnsyncedStatusCard(count: Int) {
    val cardColor = DarkSurface
    val accentColor = if (count > 0) SecondaryNeon else GrayText
    val descriptionText = if (count > 0) {
        "$count unsynced logs ready to sync"
    } else {
        "All logs are synced up to date"
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, BorderColor, RoundedCornerShape(16.dp)),
        colors = CardDefaults.cardColors(containerColor = cardColor)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(RoundedCornerShape(5.dp))
                    .background(accentColor)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    text = "Status: Sync State",
                    fontSize = 12.sp,
                    color = GrayText
                )
                Text(
                    text = descriptionText,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = LightText
                )
            }
        }
    }
}

@Composable
fun LogCard(log: LogItem) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, BorderColor, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = DarkSurface)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                val displayDate = try {
                    val timePart = log.createdAt.substring(11, 16)
                    val datePart = log.createdAt.substring(5, 10)
                    "$datePart $timePart"
                } catch (e: Exception) {
                    log.createdAt
                }
                Text(
                    text = displayDate,
                    fontSize = 11.sp,
                    color = GrayText,
                    fontFamily = FontFamily.Monospace
                )
                
                if (log.synced) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(Color(0xFF1E3A24))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text("Synced", fontSize = 10.sp, color = SuccessGreen, fontWeight = FontWeight.Bold)
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(Color(0xFF3B2E1E))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text("Unsynced", fontSize = 10.sp, color = Color(0xFFFFB74D), fontWeight = FontWeight.Bold)
                    }
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = log.text,
                fontSize = 14.sp,
                color = LightText
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SyncTab(
    serverUrl: String,
    syncState: SyncState,
    unsyncedCount: Int,
    onUpdateUrl: (String) -> Unit,
    onSync: () -> Unit,
    onClearSynced: () -> Unit,
    onResetSyncState: () -> Unit
) {
    var urlText by remember(serverUrl) { mutableStateOf(serverUrl) }
    val keyboardController = LocalSoftwareKeyboardController.current

    DisposableEffect(Unit) {
        onDispose {
            onResetSyncState()
        }
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Server configuration card
        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor, RoundedCornerShape(16.dp)),
                colors = CardDefaults.cardColors(containerColor = DarkSurface)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Server Configuration",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = LightText
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Enter your laptop's local network IP and port",
                        fontSize = 12.sp,
                        color = GrayText
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    OutlinedTextField(
                        value = urlText,
                        onValueChange = { urlText = it },
                        placeholder = { Text("http://192.168.1.100:8000", color = GrayText) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = PrimaryNeon,
                            unfocusedBorderColor = BorderColor,
                            focusedTextColor = LightText,
                            unfocusedTextColor = LightText,
                            focusedContainerColor = DarkBg,
                            unfocusedContainerColor = DarkBg
                        ),
                        singleLine = true,
                        shape = RoundedCornerShape(12.dp)
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Button(
                        onClick = {
                            onUpdateUrl(urlText)
                            keyboardController?.hide()
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = BorderColor),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text("Save Server Configuration", color = LightText, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        // Sync Operations Card
        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor, RoundedCornerShape(16.dp)),
                colors = CardDefaults.cardColors(containerColor = DarkSurface)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Sync Control",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = LightText
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "$unsyncedCount log entries pending upload",
                        fontSize = 12.sp,
                        color = GrayText
                    )
                    Spacer(modifier = Modifier.height(16.dp))

                    // Sync State display
                    when (syncState) {
                        is SyncState.Idle -> {
                            // Empty
                        }
                        is SyncState.Syncing -> {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 8.dp),
                                horizontalArrangement = Arrangement.Center,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                CircularProgressIndicator(color = SecondaryNeon, modifier = Modifier.size(24.dp))
                                Spacer(modifier = Modifier.width(12.dp))
                                Text("Uploading logs to laptop...", color = SecondaryNeon, fontSize = 14.sp)
                            }
                        }
                        is SyncState.Success -> {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(Color(0xFF1E3A24), RoundedCornerShape(8.dp))
                                    .padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(Icons.Default.CheckCircle, contentDescription = "Success", tint = SuccessGreen)
                                Spacer(modifier = Modifier.width(12.dp))
                                Text("Logs uploaded successfully!", color = SuccessGreen, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                            }
                        }
                        is SyncState.Error -> {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(Color(0xFF3F1E24), RoundedCornerShape(8.dp))
                                    .padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(Icons.Default.Warning, contentDescription = "Error", tint = ErrorRed)
                                Spacer(modifier = Modifier.width(12.dp))
                                Text((syncState as SyncState.Error).message, color = ErrorRed, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Button(
                        onClick = onSync,
                        enabled = syncState !is SyncState.Syncing && unsyncedCount > 0,
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = SecondaryNeon,
                            disabledContainerColor = BorderColor
                        ),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.Center
                        ) {
                            Icon(Icons.Default.Refresh, contentDescription = "Sync", tint = Color.Black)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Sync Now", color = Color.Black, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        // Database Cleaning Card
        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor, RoundedCornerShape(16.dp)),
                colors = CardDefaults.cardColors(containerColor = DarkSurface)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Data Management",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = LightText
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Clear local history of successfully synchronized log entries.",
                        fontSize = 12.sp,
                        color = GrayText
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    OutlinedButton(
                        onClick = onClearSynced,
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.outlinedButtonColors(
                            contentColor = ErrorRed
                        ),
                        border = BorderStroke(1.dp, ErrorRed),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.Center
                        ) {
                            Icon(Icons.Default.Delete, contentDescription = "Delete", tint = ErrorRed)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Clean Synced Logs", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }
        
        item {
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}
