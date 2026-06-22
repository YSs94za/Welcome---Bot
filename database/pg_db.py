import logging
import asyncpg
from config import DATABASE_URL

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
        )
        logger.info("PostgreSQL pool created")
    return _pool


async def init_postgres() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS welcome_messages (
                chat_id BIGINT PRIMARY KEY,
                message TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS buttons (
                id      SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                label   TEXT   NOT NULL,
                url     TEXT   NOT NULL
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_buttons_chat ON buttons(chat_id)"
        )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id         SERIAL PRIMARY KEY,
                channel_id BIGINT UNIQUE NOT NULL,
                username   TEXT,
                title      TEXT,
                added_by   BIGINT,
                added_at   TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS known_chats (
                chat_id      BIGINT PRIMARY KEY,
                chat_type    TEXT NOT NULL,
                title        TEXT,
                username     TEXT,
                registered_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at   TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    logger.info("PostgreSQL schema ready (welcome_messages, buttons, channels, known_chats)")


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Welcome messages ───────────────────────────────────────────────────────────

async def get_welcome_message(chat_id: int) -> str | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT message FROM welcome_messages WHERE chat_id = $1", chat_id
        )
        return row["message"] if row else None


async def set_welcome_message(chat_id: int, message: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO welcome_messages (chat_id, message) VALUES ($1, $2)
            ON CONFLICT (chat_id) DO UPDATE SET message = EXCLUDED.message
            """,
            chat_id, message,
        )


async def delete_welcome_message(chat_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM welcome_messages WHERE chat_id = $1", chat_id
        )
        return result.split()[-1] != "0"


# ── Buttons ────────────────────────────────────────────────────────────────────

async def get_buttons(chat_id: int) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, label, url FROM buttons WHERE chat_id = $1 ORDER BY id",
            chat_id,
        )
        return [{"id": r["id"], "label": r["label"], "url": r["url"]} for r in rows]


async def add_button(chat_id: int, label: str, url: str) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO buttons (chat_id, label, url) VALUES ($1, $2, $3) RETURNING id",
            chat_id, label, url,
        )
        return row["id"]  # type: ignore[index]


async def delete_button(button_id: int, chat_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM buttons WHERE id = $1 AND chat_id = $2", button_id, chat_id
        )
        return result.split()[-1] != "0"


async def delete_all_buttons(chat_id: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM buttons WHERE chat_id = $1", chat_id
        )
        return int(result.split()[-1])


# ── Channels ───────────────────────────────────────────────────────────────────

async def add_channel(
    channel_id: int,
    username: str | None,
    title: str | None,
    added_by: int,
) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO channels (channel_id, username, title, added_by)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (channel_id) DO UPDATE
                    SET username = EXCLUDED.username,
                        title    = EXCLUDED.title
                """,
                channel_id, username, title, added_by,
            )
            return True
        except Exception as exc:
            logger.error("add_channel error: %s", exc)
            return False


async def delete_channel(channel_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM channels WHERE channel_id = $1", channel_id
        )
        return result.split()[-1] != "0"


async def list_channels() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, channel_id, username, title, added_at FROM channels ORDER BY added_at DESC"
        )
        return [dict(r) for r in rows]


async def channel_exists(channel_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM channels WHERE channel_id = $1", channel_id
        )
        return row is not None


# ── Known chats (broadcast targets) ───────────────────────────────────────────

async def register_chat(
    chat_id: int,
    chat_type: str,
    title: str | None = None,
    username: str | None = None,
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO known_chats (chat_id, chat_type, title, username, updated_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (chat_id) DO UPDATE
                SET chat_type  = EXCLUDED.chat_type,
                    title      = EXCLUDED.title,
                    username   = EXCLUDED.username,
                    updated_at = NOW()
            """,
            chat_id, chat_type, title, username,
        )


async def get_all_chats() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT chat_id, chat_type, title, username FROM known_chats ORDER BY registered_at DESC"
        )
        return [dict(r) for r in rows]


async def remove_chat(chat_id: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM known_chats WHERE chat_id = $1", chat_id)


# ── Stats ──────────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        total_chats      = await conn.fetchval("SELECT COUNT(*) FROM known_chats")
        groups           = await conn.fetchval("SELECT COUNT(*) FROM known_chats WHERE chat_type IN ('group','supergroup')")
        private          = await conn.fetchval("SELECT COUNT(*) FROM known_chats WHERE chat_type = 'private'")
        welcome_count    = await conn.fetchval("SELECT COUNT(*) FROM welcome_messages")
        button_count     = await conn.fetchval("SELECT COUNT(*) FROM buttons")
        channel_count    = await conn.fetchval("SELECT COUNT(*) FROM channels")
        chats_with_btn   = await conn.fetchval("SELECT COUNT(DISTINCT chat_id) FROM buttons")
    return {
        "total_chats":    total_chats,
        "groups":         groups,
        "private":        private,
        "welcome_count":  welcome_count,
        "button_count":   button_count,
        "chats_with_btn": chats_with_btn,
        "channel_count":  channel_count,
    }
