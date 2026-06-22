import logging
import aiosqlite

logger = logging.getLogger(__name__)
DB_PATH = "bot.db"


async def init_sqlite() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS welcome_messages (
                chat_id INTEGER PRIMARY KEY,
                message TEXT    NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS buttons (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                label   TEXT    NOT NULL,
                url     TEXT    NOT NULL
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_buttons_chat ON buttons(chat_id)"
        )
        await db.commit()
    logger.info("SQLite initialised at %s", DB_PATH)


# ── Welcome messages ──────────────────────────────────────────────────────────

async def get_welcome_message(chat_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT message FROM welcome_messages WHERE chat_id = ?", (chat_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def set_welcome_message(chat_id: int, message: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO welcome_messages (chat_id, message) VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET message = excluded.message
            """,
            (chat_id, message),
        )
        await db.commit()


async def delete_welcome_message(chat_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM welcome_messages WHERE chat_id = ?", (chat_id,)
        )
        await db.commit()
        return cur.rowcount > 0


# ── Buttons ───────────────────────────────────────────────────────────────────

async def get_buttons(chat_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, label, url FROM buttons WHERE chat_id = ? ORDER BY id",
            (chat_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [{"id": r[0], "label": r[1], "url": r[2]} for r in rows]


async def add_button(chat_id: int, label: str, url: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO buttons (chat_id, label, url) VALUES (?, ?, ?)",
            (chat_id, label, url),
        )
        await db.commit()
        return cur.lastrowid  # type: ignore[return-value]


async def delete_button(button_id: int, chat_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM buttons WHERE id = ? AND chat_id = ?", (button_id, chat_id)
        )
        await db.commit()
        return cur.rowcount > 0


async def delete_all_buttons(chat_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM buttons WHERE chat_id = ?", (chat_id,)
        )
        await db.commit()
        return cur.rowcount
