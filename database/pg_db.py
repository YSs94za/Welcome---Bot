import logging
import asyncpg
from config import DATABASE_URL

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create PostgreSQL connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            logger.info("PostgreSQL pool created (min=1, max=10)")
        except Exception as exc:
            logger.critical("Failed to create PostgreSQL pool: %s", exc)
            raise
    return _pool


async def init_postgres() -> None:
    """Initialize PostgreSQL schema on startup.
    
    Creates tables:
    - welcome_messages: Store welcome text per chat
    - buttons: Inline buttons for welcome messages
    - channels: Registered channels (informational only)
    - known_chats: Broadcast target tracking
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            # Welcome messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS welcome_messages (
                    chat_id BIGINT PRIMARY KEY,
                    message TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            logger.info("Table 'welcome_messages' ready")

            # Buttons table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS buttons (
                    id      SERIAL PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    label   TEXT   NOT NULL,
                    url     TEXT   NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_buttons_chat ON buttons(chat_id)"
            )
            logger.info("Table 'buttons' ready")

            # Channels table (informational, no enforcement)
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
            logger.info("Table 'channels' ready")

            # Known chats table (for broadcast targeting)
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
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_known_chats_type ON known_chats(chat_type)"
            )
            logger.info("Table 'known_chats' ready")

            logger.info("PostgreSQL schema initialization complete")
        except Exception as exc:
            logger.critical("Failed to initialize PostgreSQL schema: %s", exc)
            raise


async def close_pool() -> None:
    """Close PostgreSQL connection pool on shutdown."""
    global _pool
    if _pool:
        try:
            await _pool.close()
            logger.info("PostgreSQL pool closed")
        except Exception as exc:
            logger.error("Error closing PostgreSQL pool: %s", exc)
        _pool = None


# ── Welcome messages ──────────────────────────────────────────────────────────

async def get_welcome_message(chat_id: int) -> str | None:
    """Get welcome message for a chat."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT message FROM welcome_messages WHERE chat_id = $1", chat_id
        )
        return row["message"] if row else None


async def set_welcome_message(chat_id: int, message: str) -> None:
    """Set or update welcome message for a chat."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO welcome_messages (chat_id, message, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (chat_id) DO UPDATE SET
                message = EXCLUDED.message,
                updated_at = NOW()
            """,
            chat_id, message,
        )


async def delete_welcome_message(chat_id: int) -> bool:
    """Delete welcome message for a chat."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM welcome_messages WHERE chat_id = $1", chat_id
        )
        return result.split()[-1] != "0"


# ── Buttons ────────────────────────────────────────────────────────────────────

async def get_buttons(chat_id: int) -> list[dict]:
    """Get all buttons for a chat."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, label, url FROM buttons WHERE chat_id = $1 ORDER BY id",
            chat_id,
        )
        return [dict(r) for r in rows]


async def add_button(chat_id: int, label: str, url: str) -> int:
    """Add a button to a chat's welcome message."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO buttons (chat_id, label, url) VALUES ($1, $2, $3) RETURNING id",
            chat_id, label, url,
        )
        return row["id"]  # type: ignore[index]


async def delete_button(button_id: int, chat_id: int) -> bool:
    """Delete a button by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM buttons WHERE id = $1 AND chat_id = $2", button_id, chat_id
        )
        return result.split()[-1] != "0"


async def delete_all_buttons(chat_id: int) -> int:
    """Delete all buttons for a chat."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM buttons WHERE chat_id = $1", chat_id
        )
        return int(result.split()[-1])


# ── Channels (informational only, NO subscription enforcement) ─────────────────

async def add_channel(
    channel_id: int,
    username: str | None,
    title: str | None,
    added_by: int,
) -> bool:
    """Register a channel. This is for information only.
    
    IMPORTANT: This does NOT enforce channel membership or subscriptions.
    Channels are stored for administrative tracking purposes only.
    """
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
    """Remove a registered channel."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM channels WHERE channel_id = $1", channel_id
        )
        return result.split()[-1] != "0"


async def list_channels() -> list[dict]:
    """List all registered channels."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, channel_id, username, title, added_at FROM channels ORDER BY added_at DESC"
        )
        return [dict(r) for r in rows]


async def channel_exists(channel_id: int) -> bool:
    """Check if a channel is registered."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM channels WHERE channel_id = $1", channel_id
        )
        return row is not None


# ── Known chats (broadcast targets) ────────────────────────────────────────────

async def register_chat(
    chat_id: int,
    chat_type: str,
    title: str | None = None,
    username: str | None = None,
) -> None:
    """Register a chat for broadcast targeting."""
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
    """Get all registered chats for broadcasting."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT chat_id, chat_type, title, username FROM known_chats ORDER BY registered_at DESC"
        )
        return [dict(r) for r in rows]


async def remove_chat(chat_id: int) -> None:
    """Remove a chat from broadcast targets."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM known_chats WHERE chat_id = $1", chat_id)


# ── Statistics ─────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    """Get bot statistics."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            total_chats      = await conn.fetchval("SELECT COUNT(*) FROM known_chats")
            groups           = await conn.fetchval(
                "SELECT COUNT(*) FROM known_chats WHERE chat_type IN ('group','supergroup')"
            )
            private          = await conn.fetchval(
                "SELECT COUNT(*) FROM known_chats WHERE chat_type = 'private'"
            )
            welcome_count    = await conn.fetchval("SELECT COUNT(*) FROM welcome_messages")
            button_count     = await conn.fetchval("SELECT COUNT(*) FROM buttons")
            channel_count    = await conn.fetchval("SELECT COUNT(*) FROM channels")
            chats_with_btn   = await conn.fetchval(
                "SELECT COUNT(DISTINCT chat_id) FROM buttons"
            )
        except Exception as exc:
            logger.error("Error fetching stats: %s", exc)
            return {
                "total_chats":    0,
                "groups":         0,
                "private":        0,
                "welcome_count":  0,
                "button_count":   0,
                "chats_with_btn": 0,
                "channel_count":  0,
            }

    return {
        "total_chats":    total_chats,
        "groups":         groups,
        "private":        private,
        "welcome_count":  welcome_count,
        "button_count":   button_count,
        "chats_with_btn": chats_with_btn,
        "channel_count":  channel_count,
    }
