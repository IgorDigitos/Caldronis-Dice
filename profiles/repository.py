import asyncio
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Repository:
    """Uma conexão por operação; transações executadas fora do event loop."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=5)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            with conn:
                yield conn
        finally:
            conn.close()

    async def initialize(self):
        await asyncio.to_thread(self._initialize)

    def _initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS profiles (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS attributes (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    name_normalized TEXT NOT NULL CHECK(length(name_normalized) BETWEEN 1 AND 32),
                    value INTEGER NOT NULL CHECK(value BETWEEN -1000000000 AND 1000000000),
                    PRIMARY KEY (guild_id, user_id, name_normalized),
                    FOREIGN KEY (guild_id, user_id) REFERENCES profiles(guild_id, user_id)
                        ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    master_role_id INTEGER NOT NULL
                );
            """)

    async def attributes(self, guild_id: int, user_id: int) -> dict[str, int]:
        return await asyncio.to_thread(self._attributes, guild_id, user_id)

    def _attributes(self, guild_id, user_id):
        with self.connection() as conn:
            return dict(
                conn.execute(
                    "SELECT name_normalized, value FROM attributes "
                    "WHERE guild_id=? AND user_id=? ORDER BY name_normalized",
                    (guild_id, user_id),
                )
            )

    async def set_attribute(self, guild_id: int, user_id: int, name: str, value: int):
        await asyncio.to_thread(self._set_attribute, guild_id, user_id, name, value)

    def _set_attribute(self, guild_id, user_id, name, value):
        with self.connection() as conn:
            # Serializa contagem e inserção para respeitar o limite mesmo sob concorrência.
            conn.execute("BEGIN IMMEDIATE")
            count = conn.execute(
                "SELECT COUNT(*) FROM attributes WHERE guild_id=? AND user_id=?",
                (guild_id, user_id),
            ).fetchone()[0]
            exists = conn.execute(
                "SELECT 1 FROM attributes WHERE guild_id=? AND user_id=? AND name_normalized=?",
                (guild_id, user_id, name),
            ).fetchone()
            if count >= 40 and not exists:
                raise ValueError(
                    "Máximo de 40 atributos por perfil; remova um antes de criar outro."
                )
            conn.execute(
                "INSERT OR IGNORE INTO profiles(guild_id, user_id) VALUES (?, ?)",
                (guild_id, user_id),
            )
            conn.execute(
                "INSERT INTO attributes VALUES (?, ?, ?, ?) ON CONFLICT "
                "(guild_id, user_id, name_normalized) DO UPDATE SET value=excluded.value",
                (guild_id, user_id, name, value),
            )
            conn.execute(
                "UPDATE profiles SET updated_at=CURRENT_TIMESTAMP WHERE guild_id=? AND user_id=?",
                (guild_id, user_id),
            )

    async def remove_attribute(self, guild_id: int, user_id: int, name: str) -> bool:
        return await asyncio.to_thread(self._remove_attribute, guild_id, user_id, name)

    def _remove_attribute(self, guild_id, user_id, name):
        with self.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM attributes WHERE guild_id=? AND user_id=? AND name_normalized=?",
                (guild_id, user_id, name),
            )
            if cursor.rowcount:
                conn.execute(
                    "UPDATE profiles SET updated_at=CURRENT_TIMESTAMP "
                    "WHERE guild_id=? AND user_id=?",
                    (guild_id, user_id),
                )
            return cursor.rowcount > 0

    async def master_role(self, guild_id: int) -> int | None:
        return await asyncio.to_thread(self._master_role, guild_id)

    def _master_role(self, guild_id):
        with self.connection() as conn:
            row = conn.execute(
                "SELECT master_role_id FROM guild_settings WHERE guild_id=?", (guild_id,)
            ).fetchone()
            return row[0] if row else None

    async def set_master_role(self, guild_id: int, role_id: int):
        await asyncio.to_thread(self._set_master_role, guild_id, role_id)

    def _set_master_role(self, guild_id, role_id):
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO guild_settings VALUES (?, ?) ON CONFLICT(guild_id) "
                "DO UPDATE SET master_role_id=excluded.master_role_id",
                (guild_id, role_id),
            )
