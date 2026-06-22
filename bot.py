import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from config import BOT_TOKEN, MAX_CONCURRENT_TASKS, START_FROM_LATEST
from database.pg_db import init_postgres, close_pool
from handlers import start, admin, channels, welcome, callbacks

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand(command="start",         description="Show main menu"),
    BotCommand(command="set_welcome",   description="Set welcome message for this group"),
    BotCommand(command="show_welcome",  description="Preview current welcome message"),
    BotCommand(command="del_welcome",   description="Delete welcome message & buttons"),
    BotCommand(command="add_button",    description="Add inline button  (label | url)"),
    BotCommand(command="del_button",    description="Remove button by ID"),
    BotCommand(command="list_buttons",  description="List all configured buttons"),
    BotCommand(command="add_channel",   description="Register a channel"),
    BotCommand(command="del_channel",   description="Remove channel by ID"),
    BotCommand(command="list_channels", description="List all registered channels"),
]


async def on_startup(bot: Bot) -> None:
    await init_postgres()
    await bot.set_my_commands(BOT_COMMANDS)
    me = await bot.get_me()
    logger.warning(
        "Bot @%s (id=%d) started | max_tasks=%d start_from_latest=%s",
        me.username, me.id, MAX_CONCURRENT_TASKS, START_FROM_LATEST,
    )


async def on_shutdown(bot: Bot) -> None:
    await close_pool()
    logger.warning("Bot shut down — PostgreSQL pool closed")


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(callbacks.router)
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(channels.router)
    dp.include_router(welcome.router)

    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "chat_member"],
        drop_pending_updates=START_FROM_LATEST,
    )


if __name__ == "__main__":
    asyncio.run(main())
