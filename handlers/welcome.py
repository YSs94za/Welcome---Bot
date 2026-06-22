import logging
from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION
from database.pg_db import get_welcome_message, get_buttons, register_chat
from keyboards.inline import build_welcome_keyboard

logger = logging.getLogger(__name__)
router = Router()


def _render(template: str, full_name: str, chat_title: str) -> str:
    """Render welcome message with user and chat placeholders."""
    return template.replace("{name}", full_name).replace("{chat}", chat_title)


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_new_member(event: ChatMemberUpdated, bot: Bot) -> None:
    """Send welcome message when a new user joins the chat.
    
    This handler:
    1. Registers the chat in the database
    2. Retrieves the stored welcome message (if any)
    3. Fetches associated buttons
    4. Renders placeholders ({name}, {chat})
    5. Sends the message with error handling
    """
    user = event.new_chat_member.user
    
    # Ignore bot joins
    if user.is_bot:
        logger.debug("Bot user %s joined, ignoring", user.id)
        return

    chat_id    = event.chat.id
    chat_title = event.chat.title or "the group"

    try:
        # Register chat for broadcast targeting
        await register_chat(
            chat_id=chat_id,
            chat_type=event.chat.type,
            title=event.chat.title,
            username=event.chat.username,
        )
    except Exception as exc:
        logger.error("Failed to register chat %d: %s", chat_id, exc)

    try:
        # Get welcome message from database
        welcome_text = await get_welcome_message(chat_id)
        if not welcome_text:
            logger.debug("No welcome message configured for chat %d", chat_id)
            return

        # Get buttons
        buttons = await get_buttons(chat_id)
        kb = build_welcome_keyboard(buttons)
        
        # Render message with user name and chat title
        text = _render(welcome_text, user.full_name, chat_title)

        # Send welcome message
        await bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
        logger.info("Welcome sent to user %d in chat %d", user.id, chat_id)
        
    except Exception as exc:
        logger.error("Failed to send welcome in chat %d: %s", chat_id, exc)
