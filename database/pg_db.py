import logging
import asyncpg
from config import PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=PGHOST,
            port=PGPORT,
            user=PGUSER,
            password=PGPASSWORD,
            database=PGDATABASE,
            min_size=1,
            max_size=5,
        )
        logger.info("PostgreSQL pool created (host=%s db=%s)", PGHOST, PGDATABASE)
    return _pool


async def init_postgres() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
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
    logger.info("PostgreSQL schema ready")


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Channels CRUD ─────────────────────────────────────────────────────────────

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
