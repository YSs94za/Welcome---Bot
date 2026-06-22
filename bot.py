import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.exceptions import TelegramConflictError

from config import BOT_TOKEN, MAX_CONCURRENT_TASKS, START_FROM_LATEST
from database.pg_db import init_postgres, close_pool
from handlers import start, admin, channels, welcome, callbacks, broadcast

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand(command="start",         description="Show main menu"),
    BotCommand(command="set_welcome",   description="Set welcome message for this group"),
    BotCommand(command="show_welcome",  description="Preview current welcome message"),
    BotCommand(command="del_welcome",   description="Delete welcome message & buttons"),
    BotCommand(command="add_button",    description="Add inline button (label | url)"),
    BotCommand(command="del_button",    description="Remove button by ID"),
    BotCommand(command="list_buttons",  description="List all configured buttons"),
    BotCommand(command="add_channel",   description="Register a channel"),
    BotCommand(command="del_channel",   description="Remove channel by ID"),
    BotCommand(command="list_channels", description="List all registered channels"),
    BotCommand(command="broadcast",     description="Broadcast message to all known chats"),
    BotCommand(command="stats",         description="Show bot statistics"),
    BotCommand(command="cancel",        description="Cancel current operation"),
]


async def on_startup(bot: Bot) -> None:
    """Initialize bot on startup.
    
    - Connect to PostgreSQL
    - Create tables if needed
    - Register bot commands
    - Log startup info
    """
    try:
        logger.info("Starting bot initialization...")
        await init_postgres()
        await bot.set_my_commands(BOT_COMMANDS)
        me = await bot.get_me()
        logger.warning(
            "✓ Bot @%s (id=%d) STARTED | max_tasks=%d start_from_latest=%s",
            me.username, me.id, MAX_CONCURRENT_TASKS, START_FROM_LATEST,
        )
    except Exception as exc:
        logger.critical("Failed to start bot: %s", exc)
        raise


async def on_shutdown(bot: Bot) -> None:
    """Clean up on bot shutdown."""
    try:
        await close_pool()
        logger.warning("✓ Bot shut down — PostgreSQL pool closed")
    except Exception as exc:
        logger.error("Error during shutdown: %s", exc)


async def main() -> None:
    """Main bot polling loop."""
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register routers
    dp.include_router(callbacks.router)
    dp.include_router(broadcast.router)
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(channels.router)
    dp.include_router(welcome.router)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "chat_member"],
            drop_pending_updates=START_FROM_LATEST,
        )
    except TelegramConflictError:
        logger.critical(
            "Polling conflict detected (409): another bot instance is already running. "
            "Stop the other instance before starting a new one."
        )
        raise
    except Exception as exc:
        logger.critical("Polling failed: %s", exc)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except TelegramConflictError:
        raise SystemExit(1)
    except Exception as exc:
        logger.critical("Fatal error: %s", exc)
        raise
