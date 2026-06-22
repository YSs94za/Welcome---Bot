import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.inline import start_keyboard

logger = logging.getLogger(__name__)
router = Router()

START_GIF = "https://i.postimg.cc/nhH6hs8t/c81f81a024caf4cb16ddfdc7585848c4.gif"

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
    logger.info(
        "User %s sent /start in chat %d",
        message.from_user.id if message.from_user else "?",
        message.chat.id,
    )
    await message.answer_animation(
        animation=START_GIF,
        caption=START_CAPTION,
        reply_markup=start_keyboard(),
    )
