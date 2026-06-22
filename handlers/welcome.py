import logging
from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION
from database.sqlite_db import get_welcome_message, get_buttons
from keyboards.inline import build_welcome_keyboard

logger = logging.getLogger(__name__)
router = Router()


def _render(template: str, full_name: str, chat_title: str) -> str:
    return template.replace("{name}", full_name).replace("{chat}", chat_title)


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_new_member(event: ChatMemberUpdated, bot: Bot) -> None:
    user = event.new_chat_member.user
    if user.is_bot:
        return

    chat_id    = event.chat.id
    chat_title = event.chat.title or "the group"

    welcome_text = await get_welcome_message(chat_id)
    if not welcome_text:
        return

    buttons = await get_buttons(chat_id)
    kb      = build_welcome_keyboard(buttons)
    text    = _render(welcome_text, user.full_name, chat_title)

    try:
        await bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
        logger.info("Welcomed user %d in chat %d", user.id, chat_id)
    except Exception as exc:
        logger.error("Failed to send welcome in chat %d: %s", chat_id, exc)
