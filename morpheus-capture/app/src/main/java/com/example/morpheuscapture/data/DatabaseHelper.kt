package com.example.morpheuscapture.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import java.util.UUID

class DatabaseHelper(context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    companion object {
        private const val DATABASE_NAME = "morpheus_logs.db"
        private const val DATABASE_VERSION = 1
        private const val TABLE_NAME = "logs"
        private const val COL_ID = "id"
        private const val COL_TEXT = "text"
        private const val COL_CREATED_AT = "created_at"
        private const val COL_SYNCED = "synced"
    }

    override fun onCreate(db: SQLiteDatabase) {
        val createTable = ("CREATE TABLE " + TABLE_NAME + " ("
                + COL_ID + " TEXT PRIMARY KEY, "
                + COL_TEXT + " TEXT, "
                + COL_CREATED_AT + " TEXT, "
                + COL_SYNCED + " INTEGER)")
        db.execSQL(createTable)
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS $TABLE_NAME")
        onCreate(db)
    }

    fun insertLog(text: String, createdAtIso: String): String {
        val db = this.writableDatabase
        val id = UUID.randomUUID().toString()
        val contentValues = ContentValues().apply {
            put(COL_ID, id)
            put(COL_TEXT, text)
            put(COL_CREATED_AT, createdAtIso)
            put(COL_SYNCED, 0)
        }
        db.insert(TABLE_NAME, null, contentValues)
        return id
    }

    fun getAllLogs(): List<LogItem> {
        val list = mutableListOf<LogItem>()
        val db = this.readableDatabase
        val query = "SELECT * FROM $TABLE_NAME ORDER BY $COL_CREATED_AT DESC"
        val cursor = db.rawQuery(query, null)
        if (cursor.moveToFirst()) {
            val idxId = cursor.getColumnIndexOrThrow(COL_ID)
            val idxText = cursor.getColumnIndexOrThrow(COL_TEXT)
            val idxCreatedAt = cursor.getColumnIndexOrThrow(COL_CREATED_AT)
            val idxSynced = cursor.getColumnIndexOrThrow(COL_SYNCED)
            do {
                val id = cursor.getString(idxId)
                val text = cursor.getString(idxText)
                val createdAt = cursor.getString(idxCreatedAt)
                val synced = cursor.getInt(idxSynced) == 1
                list.add(LogItem(id, text, createdAt, synced))
            } while (cursor.moveToNext())
        }
        cursor.close()
        return list
    }

    fun getUnsyncedLogs(): List<LogItem> {
        val list = mutableListOf<LogItem>()
        val db = this.readableDatabase
        val query = "SELECT * FROM $TABLE_NAME WHERE $COL_SYNCED = 0 ORDER BY $COL_CREATED_AT DESC"
        val cursor = db.rawQuery(query, null)
        if (cursor.moveToFirst()) {
            val idxId = cursor.getColumnIndexOrThrow(COL_ID)
            val idxText = cursor.getColumnIndexOrThrow(COL_TEXT)
            val idxCreatedAt = cursor.getColumnIndexOrThrow(COL_CREATED_AT)
            val idxSynced = cursor.getColumnIndexOrThrow(COL_SYNCED)
            do {
                val id = cursor.getString(idxId)
                val text = cursor.getString(idxText)
                val createdAt = cursor.getString(idxCreatedAt)
                val synced = cursor.getInt(idxSynced) == 1
                list.add(LogItem(id, text, createdAt, synced))
            } while (cursor.moveToNext())
        }
        cursor.close()
        return list
    }

    fun markAsSynced(ids: List<String>) {
        if (ids.isEmpty()) return
        val db = this.writableDatabase
        db.beginTransaction()
        try {
            val contentValues = ContentValues().apply {
                put(COL_SYNCED, 1)
            }
            for (id in ids) {
                db.update(TABLE_NAME, contentValues, "$COL_ID = ?", arrayOf(id))
            }
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
    }

    fun deleteSyncedLogs() {
        val db = this.writableDatabase
        db.delete(TABLE_NAME, "$COL_SYNCED = 1", null)
    }
}
