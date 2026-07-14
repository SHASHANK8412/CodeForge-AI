from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock


class ConversationDatabase:

    def __init__(self, database_path: Path | None = None):
        self.storage_root = Path(__file__).resolve().parent / "store"
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.database_path = database_path or (self.storage_root / "conversation_memory.db")
        self._initialized = False
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return

            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_opened_at TEXT NOT NULL,
                        message_count INTEGER NOT NULL DEFAULT 0
                    );

                    CREATE TABLE IF NOT EXISTS messages (
                        message_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id)
                            REFERENCES conversations (conversation_id)
                            ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
                        ON conversations(updated_at DESC);

                    CREATE INDEX IF NOT EXISTS idx_conversations_last_opened_at
                        ON conversations(last_opened_at DESC);

                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_timestamp
                        ON messages(conversation_id, timestamp ASC);
                    """
                )

            self._initialized = True

    @contextmanager
    def connection(self):
        self._initialize()
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
