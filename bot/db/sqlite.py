from pathlib import Path

import aiosqlite

from bot.utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        if self._connection is None:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = await aiosqlite.connect(self.database_path)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA foreign_keys = ON;")
            logger.info("Connected to SQLite database at %s", self.database_path)
        return self._connection

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
            logger.info("SQLite connection closed")

    async def execute(self, query: str, params: tuple | list = ()) -> aiosqlite.Cursor:
        conn = await self.connect()
        return await conn.execute(query, params)

    async def executemany(self, query: str, params_seq: list[tuple]) -> aiosqlite.Cursor:
        conn = await self.connect()
        return await conn.executemany(query, params_seq)

    async def commit(self) -> None:
        conn = await self.connect()
        await conn.commit()
