package com.example.morpheuscapture.data

data class LogItem(
    val id: String,
    val text: String,
    val createdAt: String, // ISO 8601 timestamp (e.g. "2026-06-21T12:00:00Z")
    val synced: Boolean
)
