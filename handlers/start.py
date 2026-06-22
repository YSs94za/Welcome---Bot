import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.inline import start_keyboard
from database.pg_db import register_chat

logger = logging.getLogger(__name__)
router = Router()

START_CAPTION = (
    "<b>👋 Welcome Bot</b>\n\n"
    "I automatically greet new members with a custom message and inline buttons.\n\n"
    "<b>📌 Features:</b>\n"
    "• Custom welcome messages per group\n"
    "• Unlimited inline URL buttons\n"
    "• Placeholder support: <code>{name}</code>, <code>{chat}</code>\n"
    "• Admin-only management\n"
    "• Multi-group support\n\n"
    "Press a button below to get started ↓"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command with safe media fallback."""
    try:
        logger.info(
            "User %s sent /start in chat %d",
            message.from_user.id if message.from_user else "?",
            message.chat.id,
        )
        await register_chat(
            chat_id=message.chat.id,
            chat_type=message.chat.type,
            title=message.chat.title or message.chat.full_name,
            username=message.chat.username,
        )
        
        # Send text message with keyboard (safe fallback)
        await message.answer(
            START_CAPTION,
            reply_markup=start_keyboard(),
        )
        logger.info("Start message sent to chat %d", message.chat.id)
        
    except Exception as exc:
        logger.error("Error in cmd_start for chat %d: %s", message.chat.id, exc)
        try:
            await message.answer(
                "❌ An error occurred. Please try again.\n"
                f"<code>{type(exc).__name__}</code>"
            )
        except Exception as nested_exc:
            logger.error("Failed to send error message: %s", nested_exc)
